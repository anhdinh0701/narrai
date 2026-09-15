"""
NarrAI Database Viewer Utility.
Runs anywhere, connects to the active database (SQL Server, PostgreSQL, or SQLite),
and prints all registered users, stories, and comics.

Usage:
    python view_database.py
"""
import sys
import os

# Ensure UTF-8 output on Windows terminal
sys.stdout.reconfigure(encoding='utf-8')

backend_dir = os.path.join(os.path.dirname(__file__), "backend")
if os.path.exists(backend_dir):
    sys.path.insert(0, backend_dir)
else:
    sys.path.insert(0, os.path.dirname(__file__))

from dotenv import load_dotenv
load_dotenv(os.path.join(backend_dir, ".env") if os.path.exists(backend_dir) else ".env")

from db.models import engine, User, Story, Comic, ComicPanel, TokenBlacklist
from sqlalchemy.orm import sessionmaker

SessionLocal = sessionmaker(bind=engine)

def view_db():
    print("=" * 75)
    print(f"  NARR AI - DATABASE VIEWER  |  Engine: {engine.dialect.name.upper()}")
    print("=" * 75)
    
    with SessionLocal() as db:
        # 1. USERS
        users = db.query(User).order_by(User.id.asc()).all()
        print(f"\n[1] BẢNG USERS ({len(users)} tài khoản đã đăng ký):")
        print("-" * 75)
        print(f"{'ID':<4} | {'Username':<20} | {'Email':<28} | {'Họ tên':<15}")
        print("-" * 75)
        for u in users:
            name_display = u.name or "(Chưa đặt)"
            print(f"{u.id:<4} | {u.username:<20} | {u.email:<28} | {name_display:<15}")
        print("-" * 75)
        
        # 2. STORIES
        stories = db.query(Story).order_by(Story.id.desc()).all()
        print(f"\n[2] BẢNG STORIES ({len(stories)} tác phẩm đã lưu):")
        print("-" * 75)
        print(f"{'ID':<4} | {'User ID':<8} | {'Số từ':<8} | {'Thời gian tạo':<20} | {'Trích đoạn'}")
        print("-" * 75)
        for s in stories:
            created_str = s.created_at.strftime("%Y-%m-%d %H:%M") if s.created_at else "N/A"
            snippet = (s.story_content or "").strip().replace("\n", " ")[:35] + "..."
            print(f"{s.id:<4} | {str(s.user_id):<8} | {str(s.word_count):<8} | {created_str:<20} | {snippet}")
        print("-" * 75)
        
        # 3. COMICS
        panels_count = db.query(ComicPanel).count()
        print(f"\n[3] BẢNG COMIC PANELS ({panels_count} khung tranh đã sinh):")
        print("-" * 75)
        panels = db.query(ComicPanel).order_by(ComicPanel.id.desc()).limit(5).all()
        print(f"{'ID':<4} | {'Comic ID':<10} | {'Khung #':<8} | {'Layout':<8} | {'Dung lượng ảnh base64'}")
        print("-" * 75)
        for p in panels:
            img_len = f"{len(p.image_url):,} ký tự" if p.image_url else "None"
            print(f"{p.id:<4} | {str(p.comic_id):<10} | {str(p.panel_index):<8} | {str(p.layout_type):<8} | {img_len}")
        print("-" * 75)
        
        # 4. BLACKLIST
        bl_count = db.query(TokenBlacklist).count()
        print(f"\n[4] BẢNG TOKEN BLACKLIST ({bl_count} token đã bị vô hiệu hóa khi logout)")
        print("=" * 75)

if __name__ == "__main__":
    view_db()
