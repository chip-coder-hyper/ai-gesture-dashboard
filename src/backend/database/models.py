from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Text
from sqlalchemy.orm import declarative_base, relationship
from datetime import datetime

# Cấu trúc nền tảng của các bảng
Base = declarative_base()

# 1. Bảng Người dùng
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Mối quan hệ: 1 User có nhiều Session
    sessions = relationship("ChatSession", back_populates="owner")

# 2. Bảng Phiên chat (Lưu ở thanh Sidebar)
class ChatSession(Base):
    __tablename__ = "chat_sessions"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    title = Column(String, default="Cuộc trò chuyện mới")
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Mối quan hệ
    owner = relationship("User", back_populates="sessions")
    messages = relationship("ChatMessage", back_populates="session", cascade="all, delete-orphan")

# 3. Bảng Lịch sử Tin nhắn
class ChatMessage(Base):
    __tablename__ = "chat_messages"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("chat_sessions.id"))
    role = Column(String)  # Sẽ là "user" hoặc "assistant"
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Mối quan hệ
    session = relationship("ChatSession", back_populates="messages")