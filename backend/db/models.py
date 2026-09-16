from sqlalchemy import Column, String, DateTime, Integer, Text, ForeignKey, create_engine, Unicode, UnicodeText
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import os

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True)
    email = Column(String(255), unique=True, index=True, nullable=True)
    username = Column(String(50), unique=True, index=True)
    name = Column(Unicode(100), nullable=True)
    password_hash = Column(String(128), nullable=True)  # nullable for social-only users
    avatar_url = Column(UnicodeText, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    stories = relationship("Story", back_populates="author")
    auth_accounts = relationship("AuthAccount", back_populates="user")

class AuthAccount(Base):
    __tablename__ = "auth_accounts"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    provider = Column(String(20), nullable=False)  # 'google', 'facebook', 'x'
    provider_account_id = Column(String(255), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", back_populates="auth_accounts")

class TokenBlacklist(Base):
    __tablename__ = "token_blacklist"
    
    id = Column(Integer, primary_key=True)
    jti = Column(String(36), unique=True, index=True, nullable=False)
    expires_at = Column(DateTime, nullable=False)

class Story(Base):
    __tablename__ = "stories"
    
    id = Column(Integer, primary_key=True)
    session_id = Column(String(100), index=True, nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    initial_prompt = Column(Unicode(500))
    refined_prompt = Column(UnicodeText)
    genre = Column(Unicode(100))
    tone = Column(Unicode(100))
    story_content = Column(UnicodeText)
    word_count = Column(Integer)
    bible_data = Column(UnicodeText, nullable=True)
    memory_data = Column(UnicodeText, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    author = relationship("User", back_populates="stories")

class Comic(Base):
    __tablename__ = 'comics'
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    story_id = Column(Integer, ForeignKey('stories.id'), nullable=True)
    title = Column(Unicode(200))
    character_bible = Column(UnicodeText, nullable=True)
    location_bible = Column(UnicodeText, nullable=True)
    story_setting = Column(UnicodeText, nullable=True)
    status = Column(String(50), default='ready')
    created_at = Column(DateTime, default=datetime.utcnow)
    
    author = relationship('User')
    panels = relationship('ComicPanel', back_populates='comic', cascade='all, delete-orphan', order_by='ComicPanel.panel_index')

class ComicPanel(Base):
    __tablename__ = 'comic_panels'
    id = Column(Integer, primary_key=True)
    comic_id = Column(Integer, ForeignKey('comics.id'))
    panel_index = Column(Integer)
    scene_id = Column(Integer, nullable=True)
    location_name = Column(Unicode(200), nullable=True)
    character_names = Column(Unicode(255), nullable=True)
    action_description = Column(UnicodeText, nullable=True)
    emotion = Column(Unicode(100), nullable=True)
    camera_angle = Column(Unicode(100), nullable=True)
    image_prompt = Column(UnicodeText)
    dialogue_text = Column(UnicodeText, nullable=True)
    speaker_name = Column(Unicode(100), nullable=True)
    bubble_type = Column(String(50), default='speech')
    narration_text = Column(UnicodeText, nullable=True)
    image_url = Column(UnicodeText, nullable=True)
    original_image_url = Column(UnicodeText, nullable=True)
    processed_image_url = Column(UnicodeText, nullable=True)
    final_image_url = Column(UnicodeText, nullable=True)
    enhancement_provider = Column(String(50), nullable=True)
    enhancement_mode = Column(String(50), nullable=True)
    enhancement_status = Column(String(50), nullable=True)
    generation_status = Column(String(50), default='pending')
    error_message = Column(UnicodeText, nullable=True)
    layout_type = Column(String(50), default='square')
    
    comic = relationship('Comic', back_populates='panels')

class ComicJob(Base):
    __tablename__ = 'comic_jobs'
    id = Column(String(50), primary_key=True)  # UUID
    comic_id = Column(Integer, ForeignKey('comics.id'), nullable=True)
    story_id = Column(Integer, ForeignKey('stories.id'), nullable=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=True)
    status = Column(String(50), default='pending')  # pending, processing, completed, failed, partial
    current_step = Column(Unicode(255), default='Khởi tạo tiến trình...')
    progress_percent = Column(Integer, default=0)
    total_panels = Column(Integer, default=0)
    completed_panels = Column(Integer, default=0)
    error_message = Column(UnicodeText, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    comic = relationship('Comic')

# Initialize DB — Supports SQL Server, PostgreSQL, or SQLite fallback
DATABASE_URL = os.environ.get("DATABASE_URL", "").strip()

if DATABASE_URL.startswith("mssql"):
    # Microsoft SQL Server (Local SQLEXPRESS or Cloud MSSQL)
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
elif DATABASE_URL.startswith("postgresql") or DATABASE_URL.startswith("postgres"):
    # PostgreSQL (Neon, Supabase, Railway, Render)
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
    engine = create_engine(DATABASE_URL, pool_pre_ping=True, pool_size=5, max_overflow=10)
elif DATABASE_URL:
    engine = create_engine(DATABASE_URL, pool_pre_ping=True)
else:
    # SQLite (local fallback pointing reliably to backend/narrai.db)
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_file_path = os.path.join(base_dir, 'narrai.db')
    engine = create_engine(f"sqlite:///{db_file_path}", connect_args={'check_same_thread': False})

Base.metadata.create_all(engine)

# Auto-migrate missing columns for existing SQLite / relational tables
def ensure_schema_compatibility():
    from sqlalchemy import inspect, text
    try:
        inspector = inspect(engine)
        existing_tables = inspector.get_table_names()
        is_mssql = engine.dialect.name == "mssql"
        add_prefix = "ADD" if is_mssql else "ADD COLUMN"
        text_type = "NVARCHAR(MAX)" if is_mssql else "TEXT"
        int_type = "INT" if is_mssql else "INTEGER"
        
        if 'comics' in existing_tables:
            cols = {c['name'] for c in inspector.get_columns('comics')}
            with engine.connect() as conn:
                for col_name, col_type in [
                    ('character_bible', text_type),
                    ('location_bible', text_type),
                    ('story_setting', text_type),
                    ('status', "VARCHAR(50) DEFAULT 'ready'")
                ]:
                    if col_name not in cols:
                        try:
                            conn.execute(text(f"ALTER TABLE comics {add_prefix} {col_name} {col_type}"))
                        except Exception:
                            pass
                conn.commit()

        if 'comic_panels' in existing_tables:
            cols = {c['name'] for c in inspector.get_columns('comic_panels')}
            with engine.connect() as conn:
                for col_name, col_type in [
                    ('scene_id', int_type),
                    ('location_name', 'NVARCHAR(200)' if is_mssql else 'VARCHAR(200)'),
                    ('character_names', 'NVARCHAR(255)' if is_mssql else 'VARCHAR(255)'),
                    ('action_description', text_type),
                    ('emotion', 'NVARCHAR(100)' if is_mssql else 'VARCHAR(100)'),
                    ('camera_angle', 'NVARCHAR(100)' if is_mssql else 'VARCHAR(100)'),
                    ('speaker_name', 'NVARCHAR(100)' if is_mssql else 'VARCHAR(100)'),
                    ('bubble_type', "VARCHAR(50) DEFAULT 'speech'"),
                    ('narration_text', text_type),
                    ('image_url', text_type),
                    ('original_image_url', text_type),
                    ('processed_image_url', text_type),
                    ('final_image_url', text_type),
                    ('enhancement_provider', 'VARCHAR(50)'),
                    ('enhancement_mode', 'VARCHAR(50)'),
                    ('enhancement_status', 'VARCHAR(50)'),
                    ('generation_status', "VARCHAR(50) DEFAULT 'pending'"),
                    ('error_message', text_type),
                    ('layout_type', "VARCHAR(50) DEFAULT 'square'")
                ]:
                    if col_name not in cols:
                        try:
                            conn.execute(text(f"ALTER TABLE comic_panels {add_prefix} {col_name} {col_type}"))
                        except Exception:
                            pass
                conn.commit()
    except Exception as e:
        logger.warning(f"[DB Schema Init Warning] {repr(e)}")

ensure_schema_compatibility()
