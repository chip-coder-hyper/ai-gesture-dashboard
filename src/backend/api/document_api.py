import os
import shutil
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from services.document_processor import DocumentProcessor
from services.vector_db import VectorDBManager 
from services.llm_factory import LLMFactory

from database.db_config import get_db
from database.models import ChatSession, ChatMessage, User
from api.auth_api import get_current_user

router = APIRouter()
processor = DocumentProcessor()
db_manager = VectorDBManager() 

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)

class ChatRequest(BaseModel):
    session_id: int
    query: str

# --- 1. TẢI TÀI LIỆU VÀ SINH CÂU HỎI GỢI Ý ---
@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        file_path = os.path.join(UPLOAD_DIR, file.filename)
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        new_session = ChatSession(user_id=current_user.id, title=f"File: {file.filename}")
        db.add(new_session)
        db.commit()
        db.refresh(new_session)
        session_id = new_session.id
        
        chunks = processor.process_document(file_path)
        
        suggested_questions = []
        if chunks:
            for chunk in chunks:
                if not hasattr(chunk, "metadata") or chunk.metadata is None:
                    chunk.metadata = {}
                chunk.metadata["session_id"] = str(session_id)
                chunk.metadata["user_id"] = str(current_user.id)
            db_manager.add_documents(chunks)
            
            # AI đọc lướt đoạn đầu để sinh câu hỏi gợi ý
            try:
                api_key = os.getenv("GEMINI_API_KEY")
                llm = LLMFactory.get_llm(provider_name="gemini", api_key=api_key)
                prompt = f"Dựa vào nội dung sau, gợi ý 3 câu hỏi ngắn gọn (dưới 15 chữ) mà người dùng có thể hỏi. Trả về 3 dòng, không gạch đầu dòng:\n\n{chunks[0].page_content[:800]}"
                
                if hasattr(llm, "invoke"):
                    res = llm.invoke(prompt)
                    text = res.content if hasattr(res, "content") else str(res)
                else:
                    res = llm.generate_content(prompt)
                    text = res.text
                    
                suggested_questions = [q.strip("- *1234567890.") for q in text.strip().split("\n") if q.strip()][:3]
            except Exception:
                suggested_questions = ["Tóm tắt tài liệu này?", "Điểm nổi bật nhất là gì?", "Ứng dụng của tài liệu?"]
        
        if os.path.exists(file_path):
            os.remove(file_path)
        
        return {
            "status": "success",
            "session_id": session_id,
            "filename": file.filename,
            "suggested_questions": suggested_questions,
            "message": "Upload thành công!"
        }
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

# --- 2. CHAT TỰ DO ---
@router.post("/chat")
async def free_chat_with_rag(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    try:
        user_query = request.query
        session_id = request.session_id
        context = ""

        session_record = db.query(ChatSession).filter(ChatSession.id == session_id, ChatSession.user_id == current_user.id).first()
        if not session_record:
            raise HTTPException(status_code=403, detail="Không có quyền truy cập!")

        db.add(ChatMessage(session_id=session_id, role="user", content=user_query))
        db.commit()

        history_records = db.query(ChatMessage).filter(ChatMessage.session_id == session_id).order_by(ChatMessage.created_at.asc()).all()[-6:]
        history_text = "\n".join([f"{msg.role}: {msg.content}" for msg in history_records[:-1]])

        try:
            print(f"🔍 Đang tìm kiếm tài liệu cho Session ID: {session_id}")
            
            # ĐÃ SỬA: Gọi đúng db_manager.db theo thiết kế của file vector_db.py
            if hasattr(db_manager, "db") and db_manager.db:
                docs = db_manager.db.similarity_search(
                    user_query, 
                    k=3,
                    filter={"session_id": str(session_id)} 
                )
                context = "\n".join([doc.page_content for doc in docs])
                print(f"✅ Đã hút thành công {len(docs)} đoạn tài liệu liên quan từ DB lên cho AI!")
            else:
                print("⚠️ CẢNH BÁO: Không tìm thấy kho chứa 'db' bên trong VectorDBManager!")
                context = ""
                
        except Exception as e_db:
            print(f"❌ LỖI NGHIÊM TRỌNG TẠI VECTOR DB: {str(e_db)}")
            context = ""

        api_key = os.getenv("GEMINI_API_KEY")
        llm = LLMFactory.get_llm(provider_name="gemini", api_key=api_key)

        prompt = f"""Bạn là trợ lý AI chuyên nghiệp. Phân tích tài liệu và lịch sử để trả lời câu hỏi.
[NGỮ CẢNH TÀI LIỆU]:\n{context}\n
[LỊCH SỬ]:\n{history_text}\n
[CÂU HỎI MỚI]: {user_query}\n[TRẢ LỜI]:"""

        if hasattr(llm, "invoke"):
            ai_response = llm.invoke(prompt)
            ai_response_text = ai_response.content if hasattr(ai_response, "content") else str(ai_response)
        else:
            ai_response = llm.generate_content(prompt)
            ai_response_text = ai_response.text

        db.add(ChatMessage(session_id=session_id, role="ai", content=ai_response_text))
        db.commit()

        return {"status": "success", "ai_response": ai_response_text}
    except Exception as e:
        import traceback
        print("\n🚨🚨🚨 LỖI TRẦN TRỤI TỪ BACKEND 🚨🚨🚨")
        traceback.print_exc()
        print("🚨🚨🚨===========================🚨🚨🚨\n")
        raise HTTPException(status_code=500, detail=str(e))

# --- 3. LẤY DANH SÁCH CÁC PHIÊN CHAT CŨ ---
@router.get("/sessions")
def get_user_sessions(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    sessions = db.query(ChatSession).filter(ChatSession.user_id == current_user.id).order_by(ChatSession.created_at.desc()).all()
    return [{"id": s.id, "title": s.title} for s in sessions]

# --- 4. LẤY TIN NHẮN CỦA MỘT PHIÊN CHAT ---
@router.get("/sessions/{session_id}/messages")
def get_session_messages(session_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    messages = db.query(ChatMessage).filter(ChatMessage.session_id == session_id).order_by(ChatMessage.created_at.asc()).all()
    return [{"role": m.role, "content": m.content} for m in messages]