from fastapi import FastAPI, Depends, HTTPException, status, Request, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
import json
import os
import time
import logging
from dotenv import load_dotenv

logger = logging.getLogger(__name__)

# Load .env from current directory
load_dotenv(dotenv_path=os.path.join(os.path.dirname(__file__), '.env'))

app = FastAPI(title="NarrAI MVP")

REQUIRED_API_KEYS = {
    "GROQ_API_KEY": "Story Generator and Editor",
    "GROQ_API_KEY_BIBLE": "QA Refiner and Memory Extractor",
    "GROQ_API_KEY_COPILOT": "Master Controller / Copilot",
}

def safe_generation_error(error, operation="sinh truyện"):
    message = str(error)
    if "413" in message or "rate_limit_exceeded" in message or "Request too large" in message:
        return f"Yêu cầu {operation} vượt giới hạn token hiện tại. Hãy chọn nội dung ngắn hơn hoặc thử lại sau."
    return f"Không thể {operation} lúc này. Vui lòng thử lại sau."

# CORS configuration — restricted origins
FRONTEND_URL = os.environ.get("FRONTEND_URL", "http://localhost:8000")
ALLOWED_ORIGINS = [
    FRONTEND_URL,
    "http://localhost:3000",
    "http://localhost:8000",
]
# Add production URL if different
if FRONTEND_URL not in ALLOWED_ORIGINS:
    ALLOWED_ORIGINS.append(FRONTEND_URL)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_origin_regex=r"https://.*\.vercel\.app|https://.*\.onrender\.com|http://localhost:.*",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Lazy-load agents
qa_refiner = None
story_generator = None

def get_qa_refiner():
    global qa_refiner
    if qa_refiner is None:
        from agents.qa_refiner import QARefiner
        qa_refiner = QARefiner()
    return qa_refiner

def get_story_generator():
    global story_generator
    if story_generator is None:
        from agents.story_generator import StoryGenerator
        story_generator = StoryGenerator()
    return story_generator

import re
from datetime import datetime
from fastapi.responses import StreamingResponse, JSONResponse, RedirectResponse, FileResponse
from db.models import Story, User, AuthAccount, TokenBlacklist, Comic, ComicPanel, ComicJob, engine
from sqlalchemy.orm import sessionmaker, Session
from auth import (
    verify_password, get_password_hash,
    create_access_token, create_refresh_token, decode_access_token,
    is_token_blacklisted, blacklist_token, cleanup_expired_blacklist,
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Cache for users to prevent DB hits on every request
USER_CACHE = {}

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/login", auto_error=False)

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    if not token:
        return None
    
    # Decode token
    payload = decode_access_token(token)
    if not payload:
        return None
    
    # Check token type
    if payload.get("type") != "access":
        return None
    
    # Check blacklist
    jti = payload.get("jti")
    if jti and is_token_blacklisted(jti, db):
        return None
    
    # Check cache
    cache_key = f"{payload.get('sub')}:{jti}"
    if cache_key in USER_CACHE:
        return USER_CACHE[cache_key]
    
    username = payload.get("sub")
    user = db.query(User).filter(User.username == username).first()
    
    if user:
        USER_CACHE[cache_key] = user
        
    return user

# ============ PYDANTIC MODELS ============
class ChatInterviewRequest(BaseModel):
    chat_history: list | None = None
    initial_prompt: str | None = None
    answers: list | None = None
    questions: list | None = None

class GenerateQuestionsRequest(BaseModel):
    prompt: str

class ChatRequest(BaseModel):
    story_text: str
    user_message: str
    story_id: int | None = None

class GenerateStoryRequest(BaseModel):
    refined_prompt: str
    story_length: str = "medium"

class EditTextRequest(BaseModel):
    original_text: str
    instruction: str

class UserCreate(BaseModel):
    username: str
    password: str
    email: str | None = None
    name: str | None = None

class RefreshTokenRequest(BaseModel):
    refresh_token: str

# ============ AUTH ENDPOINTS ============

@app.post("/api/register")
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    # Use email if provided, otherwise use username as email
    email = user.email or user.username
    
    # Check duplicate by username
    existing = db.query(User).filter(User.username == user.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Tên đăng nhập đã tồn tại")
    
    # Check duplicate by email (if different from username)
    if email != user.username:
        existing_email = db.query(User).filter(User.email == email).first()
        if existing_email:
            raise HTTPException(status_code=400, detail="Email đã được sử dụng")
    
    hashed_password = get_password_hash(user.password)
    new_user = User(
        username=user.username,
        email=email,
        name=user.name or user.username,
        password_hash=hashed_password,
    )
    db.add(new_user)
    db.commit()
    return {"status": "success", "message": "Đăng ký thành công"}

@app.post("/api/login")
def login_user(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    # Find user by username OR email
    user = db.query(User).filter(
        (User.username == form_data.username) | (User.email == form_data.username)
    ).first()
    
    if not user or not user.password_hash or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=400, detail="Sai tên đăng nhập hoặc mật khẩu")
    
    access_token = create_access_token(data={"sub": user.username})
    refresh_token = create_refresh_token(data={"sub": user.username})
    
    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
        "username": user.username,
    }

@app.post("/api/refresh")
def refresh_access_token(req: RefreshTokenRequest, db: Session = Depends(get_db)):
    payload = decode_access_token(req.refresh_token)
    if not payload or payload.get("type") != "refresh":
        raise HTTPException(status_code=401, detail="Refresh token không hợp lệ hoặc đã hết hạn")
    
    # Check blacklist
    jti = payload.get("jti")
    if jti and is_token_blacklisted(jti, db):
        raise HTTPException(status_code=401, detail="Token đã bị vô hiệu hóa")
    
    username = payload.get("sub")
    user = db.query(User).filter(User.username == username).first()
    if not user:
        raise HTTPException(status_code=401, detail="Người dùng không tồn tại")
    
    # Blacklist the old refresh token (single use)
    if jti:
        exp = datetime.utcfromtimestamp(payload.get("exp", 0))
        blacklist_token(jti, exp, db)
    
    new_access = create_access_token(data={"sub": user.username})
    new_refresh = create_refresh_token(data={"sub": user.username})
    
    return {
        "access_token": new_access,
        "refresh_token": new_refresh,
        "token_type": "bearer",
    }

@app.post("/api/logout")
def logout_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    if not token:
        return {"status": "success", "message": "Đã đăng xuất"}
    
    payload = decode_access_token(token)
    if payload:
        jti = payload.get("jti")
        if jti:
            exp = datetime.utcfromtimestamp(payload.get("exp", 0))
            try:
                blacklist_token(jti, exp, db)
            except Exception:
                pass  # Already blacklisted or DB error — still log out client side
    
    # Periodically clean up expired entries
    try:
        cleanup_expired_blacklist(db)
    except Exception:
        pass
    
    return {"status": "success", "message": "Đã đăng xuất"}

@app.get("/api/me")
def read_users_me(current_user: User = Depends(get_current_user)):
    if not current_user:
        raise HTTPException(status_code=401, detail="Chưa đăng nhập")
    return {
        "id": current_user.id,
        "username": current_user.username,
        "email": current_user.email,
        "name": current_user.name,
        "avatar_url": current_user.avatar_url,
    }

# ============ OAUTH SOCIAL LOGIN ENDPOINTS ============

@app.get("/api/auth/providers")
def get_auth_providers():
    """Return list of configured OAuth providers for frontend."""
    from oauth import get_available_providers
    return {"providers": get_available_providers()}

@app.get("/api/auth/{provider}")
async def oauth_login(provider: str, request: Request):
    """Redirect user to OAuth provider's authorization page."""
    from oauth import oauth as oauth_client, is_provider_configured
    
    if not is_provider_configured(provider):
        return RedirectResponse(f"{FRONTEND_URL}?auth_error=provider_not_configured&provider={provider}")
    
    redirect_uri = f"{FRONTEND_URL}/api/auth/{provider}/callback"
    client = oauth_client.create_client(provider)
    return await client.authorize_redirect(request, redirect_uri)

@app.get("/api/auth/{provider}/callback")
async def oauth_callback(provider: str, request: Request, db: Session = Depends(get_db)):
    """Handle OAuth callback: find or create user, return JWT via redirect."""
    from oauth import oauth as oauth_client, is_provider_configured, get_oauth_user_info
    
    if not is_provider_configured(provider):
        raise HTTPException(status_code=400, detail=f"Provider '{provider}' chưa được cấu hình")
    
    try:
        client = oauth_client.create_client(provider)
        token = await client.authorize_access_token(request)
    except Exception as e:
        return RedirectResponse(f"{FRONTEND_URL}?auth_error=oauth_failed")
    
    user_info = await get_oauth_user_info(provider, token)
    if not user_info or not user_info.get("provider_account_id"):
        return RedirectResponse(f"{FRONTEND_URL}?auth_error=no_user_info")
    
    provider_id = user_info["provider_account_id"]
    
    # 1. Check if this social account is already linked
    auth_account = db.query(AuthAccount).filter(
        AuthAccount.provider == provider,
        AuthAccount.provider_account_id == provider_id,
    ).first()
    
    if auth_account:
        user = db.query(User).filter(User.id == auth_account.user_id).first()
    else:
        user = None
        
        # 2. Check if email matches an existing user
        email = user_info.get("email")
        if email:
            user = db.query(User).filter(User.email == email).first()
        
        # 3. Create new user if no match found
        if not user:
            username = email or f"{provider}_{provider_id}"
            # Ensure unique username
            base_username = username
            counter = 1
            while db.query(User).filter(User.username == username).first():
                username = f"{base_username}_{counter}"
                counter += 1
            
            user = User(
                username=username,
                email=email,
                name=user_info.get("name"),
                avatar_url=user_info.get("avatar_url"),
                password_hash=None,  # Social-only user, no password
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        else:
            # Update avatar/name from social profile if not set
            if user_info.get("avatar_url") and not user.avatar_url:
                user.avatar_url = user_info["avatar_url"]
            if user_info.get("name") and not user.name:
                user.name = user_info["name"]
            db.commit()
        
        # 4. Link the social account
        new_auth = AuthAccount(
            user_id=user.id,
            provider=provider,
            provider_account_id=provider_id,
        )
        db.add(new_auth)
        db.commit()
    
    # 5. Generate JWT and redirect with token
    access_token = create_access_token(data={"sub": user.username})
    refresh_token = create_refresh_token(data={"sub": user.username})
    
    return RedirectResponse(
        f"{FRONTEND_URL}?access_token={access_token}&refresh_token={refresh_token}&username={user.username}"
    )

# ============ CORE ENDPOINTS ============

@app.post("/api/generate-questions")
def generate_questions(request: GenerateQuestionsRequest):
    try:
        qa = get_qa_refiner()
        response = qa.chat_interview([{"role": "user", "content": request.prompt}])
        cleaned = response.replace("[READY]", "").strip()
        lines = [line.strip() for line in cleaned.split("\n") if line.strip()]
        questions = [l for l in lines if "?" in l or l.startswith(("1", "2", "3", "4", "-", "*"))]
        if not questions:
            questions = [cleaned]
        return {"status": "success", "questions": questions, "analysis": "Ý tưởng đã được phân tích."}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/api/chat-interview")
def chat_interview(request: ChatInterviewRequest):
    try:
        qa = get_qa_refiner()
        history = request.chat_history or []
        response = qa.chat_interview(history)
        is_ready = "[READY]" in response
        cleaned_response = response.replace("[READY]", "").strip()
        return {"status": "success", "message": cleaned_response, "is_ready": is_ready}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/api/refine-prompt")
def refine_prompt(request: ChatInterviewRequest):
    try:
        qa = get_qa_refiner()
        history = request.chat_history
        if not history and request.initial_prompt:
            history = [{"role": "user", "content": request.initial_prompt}]
            if request.questions and request.answers:
                for q, a in zip(request.questions, request.answers):
                    history.append({"role": "assistant", "content": q})
                    history.append({"role": "user", "content": a})
        refined = qa.refine_prompt(history or [])
        return {"status": "success", "refined_prompt": refined}
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"status": "error", "message": str(e)}

@app.post("/api/edit-text")
async def edit_text(request: EditTextRequest):
    try:
        from agents.editor_agent import EditorAgent
        editor = EditorAgent()
        revised = editor.edit_text(request.original_text, request.instruction)
        return {"status": "success", "revised_text": revised}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/api/generate-story")
def generate_story(request: GenerateStoryRequest, current_user: User = Depends(get_current_user)):
    try:
        gen = get_story_generator()
        
        async def stream_and_save():
            full_story = ""
            saved_story_id = None
            try:
                for chunk in gen.generate_story_stream(request.refined_prompt, request.story_length):
                    full_story += chunk
                    yield chunk
            except Exception as e:
                yield f"\n\n[GENERATION_ERROR:{safe_generation_error(e)}]"
                return
                
            word_count = len(full_story.split())
            if word_count > 10 and current_user:
                db = SessionLocal()
                try:
                    new_story = Story(
                        user_id=current_user.id,
                        refined_prompt=request.refined_prompt,
                        story_content=full_story,
                        word_count=word_count
                    )
                    db.add(new_story)
                    db.commit()
                    db.refresh(new_story)
                    saved_story_id = new_story.id
                except Exception as e:
                    print(f"DB Error: {e}")
                finally:
                    db.close()

            if saved_story_id:
                yield f"\n\n[STORY_ID:{saved_story_id}]"

        return StreamingResponse(stream_and_save(), media_type="text/plain")
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/api/trending-topics")
async def get_trending_topics():
    try:
        file_path = os.path.join(os.path.dirname(__file__), "data", "trending_themes.json")
        with open(file_path, "r", encoding="utf-8") as f:
            topics = json.load(f)
        return {"status": "success", "topics": topics}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/api/stories")
async def get_stories(current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not current_user:
        return {"status": "success", "stories": []}
        
    try:
        stories = db.query(Story).filter(Story.user_id == current_user.id).order_by(Story.created_at.desc()).limit(20).all()
        result = []
        for s in stories:
            first_line = s.story_content.strip().split('\n')[0] if s.story_content else "Truyện chưa đặt tên"
            title = first_line.replace("**", "").replace("#", "").strip()
            if len(title) > 60:
                title = title[:60] + "..."
            result.append({
                "id": s.id,
                "title": title,
                "word_count": s.word_count,
                "created_at": s.created_at.strftime("%H:%M %d/%m/%Y") if s.created_at else "",
                "snippet": s.story_content[:120].strip() + "..." if s.story_content else ""
            })
        return {"status": "success", "stories": result}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/api/stories/{story_id}")
async def get_story_detail(story_id: int, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not current_user:
        return {"status": "error", "message": "Yêu cầu đăng nhập"}
        
    try:
        story = db.query(Story).filter(Story.id == story_id, Story.user_id == current_user.id).first()
        if not story:
            return {"status": "error", "message": "Không tìm thấy truyện hoặc không có quyền xem"}
        return {
            "status": "success",
            "story": {
                "id": story.id,
                "session_id": story.session_id,
                "refined_prompt": story.refined_prompt,
                "story_content": story.story_content,
                "word_count": story.word_count,
                "bible_data": story.bible_data,
                "memory_data": story.memory_data,
                "created_at": story.created_at.strftime("%H:%M %d/%m/%Y") if story.created_at else ""
            }
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/api/health")
async def health():
    missing = [name for name in REQUIRED_API_KEYS if not os.environ.get(name)]
    return {
        "status": "ok" if not missing else "degraded",
        "message": "Backend is running!",
        "database": engine.dialect.name,
        "missing_keys": missing,
    }

# ================= COMIC & IMAGE POST-PROCESSING ENDPOINTS =================
from typing import Optional, List, Dict, Any
from fastapi.responses import FileResponse
from services.image_gen import generate_comic_panel_image, get_comfyui_status
from services.post_processor import ImagePostProcessor
from services.stability_service import StabilityImageService
from db.models import Comic, ComicPanel

post_processor = ImagePostProcessor()
stability_service = post_processor.stability

@app.get("/api/comfy/status")
def get_comfy_status():
    """
    Returns live connection status of local ComfyUI server and active checkpoint.
    """
    return get_comfyui_status()

@app.get("/api/stability/config")
def get_stability_config():
    """
    Public config endpoint for frontend to display enhancement options.
    Never exposes API keys or secrets.
    """
    return {
        "status": "success",
        "enabled": stability_service.is_available(),
        "default_mode": os.environ.get("STABILITY_DEFAULT_MODE", "upscale").strip().lower(),
        "provider": "stability-ai",
        "modes": [
            {"id": "none", "label": "Bản gốc (ComfyUI)"},
            {"id": "upscale", "label": "Tăng độ nét (Fast Upscale 4x)"},
            {"id": "enhance", "label": "Tối ưu chi tiết & ánh sáng (SD3 Enhance)"}
        ]
    }

@app.get("/api/images/{stage}/{filename}")
async def get_stage_image(stage: str, filename: str):
    """
    Securely serves multi-stage pipeline images:
    /api/images/original/...
    /api/images/processed/...
    /api/images/final/...
    Prevents path traversal attacks.
    """
    allowed_stages = {"original", "processed", "final"}
    if stage not in allowed_stages:
        raise HTTPException(status_code=400, detail="Invalid stage")

    # Guard against directory traversal
    if ".." in filename or "/" in filename or "\\" in filename:
        raise HTTPException(status_code=400, detail="Invalid filename")

    file_path = os.path.join(post_processor.base_dir, stage, filename)
    if not os.path.isfile(file_path):
        raise HTTPException(status_code=404, detail="Image not found")

    return FileResponse(file_path, media_type="image/png")

# ================= COMIC BACKGROUND JOBS & STORY PIPELINE =================
import uuid

class CreateComicJobRequest(BaseModel):
    story_id: Optional[int] = None
    story_text: Optional[str] = ""
    genre: Optional[str] = ""
    style: Optional[str] = ""
    enhancement_mode: Optional[str] = "none"

def run_comic_generation_job(job_id: str, story_id: Optional[int], story_text: str, genre: str, style: str, user_id: Optional[int]):
    """
    Background Task: Executes 8-stage Story-to-Comic generation pipeline.
    Updates ComicJob in real-time so frontend polling reflects live progress.
    """
    db = SessionLocal()
    try:
        job = db.query(ComicJob).filter(ComicJob.id == job_id).first()
        if not job:
            return
        
        job.status = "processing"
        job.progress_percent = 5
        job.current_step = "Đang phân tích kịch bản & thiết kế nhân vật..."
        db.commit()

        # Step 1: Script & Bibles extraction (Character Bible + Location Bible)
        from agents.pro_comic_agent import ProComicAgent
        agent = ProComicAgent()
        script_data = agent.generate(story_text=story_text, genre=genre, style=style)

        char_bible = script_data.get("character_bible", [])
        loc_bible = script_data.get("location_bible", [])
        story_setting = script_data.get("story_setting", "")
        panels_plan = script_data.get("panels", [])

        # Create or update Comic record
        comic = None
        if job.comic_id:
            comic = db.query(Comic).filter(Comic.id == job.comic_id).first()
        if not comic:
            comic = Comic(
                user_id=user_id,
                story_id=story_id,
                title="Truyện tranh Chuyển thể",
                character_bible=json.dumps(char_bible, ensure_ascii=False),
                location_bible=json.dumps(loc_bible, ensure_ascii=False),
                story_setting=story_setting,
                status="processing"
            )
            db.add(comic)
            db.commit()
            db.refresh(comic)
            job.comic_id = comic.id
        else:
            comic.character_bible = json.dumps(char_bible, ensure_ascii=False)
            comic.location_bible = json.dumps(loc_bible, ensure_ascii=False)
            comic.story_setting = story_setting
            comic.status = "processing"

        job.total_panels = len(panels_plan)
        job.current_step = f"Đã xây dựng kịch bản {len(panels_plan)} khung tranh. Bắt đầu vẽ tranh..."
        job.progress_percent = 20
        db.commit()

        # Step 2: Initialize panel records in DB (so frontend immediately gets the script, characters, and dialogues)
        panel_records = []
        for idx, p_data in enumerate(panels_plan):
            p_idx = p_data.get("panel_index", idx + 1)
            raw_s = str(p_data.get("scene_id", "1")).upper().replace("S", "").strip()
            scene_val = int(raw_s) if raw_s.isdigit() else 1
            p_rec = ComicPanel(
                comic_id=comic.id,
                panel_index=p_idx,
                scene_id=scene_val,
                location_name=p_data.get("location_name", ""),
                character_names=p_data.get("character_names", ""),
                action_description=p_data.get("action", ""),
                emotion=p_data.get("emotion", ""),
                camera_angle=p_data.get("camera_angle", ""),
                image_prompt=p_data.get("image_prompt", ""),
                dialogue_text=p_data.get("dialogue", ""),
                speaker_name=p_data.get("speaker", ""),
                bubble_type=p_data.get("bubble_type", "speech"),
                narration_text=p_data.get("narration", ""),
                layout_type=p_data.get("layout_type", "square"),
                generation_status="pending"
            )
            db.add(p_rec)
            panel_records.append(p_rec)
        db.commit()

        # Step 3: Sequential Image Generation via Primary Provider (Stability AI)
        from services.image_provider import ImageProviderFactory
        stability_provider = ImageProviderFactory.get_primary_provider()
        backend_dir = os.path.dirname(os.path.abspath(__file__))
        final_dir = os.path.join(backend_dir, "outputs", "final")
        os.makedirs(final_dir, exist_ok=True)

        credit_warning_logged = False

        for i, panel in enumerate(panel_records):
            job.current_step = f"Đang vẽ tranh khung {i + 1}/{len(panel_records)}..."
            job.progress_percent = int(20 + ((i) / len(panel_records)) * 75)
            panel.generation_status = "generating"
            db.commit()

            seed_val = (comic.id * 100) + panel.panel_index
            result = stability_provider.generate_image(
                prompt=panel.image_prompt,
                aspect_ratio=panel.layout_type,
                seed=seed_val
            )

            if result.get("success") and result.get("image_bytes"):
                fn = f"panel_{comic.id}_{panel.panel_index}_{uuid.uuid4().hex[:8]}.png"
                fp = os.path.join(final_dir, fn)
                with open(fp, "wb") as f:
                    f.write(result["image_bytes"])
                
                panel_url = f"/api/images/final/{fn}"
                panel.original_image_url = panel_url
                panel.processed_image_url = panel_url
                panel.final_image_url = panel_url
                panel.image_url = panel_url
                panel.enhancement_provider = "stability"
                panel.enhancement_mode = "text-to-image"
                panel.enhancement_status = "completed"
                panel.generation_status = "completed"
                panel.error_message = None
                job.completed_panels += 1
            else:
                err_code = result.get("error_code")
                err_msg = result.get("error_message") or "Không thể tạo ảnh cho khung tranh này"
                panel.generation_status = "failed"
                panel.error_message = f"[{err_code}] {err_msg}"
                if err_code == "INSUFFICIENT_CREDITS" and not credit_warning_logged:
                    job.error_message = (
                        "Tài khoản Stability AI của bạn hiện chưa có đủ credits (cần nạp thêm tại platform.stability.ai). "
                        "Hệ thống đã lưu lại kịch bản, lời thoại và bố cục khung tranh hoàn chỉnh."
                    )
                    credit_warning_logged = True

            db.commit()

        # Step 4: Finalize Job
        comic.status = "ready"
        job.progress_percent = 100
        if job.completed_panels == job.total_panels:
            job.status = "completed"
            job.current_step = "Hoàn tất chuyển thể truyện tranh!"
        elif job.completed_panels > 0:
            job.status = "partial"
            job.current_step = f"Đã hoàn thành {job.completed_panels}/{job.total_panels} khung tranh."
        else:
            job.status = "failed"
            job.current_step = "Chưa thể tạo ảnh vì tài khoản Stability AI chưa có credits."

        db.commit()

    except Exception as e:
        logger.error(f"[ComicJob] Fatal job failure: {repr(e)}")
        try:
            job = db.query(ComicJob).filter(ComicJob.id == job_id).first()
            if job:
                job.status = "failed"
                job.error_message = str(e)
                job.current_step = f"Lỗi hệ thống: {repr(e)}"
                db.commit()
        except Exception:
            pass
    finally:
        db.close()


@app.post("/api/comic/jobs/create")
def create_comic_job(
    request: CreateComicJobRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    user_id = current_user.id if current_user else None
    if not user_id:
        first_user = db.query(User).first()
        if first_user:
            user_id = first_user.id

    effective_text = (request.story_text or "").strip()
    if not effective_text or len(effective_text) < 5:
        if request.story_id:
            s_rec = db.query(Story).filter(Story.id == request.story_id).first()
            if s_rec and s_rec.story_content:
                effective_text = s_rec.story_content
        if not effective_text:
            effective_text = "Một câu chuyện hành động kịch tính và hào hùng, nhân vật chính bước lên đỉnh cao võ học."

    job_id = f"job_{uuid.uuid4().hex[:16]}"
    job = ComicJob(
        id=job_id,
        user_id=user_id,
        story_id=request.story_id,
        status="pending",
        progress_percent=0,
        current_step="Đang khởi tạo tiến trình tạo truyện tranh..."
    )
    db.add(job)
    db.commit()

    background_tasks.add_task(
        run_comic_generation_job,
        job_id,
        request.story_id,
        effective_text,
        request.genre or "",
        request.style or "",
        user_id
    )

    return {"status": "success", "job_id": job_id}


@app.get("/api/comic/jobs/{job_id}")
def get_comic_job_status(job_id: str, db: Session = Depends(get_db)):
    job = db.query(ComicJob).filter(ComicJob.id == job_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Không tìm thấy tiến trình này.")

    comic = db.query(Comic).filter(Comic.id == job.comic_id).first() if job.comic_id else None

    panels_data = []
    char_bible = []
    loc_bible = []
    story_setting = ""

    if comic:
        if comic.character_bible:
            try:
                char_bible = json.loads(comic.character_bible)
            except Exception:
                char_bible = []
        if comic.location_bible:
            try:
                loc_bible = json.loads(comic.location_bible)
            except Exception:
                loc_bible = []
        story_setting = comic.story_setting or ""

        for p in comic.panels:
            panels_data.append({
                "id": p.id,
                "panel_index": p.panel_index,
                "scene_id": p.scene_id,
                "location_name": p.location_name,
                "character_names": p.character_names,
                "action_description": p.action_description,
                "emotion": p.emotion,
                "camera_angle": p.camera_angle,
                "image_prompt": p.image_prompt,
                "dialogue_text": p.dialogue_text,
                "dialogue": p.dialogue_text,
                "speaker_name": p.speaker_name,
                "speaker": p.speaker_name,
                "bubble_type": p.bubble_type or ("speech" if p.dialogue_text else "none"),
                "narration": p.narration_text or "",
                "narration_text": p.narration_text or "",
                "layout_type": p.layout_type or "square",
                "image_url": p.final_image_url or p.image_url,
                "original_image_url": p.original_image_url,
                "processed_image_url": p.processed_image_url,
                "final_image_url": p.final_image_url,
                "enhancement_provider": p.enhancement_provider,
                "enhancement_mode": p.enhancement_mode,
                "enhancement_status": p.enhancement_status,
                "generation_status": p.generation_status or ("completed" if (p.final_image_url or p.image_url) else "pending"),
                "error_message": p.error_message
            })

    return {
        "status": "success",
        "job": {
            "id": job.id,
            "status": job.status,
            "current_step": job.current_step,
            "progress_percent": job.progress_percent,
            "total_panels": job.total_panels,
            "completed_panels": job.completed_panels,
            "error_message": job.error_message,
            "comic_id": job.comic_id
        },
        "character_bible": char_bible,
        "location_bible": loc_bible,
        "story_setting": story_setting,
        "panels": panels_data
    }


class RetryPanelRequest(BaseModel):
    custom_prompt: Optional[str] = None

@app.post("/api/comic/panels/{panel_id}/retry")
def retry_comic_panel(panel_id: int, request: RetryPanelRequest = RetryPanelRequest(), db: Session = Depends(get_db)):
    panel = db.query(ComicPanel).filter(ComicPanel.id == panel_id).first()
    if not panel:
        raise HTTPException(status_code=404, detail="Không tìm thấy khung tranh.")

    from services.image_provider import ImageProviderFactory
    stability_provider = ImageProviderFactory.get_primary_provider()

    effective_prompt = (request.custom_prompt or panel.image_prompt or "masterpiece full color anime webtoon illustration").strip()
    panel.generation_status = "generating"
    db.commit()

    import random
    new_seed = random.randint(1000, 99999999)
    result = stability_provider.generate_image(
        prompt=effective_prompt,
        aspect_ratio=panel.layout_type or "square",
        seed=new_seed
    )

    if result.get("success") and result.get("image_bytes"):
        backend_dir = os.path.dirname(os.path.abspath(__file__))
        final_dir = os.path.join(backend_dir, "outputs", "final")
        os.makedirs(final_dir, exist_ok=True)
        fn = f"panel_retry_{panel.comic_id}_{panel.panel_index}_{uuid.uuid4().hex[:8]}.png"
        fp = os.path.join(final_dir, fn)
        with open(fp, "wb") as f:
            f.write(result["image_bytes"])

        panel_url = f"/api/images/final/{fn}"
        panel.image_url = panel_url
        panel.final_image_url = panel_url
        panel.processed_image_url = panel_url
        panel.enhancement_provider = "stability"
        panel.generation_status = "completed"
        panel.error_message = None
        db.commit()
        db.refresh(panel)
        return {
            "status": "success",
            "panel": {
                "id": panel.id,
                "panel_index": panel.panel_index,
                "image_url": panel.image_url,
                "final_image_url": panel.final_image_url,
                "generation_status": panel.generation_status
            }
        }
    else:
        err_code = result.get("error_code")
        err_msg = result.get("error_message") or "Không thể tạo lại ảnh cho khung này"
        panel.generation_status = "failed"
        panel.error_message = f"[{err_code}] {err_msg}"
        db.commit()
        return {
            "status": "error",
            "error_code": err_code,
            "message": err_msg
        }


@app.post("/api/comic/panels/{panel_id}/enhance-comfyui")
def enhance_panel_with_comfyui(panel_id: int, db: Session = Depends(get_db)):
    panel = db.query(ComicPanel).filter(ComicPanel.id == panel_id).first()
    if not panel:
        raise HTTPException(status_code=404, detail="Không tìm thấy khung tranh.")

    from services.image_provider import ImageProviderFactory
    comfy_provider = ImageProviderFactory.get_local_enhancer()
    if not comfy_provider.is_available():
        return {
            "status": "error",
            "message": "ComfyUI hiện đang tắt trên máy tính của bạn. Hãy khởi động ComfyUI (cổng 8188) để sử dụng tính năng này."
        }

    res = comfy_provider.generate_image(prompt=panel.image_prompt or "comic manga scene")
    if res.get("success") and res.get("image_bytes"):
        backend_dir = os.path.dirname(os.path.abspath(__file__))
        proc_dir = os.path.join(backend_dir, "outputs", "processed")
        os.makedirs(proc_dir, exist_ok=True)
        fn = f"panel_comfy_{panel.comic_id}_{panel.panel_index}_{uuid.uuid4().hex[:8]}.png"
        fp = os.path.join(proc_dir, fn)
        with open(fp, "wb") as f:
            f.write(res["image_bytes"])

        panel_url = f"/api/images/processed/{fn}"
        panel.processed_image_url = panel_url
        panel.final_image_url = panel_url
        panel.image_url = panel_url
        panel.enhancement_provider = "comfyui"
        db.commit()
        db.refresh(panel)
        return {
            "status": "success",
            "panel": {
                "id": panel.id,
                "panel_index": panel.panel_index,
                "image_url": panel.image_url,
                "final_image_url": panel.final_image_url
            }
        }
    else:
        return {
            "status": "error",
            "message": res.get("error_message") or "Không thể xử lý qua ComfyUI"
        }

class ComicRequest(BaseModel):
    story_id: Optional[int] = None
    story_text: Optional[str] = ""
    enhancement_mode: Optional[str] = "none"
    strength: Optional[float] = 0.35

@app.post("/api/comic/generate")
def create_comic(request: ComicRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    user_id = current_user.id if current_user else None
    if not user_id:
        first_user = db.query(User).first()
        if first_user:
            user_id = first_user.id

    effective_text = (request.story_text or "").strip()
    if not effective_text or len(effective_text) < 5:
        if request.story_id:
            s_rec = db.query(Story).filter(Story.id == request.story_id).first()
            if s_rec and s_rec.story_content:
                effective_text = s_rec.story_content
        if not effective_text:
            effective_text = "Một câu chuyện hành động kịch tính và hào hùng, nhân vật chính bước lên con đường chinh phục đỉnh cao võ học giữa bão tố mây mù."

    # 1. Parse text to JSON panels using LLM
    from agents.comic_agent import ComicDirectorAgent
    director = ComicDirectorAgent()
    script_data = director.generate_comic_script(effective_text)
    
    # Check ComfyUI readiness: 3-4 panels for responsive generation (~45s)
    comfy_info = get_comfyui_status()
    max_panels = 4 if comfy_info.get("connected") else 8
    if len(script_data) > max_panels:
        script_data = script_data[:max_panels]
    elif len(script_data) < 3:
        script_data = script_data + [
            {"panel_index": len(script_data) + 1, "image_prompt": "A heroic silhouette facing the sunset, manga style, high quality", "dialogue_text": "Hành trình vẫn tiếp diễn...", "layout_type": "wide"}
        ]

    # 2. Save to DB
    comic = Comic(user_id=user_id, story_id=request.story_id, title="Comic Adaptation")
    db.add(comic)
    db.commit()
    db.refresh(comic)
    
    # 3. Create panels and generate images
    panels_response = []
    req_mode = (request.enhancement_mode or "none").strip().lower()
    strength = request.strength if request.strength is not None else 0.35

    for idx, item in enumerate(script_data):
        p_img_prompt = item.get('image_prompt') or item.get('description') or item.get('image_description') or 'comic manga scene'
        p_dialogue = item.get('dialogue_text') or item.get('dialogue') or item.get('text') or ''
        p_layout = item.get('layout_type') or item.get('layout') or 'square'
        p_idx = item.get('panel_index', idx + 1)

        # Stage 1: Fast, reliable curated manga panel or ComfyUI
        raw_image = generate_comic_panel_image(p_img_prompt, seed=comic.id + p_idx)

        # In initial batch, if user explicitly selected upscale/enhance, enhance panel 1 to avoid timeout
        panel_enh_mode = req_mode if (req_mode in ("upscale", "enhance") and idx == 0) else "none"

        proc_result = post_processor.process_panel_image(
            comic_id=comic.id,
            panel_index=p_idx,
            raw_image=raw_image,
            prompt=p_img_prompt,
            mode=panel_enh_mode,
            strength=strength
        )

        panel = ComicPanel(
            comic_id=comic.id,
            panel_index=p_idx,
            image_prompt=p_img_prompt,
            dialogue_text=p_dialogue,
            layout_type=p_layout,
            image_url=proc_result["final_url"],
            original_image_url=proc_result["original_url"],
            processed_image_url=proc_result["processed_url"],
            final_image_url=proc_result["final_url"],
            enhancement_provider=proc_result["provider"],
            enhancement_mode=proc_result["mode"],
            enhancement_status=proc_result["status"]
        )
        db.add(panel)
        db.commit()
        db.refresh(panel)

        panels_response.append({
            'id': panel.id,
            'panel_index': panel.panel_index,
            'image_url': panel.image_url,
            'original_image_url': panel.original_image_url,
            'processed_image_url': panel.processed_image_url,
            'final_image_url': panel.final_image_url,
            'enhancement_provider': panel.enhancement_provider,
            'enhancement_mode': panel.enhancement_mode,
            'enhancement_status': panel.enhancement_status,
            'image_prompt': panel.image_prompt,
            'dialogue_text': panel.dialogue_text,
            'layout_type': panel.layout_type
        })
        
    return {"status": "success", "comic_id": comic.id, "panels": panels_response}


# ================= PRO COMIC GENERATION (Character Bible + Panel Planner) =================

class ProComicRequest(BaseModel):
    story_id: Optional[int] = None
    story_text: Optional[str] = ""
    genre: Optional[str] = ""
    style: Optional[str] = ""
    enhancement_mode: Optional[str] = "none"
    strength: Optional[float] = 0.35

@app.post("/api/comic/generate-pro")
def create_comic_pro(request: ProComicRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    Pro comic generation pipeline:
    1. ProComicAgent: builds Character Bible + Panel Plan with story logic
    2. ComfyUI: generates each panel image using rich, character-consistent prompts
    3. Stability AI: auto-enhances (if available)
    4. Returns panels + character_bible for frontend compositor
    """
    user_id = current_user.id if current_user else None
    if not user_id:
        first_user = db.query(User).first()
        if first_user:
            user_id = first_user.id

    effective_text = (request.story_text or "").strip()
    if not effective_text or len(effective_text) < 5:
        if request.story_id:
            s_rec = db.query(Story).filter(Story.id == request.story_id).first()
            if s_rec and s_rec.story_content:
                effective_text = s_rec.story_content
        if not effective_text:
            effective_text = "Mot cau chuyen hanh dong kich tinh va hao hung, nhan vat chinh buoc len dinh cao."

    # Step 1: Generate Character Bible + Panel Plan
    from agents.pro_comic_agent import ProComicAgent
    pro_agent = ProComicAgent()
    script_data = pro_agent.generate(
        story_text=effective_text,
        genre=request.genre or "",
        style=request.style or ""
    )

    character_bible = script_data.get("character_bible", [])
    story_setting = script_data.get("story_setting", "")
    panels_plan = script_data.get("panels", [])

    # Target 12 to 16 panels for a rich, complete comic chapter
    comfy_info = get_comfyui_status()
    max_panels = 12 if comfy_info.get("connected") else 16
    if len(panels_plan) > max_panels:
        panels_plan = panels_plan[:max_panels]

    # Step 2: Save Comic to DB
    character_bible = script_data.get("character_bible", [])
    location_bible = script_data.get("location_bible", [])
    story_setting = script_data.get("story_setting", "")
    panels_plan = script_data.get("panels", [])

    if len(panels_plan) > 8:
        panels_plan = panels_plan[:8]

    comic = Comic(
        user_id=user_id,
        story_id=request.story_id,
        title="Pro Comic",
        character_bible=json.dumps(character_bible, ensure_ascii=False),
        location_bible=json.dumps(location_bible, ensure_ascii=False),
        story_setting=story_setting,
        status="ready"
    )
    db.add(comic)
    db.commit()
    db.refresh(comic)

    # Step 3: Generate images for each panel
    panels_response = []
    req_mode = (request.enhancement_mode or "none").strip().lower()
    strength = request.strength if request.strength is not None else 0.35

    # Auto-select enhancement: if Stability AI available, use upscale for quality
    if req_mode == "none" and stability_service.is_available():
        auto_mode = "upscale"
    else:
        auto_mode = req_mode

    for idx, item in enumerate(panels_plan):
        p_img_prompt = item.get("image_prompt") or "manga style panel, high quality"
        p_dialogue = item.get("dialogue") or item.get("dialogue_text") or ""
        p_layout = item.get("layout_type") or "square"
        p_idx = item.get("panel_index", idx + 1)
        raw_s = str(item.get("scene_id", "1")).upper().replace("S", "").strip()
        scene_val = int(raw_s) if raw_s.isdigit() else 1

        # Stage 1: ComfyUI or Stability AI image generation
        raw_image = generate_comic_panel_image(p_img_prompt, seed=comic.id + p_idx, layout_type=p_layout)

        # Stage 2: Auto enhancement (Stability AI)
        panel_enh_mode = auto_mode if idx < 2 else "none"

        proc_result = post_processor.process_panel_image(
            comic_id=comic.id,
            panel_index=p_idx,
            raw_image=raw_image,
            prompt=p_img_prompt,
            mode=panel_enh_mode,
            strength=strength
        )

        panel = ComicPanel(
            comic_id=comic.id,
            panel_index=p_idx,
            scene_id=scene_val,
            location_name=item.get("location_name") or item.get("location") or "",
            character_names=item.get("character_names") or "",
            action_description=item.get("action") or "",
            emotion=item.get("emotion") or "",
            camera_angle=item.get("camera_angle") or "",
            image_prompt=p_img_prompt,
            dialogue_text=p_dialogue,
            speaker_name=item.get("speaker") or "",
            bubble_type=item.get("bubble_type", "speech" if p_dialogue else "none"),
            narration_text=item.get("narration") or "",
            layout_type=p_layout,
            image_url=proc_result["final_url"],
            original_image_url=proc_result["original_url"],
            processed_image_url=proc_result["processed_url"],
            final_image_url=proc_result["final_url"],
            enhancement_provider=proc_result["provider"],
            enhancement_mode=proc_result["mode"],
            enhancement_status=proc_result["status"],
            generation_status="completed" if proc_result["final_url"] else "pending"
        )
        db.add(panel)
        db.commit()
        db.refresh(panel)

        panels_response.append({
            "id": panel.id,
            "panel_index": panel.panel_index,
            "image_url": panel.image_url,
            "original_image_url": panel.original_image_url,
            "processed_image_url": panel.processed_image_url,
            "final_image_url": panel.final_image_url,
            "enhancement_provider": panel.enhancement_provider,
            "enhancement_mode": panel.enhancement_mode,
            "enhancement_status": panel.enhancement_status,
            "image_prompt": panel.image_prompt,
            "dialogue_text": p_dialogue,
            "dialogue": p_dialogue,
            "layout_type": p_layout,
            "bubble_type": panel.bubble_type,
            "speaker": panel.speaker_name,
            "speaker_name": panel.speaker_name,
            "narration": panel.narration_text,
            "narration_text": panel.narration_text,
            "location_name": panel.location_name,
            "location": panel.location_name,
            "time_of_day": item.get("time_of_day", ""),
            "emotion": panel.emotion,
            "scene_id": panel.scene_id,
            "shot_type": item.get("shot_type", ""),
            "camera_angle": panel.camera_angle,
            "generation_status": panel.generation_status
        })

    return {
        "status": "success",
        "comic_id": comic.id,
        "character_bible": character_bible,
        "location_bible": location_bible,
        "story_setting": story_setting,
        "panels": panels_response
    }



class EnhancePanelRequest(BaseModel):
    panel_id: int
    mode: str = "upscale"  # "upscale" or "enhance"
    strength: Optional[float] = 0.35

@app.post("/api/comic/enhance-panel")
def enhance_comic_panel(request: EnhancePanelRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    On-demand individual panel enhancement or upscaling via Stability AI.
    """
    panel = db.query(ComicPanel).filter(ComicPanel.id == request.panel_id).first()
    if not panel:
        return {"status": "error", "message": "Không tìm thấy khung tranh."}

    # Source is original image if available, else current image_url
    input_source = panel.original_image_url or panel.image_url
    if not input_source:
        return {"status": "error", "message": "Khung tranh không có dữ liệu ảnh."}

    # If input_source is a served endpoint URL like /api/images/original/xyz.png, convert to local path
    if input_source.startswith("/api/images/"):
        rel_subpath = input_source.replace("/api/images/", "").strip("/")
        input_source = os.path.join(post_processor.base_dir, rel_subpath)

    proc_result = post_processor.process_panel_image(
        comic_id=panel.comic_id,
        panel_index=panel.panel_index,
        raw_image=input_source,
        prompt=panel.image_prompt or "",
        mode=request.mode,
        strength=request.strength or 0.35
    )

    if proc_result.get("status") == "fallback":
        return {
            "status": "error",
            "message": "Không thể xử lý qua Stability AI lúc này (API lỗi hoặc không phản hồi). Đã giữ nguyên ảnh gốc.",
            "panel": {
                'id': panel.id,
                'panel_index': panel.panel_index,
                'image_url': panel.image_url,
                'original_image_url': panel.original_image_url,
                'processed_image_url': panel.processed_image_url,
                'final_image_url': panel.final_image_url,
                'enhancement_provider': panel.enhancement_provider,
                'enhancement_mode': panel.enhancement_mode,
                'enhancement_status': panel.enhancement_status
            }
        }

    panel.processed_image_url = proc_result["processed_url"]
    panel.final_image_url = proc_result["final_url"]
    panel.image_url = proc_result["final_url"]
    panel.enhancement_provider = proc_result["provider"]
    panel.enhancement_mode = proc_result["mode"]
    panel.enhancement_status = proc_result["status"]
    db.commit()
    db.refresh(panel)

    return {
        "status": "success",
        "panel": {
            'id': panel.id,
            'panel_index': panel.panel_index,
            'image_url': panel.image_url,
            'original_image_url': panel.original_image_url,
            'processed_image_url': panel.processed_image_url,
            'final_image_url': panel.final_image_url,
            'enhancement_provider': panel.enhancement_provider,
            'enhancement_mode': panel.enhancement_mode,
            'enhancement_status': panel.enhancement_status
        }
    }

class RegenerateComfyUIPanelRequest(BaseModel):
    panel_id: int
    prompt: Optional[str] = None

@app.post("/api/comic/generate-comfyui-panel")
def regenerate_comfyui_panel(request: RegenerateComfyUIPanelRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """
    On-demand individual panel re-generation using local ComfyUI model.
    """
    panel = db.query(ComicPanel).filter(ComicPanel.id == request.panel_id).first()
    if not panel:
        return {"status": "error", "message": "Không tìm thấy khung tranh."}

    prompt = (request.prompt or panel.image_prompt or "comic manga scene").strip()
    seed = (panel.id * 7919 + int(time.time())) % 100000000

    raw_image = generate_comic_panel_image(prompt, seed=seed)

    proc_result = post_processor.process_panel_image(
        comic_id=panel.comic_id,
        panel_index=panel.panel_index,
        raw_image=raw_image,
        prompt=prompt,
        mode="none"
    )

    panel.original_image_url = proc_result["original_url"]
    panel.processed_image_url = proc_result["processed_url"]
    panel.final_image_url = proc_result["final_url"]
    panel.image_url = proc_result["final_url"]
    panel.enhancement_provider = "comfyui"
    panel.enhancement_mode = "none"
    panel.enhancement_status = "comfyui_generated"
    db.commit()
    db.refresh(panel)

    return {
        "status": "success",
        "panel": {
            'id': panel.id,
            'panel_index': panel.panel_index,
            'image_url': panel.image_url,
            'original_image_url': panel.original_image_url,
            'processed_image_url': panel.processed_image_url,
            'final_image_url': panel.final_image_url,
            'enhancement_provider': panel.enhancement_provider,
            'enhancement_mode': panel.enhancement_mode,
            'enhancement_status': panel.enhancement_status,
            'image_prompt': panel.image_prompt,
            'dialogue_text': panel.dialogue_text,
            'layout_type': panel.layout_type
        }
    }

@app.post("/api/chat")
async def chat_with_assistant(request: ChatRequest, current_user: User = Depends(get_current_user)):
    if not current_user:
        return JSONResponse(status_code=401, content={"detail": "Not authenticated"})
    try:
        gen = get_story_generator()
        response = gen.handle_chat_instruction(request.story_text, request.user_message)
        if request.story_id:
            db = SessionLocal()
            try:
                story = db.query(Story).filter(
                    Story.id == request.story_id,
                    Story.user_id == current_user.id,
                ).first()
                if story and response.get("new_story_content"):
                    addition = response["new_story_content"]
                    story.story_content = f"{story.story_content}\n\n{addition}" if story.story_content else addition
                    story.word_count = len(story.story_content.split())
                    db.commit()
            finally:
                db.close()
        return {"status": "success", "chat_reply": response.get("chat_reply", ""), "new_story_content": response.get("new_story_content", "")}
    except Exception as e:
        return {"status": "error", "message": str(e)}

# ===== STORY MEMORY SYSTEM =====
from agents.story_memory import StoryBible, StoryMemory
from agents.memory_extractor import MemoryExtractor
from agents.copilot_agent import CopilotAgent

# In-memory session store for story memories
STORY_SESSIONS = {}

def get_story_session(session_id: str, current_user: User):
    memory = STORY_SESSIONS.get(session_id)
    if memory or not current_user:
        return memory

    db = SessionLocal()
    try:
        story = db.query(Story).filter(
            Story.session_id == session_id,
            Story.user_id == current_user.id,
        ).first()
        if not story or not story.memory_data:
            return None

        memory = StoryMemory.from_dict(json.loads(story.memory_data))
        STORY_SESSIONS[session_id] = memory
        return memory
    except (json.JSONDecodeError, TypeError, ValueError) as e:
        print(f"Session restore error: {e}")
        return None
    finally:
        db.close()

def memory_json(memory: StoryMemory) -> str:
    return json.dumps(memory.to_dict(), ensure_ascii=False)

copilot = None
def get_copilot():
    global copilot
    if copilot is None:
        copilot = CopilotAgent()
    return copilot


memory_extractor = None
def get_memory_extractor():
    global memory_extractor
    if memory_extractor is None:
        memory_extractor = MemoryExtractor()
    return memory_extractor

class InitStoryRequest(BaseModel):
    refined_prompt: str
    story_length: str = "long"

class ChapterRequest(BaseModel):
    session_id: str
    user_instruction: str = ""

class EndStoryRequest(BaseModel):
    session_id: str

class CopilotEventRequest(BaseModel):
    session_id: str
    event_type: str
    event_data: str
    story_id: int | None = None

@app.post("/api/copilot-event")
def copilot_event(request: CopilotEventRequest, current_user: User = Depends(get_current_user)):
    try:
        memory = None
        if current_user:
            db = SessionLocal()
            try:
                story_query = db.query(Story).filter(Story.user_id == current_user.id)
                if request.story_id:
                    story_query = story_query.filter(Story.id == request.story_id)
                elif request.session_id and request.session_id != 'temp':
                    story_query = story_query.filter(Story.session_id == request.session_id)
                else:
                    story_query = None

                if story_query:
                    story = story_query.first()
                    if story and story.memory_data:
                        try:
                            memory = StoryMemory.from_dict(json.loads(story.memory_data))
                        except Exception:
                            pass
            finally:
                db.close()

        if memory is None and request.session_id:
            memory = get_story_session(request.session_id, current_user)

        agent = get_copilot()
        # Copilot process the event and decides the action
        result = agent.process_event(request.event_type, request.event_data, memory)

        # Safe print for Windows
        try:
            print(f"--- MASTER CONTROLLER THOUGHT ---")
            print(str(result.get('thought', 'No thought')).encode('utf-8', 'replace').decode('utf-8'))
            print(f"ACTION: {result.get('action')}")
            print(f"---------------------------------")
        except:
            pass

        # Save memory changes to DB if story exists
        if memory and current_user:
            db = SessionLocal()
            try:
                story_query = db.query(Story).filter(Story.user_id == current_user.id)
                if request.story_id:
                    story_query = story_query.filter(Story.id == request.story_id)
                elif request.session_id and request.session_id != 'temp':
                    story_query = story_query.filter(Story.session_id == request.session_id)
                else:
                    story_query = None
                if story_query:
                    story = story_query.first()
                    if story:
                        story.memory_data = memory_json(memory)
                        db.commit()
            except Exception as e:
                pass
            finally:
                db.close()

        return {"status": "success", "data": result}
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"status": "error", "message": str(e)}
    
@app.post("/api/init-story")
def init_story(request: InitStoryRequest, current_user: User = Depends(get_current_user)):
    try:
        extractor = get_memory_extractor()
        gen = get_story_generator()

        # Step 1: Extract Story Bible from refined_prompt
        bible = extractor.extract_bible(request.refined_prompt)

        # Step 2: Create Memory with Bible
        memory = StoryMemory(story_bible=bible)
        session_id = memory.session_id

        # Step 3: Generate Chapter 1 (streaming)
        def stream_chapter_1():
            chapter_text = ""
            saved_story_id = None
            try:
                for chunk in gen.generate_chapter_stream(memory):
                    chapter_text += chunk
                    yield chunk
            except Exception as e:
                yield f"\n\n[GENERATION_ERROR:{safe_generation_error(e, 'sinh chương')}]"
                return

            # Step 4: Update memory with chapter 1
            memory.append_chapter(chapter_text)
            try:
                extractor.extract_memory(chapter_text, memory)
            except Exception as e:
                print(f"Memory extraction error: {e}")

            # Store session
            STORY_SESSIONS[session_id] = memory

            # Save to DB
            word_count = len(chapter_text.split())
            if word_count > 10 and current_user:
                db = SessionLocal()
                try:
                    import json
                    from dataclasses import asdict
                    new_story = Story(
                        session_id=session_id,
                        user_id=current_user.id,
                        refined_prompt=request.refined_prompt,
                        story_content=chapter_text,
                        word_count=word_count,
                        bible_data=json.dumps(memory.story_bible.to_dict(), ensure_ascii=False) if memory.story_bible else None,
                        memory_data=memory_json(memory)
                    )
                    db.add(new_story)
                    db.commit()
                    db.refresh(new_story)
                    saved_story_id = new_story.id
                except Exception as e:
                    print(f"DB Error: {e}")
                finally:
                    db.close()

            # Yield session_id at the end as a special marker
            yield f"\n\n[SESSION_ID:{session_id}]"
            if saved_story_id:
                yield f"\n\n[STORY_ID:{saved_story_id}]"

        return StreamingResponse(stream_chapter_1(), media_type="text/plain")
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"status": "error", "message": str(e)}

@app.post("/api/generate-chapter")
def generate_chapter(request: ChapterRequest, current_user: User = Depends(get_current_user)):
    try:
        memory = get_story_session(request.session_id, current_user)
        if not memory:
            return JSONResponse(status_code=404, content={"status": "error", "message": "Session khong ton tai hoac da het han."})

        if not current_user:
            return JSONResponse(status_code=401, content={"status": "error", "message": "Chưa đăng nhập"})
        db = SessionLocal()
        try:
            story = db.query(Story).filter(
                Story.session_id == request.session_id,
                Story.user_id == current_user.id,
            ).first()
            if not story:
                return JSONResponse(status_code=404, content={"status": "error", "message": "Không tìm thấy phiên truyện hoặc không có quyền truy cập."})
        finally:
            db.close()

        gen = get_story_generator()
        extractor = get_memory_extractor()

        def stream_next_chapter():
            chapter_text = ""
            try:
                for chunk in gen.generate_chapter_stream(memory, request.user_instruction):
                    chapter_text += chunk
                    yield chunk
            except Exception as e:
                yield f"\n\n[GENERATION_ERROR:{safe_generation_error(e, 'sinh chương')}]"
                return

            # Update memory
            memory.append_chapter(chapter_text)
            try:
                extractor.extract_memory(chapter_text, memory)
            except Exception as e:
                print(f"Memory extraction error: {e}")

            # Update session
            STORY_SESSIONS[request.session_id] = memory

            # Update story in DB
            if current_user:
                db = SessionLocal()
                try:
                    story = db.query(Story).filter(Story.session_id == request.session_id).first()
                    if story:
                        story.story_content = memory.get_full_story()
                        story.word_count = len(story.story_content.split())
                        story.memory_data = memory_json(memory)
                        db.commit()
                except Exception as e:
                    print(f"DB Error: {e}")
                finally:
                    db.close()

        return StreamingResponse(stream_next_chapter(), media_type="text/plain")
    except Exception as e:
        import traceback
        traceback.print_exc()
        return {"status": "error", "message": str(e)}

@app.post("/api/end-story")
def end_story(request: EndStoryRequest, current_user: User = Depends(get_current_user)):
    try:
        memory = get_story_session(request.session_id, current_user)
        if not memory:
            return JSONResponse(status_code=404, content={"status": "error", "message": "Session khong ton tai."})

        if not current_user:
            return JSONResponse(status_code=401, content={"status": "error", "message": "Chưa đăng nhập"})
        db = SessionLocal()
        try:
            story = db.query(Story).filter(
                Story.session_id == request.session_id,
                Story.user_id == current_user.id,
            ).first()
            if not story:
                return JSONResponse(status_code=404, content={"status": "error", "message": "Không tìm thấy phiên truyện hoặc không có quyền truy cập."})
        finally:
            db.close()

        gen = get_story_generator()

        def stream_ending():
            ending_text = ""
            try:
                for chunk in gen.generate_ending_stream(memory):
                    ending_text += chunk
                    yield chunk
            except Exception as e:
                yield f"\n\n[GENERATION_ERROR:{safe_generation_error(e, 'viết đoạn kết')}]"
                return

            memory.append_chapter(ending_text)

            # Final DB save
            if current_user:
                db = SessionLocal()
                try:
                    story = db.query(Story).filter(Story.session_id == request.session_id).first()
                    if story:
                        story.story_content = memory.get_full_story()
                        story.word_count = len(story.story_content.split())
                        story.memory_data = memory_json(memory)
                        db.commit()
                except Exception as e:
                    print(f"DB Error: {e}")
                finally:
                    db.close()

            # Clean up session
            del STORY_SESSIONS[request.session_id]

        return StreamingResponse(stream_ending(), media_type="text/plain")
    except Exception as e:
        return {"status": "error", "message": str(e)}

from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

# Mount frontend static files
frontend_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), "frontend")
if os.path.exists(frontend_path):
    app.mount("/static", StaticFiles(directory=frontend_path), name="static")

    @app.get("/")
    async def serve_frontend():
        return FileResponse(os.path.join(frontend_path, "index.html"))

    @app.get("/{path:path}")
    async def serve_frontend_paths(path: str):
        file_path = os.path.join(frontend_path, path)
        if os.path.exists(file_path) and os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(frontend_path, "index.html"))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", "8000")))
