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
    created_at = Column(DateTime, default=datetime.utcnow)
    
    author = relationship('User')
    panels = relationship('ComicPanel', back_populates='comic', cascade='all, delete-orphan')

class ComicPanel(Base):
    __tablename__ = 'comic_panels'
    id = Column(Integer, primary_key=True)
    comic_id = Column(Integer, ForeignKey('comics.id'))
    panel_index = Column(Integer)
    image_prompt = Column(UnicodeText)
    dialogue_text = Column(UnicodeText)
    image_url = Column(UnicodeText, nullable=True)
    original_image_url = Column(UnicodeText, nullable=True)
    processed_image_url = Column(UnicodeText, nullable=True)
    final_image_url = Column(UnicodeText, nullable=True)
    enhancement_provider = Column(String(50), nullable=True)
    enhancement_mode = Column(String(50), nullable=True)
    enhancement_status = Column(String(50), nullable=True)
    layout_type = Column(String(50), default='square')
    
    comic = relationship('Comic', back_populates='panels')

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
    # SQLite (local fallback)
    engine = create_engine('sqlite:///narrai.db', connect_args={'check_same_thread': False})

Base.metadata.create_all(engine)
