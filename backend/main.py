from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from pydantic import BaseModel
import json
import os
from dotenv import load_dotenv

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

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
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
from fastapi.responses import StreamingResponse, JSONResponse
from db.models import Story, User, engine
from sqlalchemy.orm import sessionmaker, Session
from auth import verify_password, get_password_hash, create_access_token, decode_access_token

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
        
    if token in USER_CACHE:
        return USER_CACHE[token]
        
    payload = decode_access_token(token)
    if not payload:
        return None
    username: str = payload.get("sub")
    user = db.query(User).filter(User.username == username).first()
    
    if user:
        USER_CACHE[token] = user
        
    return user

# ============ PYDANTIC MODELS ============
class ChatInterviewRequest(BaseModel):
    chat_history: list

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

# ============ AUTH ENDPOINTS ============

@app.post("/api/register")
def register_user(user: UserCreate, db: Session = Depends(get_db)):
    existing = db.query(User).filter(User.username == user.username).first()
    if existing:
        raise HTTPException(status_code=400, detail="Tên đăng nhập đã tồn tại")
    
    hashed_password = get_password_hash(user.password)
    new_user = User(username=user.username, password_hash=hashed_password)
    db.add(new_user)
    db.commit()
    return {"status": "success", "message": "Đăng ký thành công"}

@app.post("/api/login")
def login_user(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == form_data.username).first()
    if not user or not verify_password(form_data.password, user.password_hash):
        raise HTTPException(status_code=400, detail="Sai tên đăng nhập hoặc mật khẩu")
    
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer", "username": user.username}

@app.get("/api/me")
def read_users_me(current_user: User = Depends(get_current_user)):
    if not current_user:
        raise HTTPException(status_code=401, detail="Chưa đăng nhập")
    return {"username": current_user.username}

# ============ CORE ENDPOINTS ============

@app.post("/api/chat-interview")
def chat_interview(request: ChatInterviewRequest):
    try:
        qa = get_qa_refiner()
        response = qa.chat_interview(request.chat_history)
        is_ready = "[READY]" in response
        cleaned_response = response.replace("[READY]", "").strip()
        return {"status": "success", "message": cleaned_response, "is_ready": is_ready}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.post("/api/refine-prompt")
def refine_prompt(request: ChatInterviewRequest):
    try:
        qa = get_qa_refiner()
        refined = qa.refine_prompt(request.chat_history)
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
        "missing_keys": missing,
    }

# ================= COMIC ENDPOINTS =================
from services.image_gen import generate_comic_panel_image
from db.models import Comic, ComicPanel

class ComicRequest(BaseModel):
    story_id: int
    story_text: str

@app.post("/api/comic/generate")
def create_comic(request: ComicRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    if not current_user:
        return {"status": "error", "message": "Bạn chưa đăng nhập."}

    story = db.query(Story).filter(
        Story.id == request.story_id,
        Story.user_id == current_user.id,
    ).first()
    if not story:
        return {"status": "error", "message": "Không tìm thấy truyện hoặc không có quyền truy cập."}
        
    # 1. Parse text to JSON panels using LLM
    from agents.comic_agent import ComicDirectorAgent
    director = ComicDirectorAgent()
    script_data = director.generate_comic_script(request.story_text)
    
    # 2. Save to DB
    comic = Comic(user_id=current_user.id, story_id=request.story_id, title="Comic Adaptation")
    db.add(comic)
    db.commit()
    db.refresh(comic)
    
    # 3. Create panels and generate images
    panels_response = []
    for item in script_data:
        # LLMs often invent slightly different keys, so we check alternatives
        p_img_prompt = item.get('image_prompt') or item.get('description') or item.get('image_description') or 'comic manga scene'
        p_dialogue = item.get('dialogue_text') or item.get('dialogue') or item.get('text') or ''
        p_layout = item.get('layout_type') or item.get('layout') or 'square'
        
        # Generate image (using our mock Pollinations API for instant demo)
        img_url = generate_comic_panel_image(p_img_prompt, seed=comic.id)
        
        panel = ComicPanel(
            comic_id=comic.id,
            panel_index=item.get('panel_index', 1),
            image_prompt=p_img_prompt,
            dialogue_text=p_dialogue,
            layout_type=p_layout,
            image_url=img_url
        )
        db.add(panel)
        db.commit()
        
        panels_response.append({
            'panel_index': panel.panel_index,
            'image_url': panel.image_url,
            'image_prompt': panel.image_prompt,
            'dialogue_text': panel.dialogue_text,
            'layout_type': panel.layout_type
        })
        
    return {"status": "success", "comic_id": comic.id, "panels": panels_response}

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
        memory = get_story_session(request.session_id, current_user)

        if not current_user:
            return JSONResponse(status_code=401, content={"status": "error", "message": "Chưa đăng nhập"})
        db = SessionLocal()
        try:
            story_query = db.query(Story).filter(Story.user_id == current_user.id)
            if request.story_id:
                story_query = story_query.filter(Story.id == request.story_id)
            else:
                story_query = story_query.filter(Story.session_id == request.session_id)
            story = story_query.first()
            if not story:
                return JSONResponse(status_code=404, content={"status": "error", "message": "Không tìm thấy phiên truyện hoặc không có quyền truy cập."})
            if memory is None and story.memory_data:
                memory = StoryMemory.from_dict(json.loads(story.memory_data))
        finally:
            db.close()
        
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
            
        
        # Save memory changes to DB
        if memory and current_user:
            db = SessionLocal()
            try:
                story_query = db.query(Story).filter(Story.user_id == current_user.id)
                if request.story_id:
                    story_query = story_query.filter(Story.id == request.story_id)
                else:
                    story_query = story_query.filter(Story.session_id == request.session_id)
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
