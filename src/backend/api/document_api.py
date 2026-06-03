import os
import shutil
import uuid
import traceback

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from services.document_processor import DocumentProcessor
from services.vector_db import VectorDBManager
from services.llm_factory import LLMFactory

from database.db_config import get_db
from database.models import ChatSession, ChatMessage, User


router = APIRouter()
processor = DocumentProcessor()
db_manager = VectorDBManager()

UPLOAD_DIR = "uploads"
os.makedirs(UPLOAD_DIR, exist_ok=True)


class ChatRequest(BaseModel):
    session_id: int
    query: str


def get_demo_user(db: Session = Depends(get_db)):
    """
    Demo mode:
    - Không yêu cầu đăng nhập.
    - Tự lấy hoặc tạo user demo_guest.
    """
    try:
        if hasattr(User, "username"):
            user = db.query(User).filter(User.username == "demo_guest").first()
            if user:
                return user

        user = db.query(User).first()
        if user:
            return user

        values = {}
        column_names = set(User.__table__.columns.keys())

        if "username" in column_names:
            values["username"] = "demo_guest"

        if "email" in column_names:
            values["email"] = "demo_guest@example.com"

        if "hashed_password" in column_names:
            values["hashed_password"] = "demo_password"

        if "password" in column_names:
            values["password"] = "demo_password"

        if "role" in column_names:
            values["role"] = "user"

        user = User(**values)
        db.add(user)
        db.commit()
        db.refresh(user)

        return user

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(
            status_code=500,
            detail=f"Không thể tạo demo user: {str(e)}",
        )


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_demo_user),
):
    file_path = None

    try:
        safe_filename = os.path.basename(file.filename)
        unique_filename = f"{uuid.uuid4().hex}_{safe_filename}"
        file_path = os.path.join(UPLOAD_DIR, unique_filename)

        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        new_session = ChatSession(
            user_id=current_user.id,
            title=f"File: {safe_filename}",
        )

        db.add(new_session)
        db.commit()
        db.refresh(new_session)

        session_id = new_session.id

        chunks = processor.process_document(file_path)

        suggested_questions = [
            "Tóm tắt tài liệu này?",
            "Điểm nổi bật nhất là gì?",
            "Ứng dụng của tài liệu?",
        ]

        if chunks:
            for chunk in chunks:
                if not hasattr(chunk, "metadata") or chunk.metadata is None:
                    chunk.metadata = {}

                chunk.metadata["session_id"] = str(session_id)
                chunk.metadata["user_id"] = str(current_user.id)

            db_manager.add_documents(chunks)

            try:
                api_key = os.getenv("GEMINI_API_KEY")
                llm = LLMFactory.get_llm(
                    provider_name="gemini",
                    api_key=api_key,
                )

                prompt = (
                    "Dựa vào nội dung sau, gợi ý 3 câu hỏi ngắn gọn "
                    "(dưới 15 chữ) mà người dùng có thể hỏi. "
                    "Trả về đúng 3 dòng, không gạch đầu dòng:\n\n"
                    f"{chunks[0].page_content[:800]}"
                )

                if hasattr(llm, "invoke"):
                    res = llm.invoke(prompt)
                    text = res.content if hasattr(res, "content") else str(res)
                else:
                    res = llm.generate_content(prompt)
                    text = res.text

                questions = [
                    q.strip("- *1234567890. ")
                    for q in text.strip().split("\n")
                    if q.strip()
                ]

                if questions:
                    suggested_questions = questions[:3]

            except Exception:
                traceback.print_exc()

        return {
            "status": "success",
            "session_id": session_id,
            "filename": safe_filename,
            "suggested_questions": suggested_questions,
            "message": "Upload thành công!",
        }

    except Exception as e:
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        if file_path and os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception:
                pass


@router.post("/chat")
async def free_chat_with_rag(
    request: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_demo_user),
):
    try:
        user_query = request.query
        session_id = request.session_id
        context = ""

        session_record = (
            db.query(ChatSession)
            .filter(
                ChatSession.id == session_id,
                ChatSession.user_id == current_user.id,
            )
            .first()
        )

        if not session_record:
            raise HTTPException(
                status_code=403,
                detail="Không có quyền truy cập session này!",
            )

        db.add(
            ChatMessage(
                session_id=session_id,
                role="user",
                content=user_query,
            )
        )
        db.commit()

        history_records = (
            db.query(ChatMessage)
            .filter(ChatMessage.session_id == session_id)
            .order_by(ChatMessage.created_at.asc())
            .all()
        )[-6:]

        history_text = "\n".join(
            [
                f"{msg.role}: {msg.content}"
                for msg in history_records[:-1]
            ]
        )

        try:
            print(f"🔍 Đang tìm kiếm tài liệu cho Session ID: {session_id}")

            if hasattr(db_manager, "db") and db_manager.db:
                docs = db_manager.db.similarity_search(
                    user_query,
                    k=3,
                    filter={"session_id": str(session_id)},
                )

                context = "\n".join([doc.page_content for doc in docs])

                print(
                    f"✅ Đã lấy {len(docs)} đoạn tài liệu liên quan từ Vector DB."
                )
            else:
                print("⚠️ Không tìm thấy db trong VectorDBManager.")
                context = ""

        except Exception as e_db:
            print(f"❌ Lỗi Vector DB: {str(e_db)}")
            context = ""

        api_key = os.getenv("GEMINI_API_KEY")

        llm = LLMFactory.get_llm(
            provider_name="gemini",
            api_key=api_key,
        )

        prompt = f"""
Bạn là trợ lý AI chuyên nghiệp.
Hãy trả lời dựa trên tài liệu và lịch sử hội thoại.

[NGỮ CẢNH TÀI LIỆU]
{context}

[LỊCH SỬ]
{history_text}

[CÂU HỎI MỚI]
{user_query}

[TRẢ LỜI]
"""

        if hasattr(llm, "invoke"):
            ai_response = llm.invoke(prompt)
            ai_response_text = (
                ai_response.content
                if hasattr(ai_response, "content")
                else str(ai_response)
            )
        else:
            ai_response = llm.generate_content(prompt)
            ai_response_text = ai_response.text

        db.add(
            ChatMessage(
                session_id=session_id,
                role="ai",
                content=ai_response_text,
            )
        )
        db.commit()

        return {
            "status": "success",
            "ai_response": ai_response_text,
        }

    except HTTPException:
        raise

    except Exception as e:
        print("\n🚨 BACKEND CHAT ERROR 🚨")
        traceback.print_exc()
        print("🚨====================🚨\n")

        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sessions")
def get_user_sessions(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_demo_user),
):
    sessions = (
        db.query(ChatSession)
        .filter(ChatSession.user_id == current_user.id)
        .order_by(ChatSession.created_at.desc())
        .all()
    )

    return [
        {
            "id": s.id,
            "title": s.title,
        }
        for s in sessions
    ]


@router.get("/sessions/{session_id}/messages")
def get_session_messages(
    session_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_demo_user),
):
    session_record = (
        db.query(ChatSession)
        .filter(
            ChatSession.id == session_id,
            ChatSession.user_id == current_user.id,
        )
        .first()
    )

    if not session_record:
        raise HTTPException(
            status_code=403,
            detail="Không có quyền truy cập session này!",
        )

    messages = (
        db.query(ChatMessage)
        .filter(ChatMessage.session_id == session_id)
        .order_by(ChatMessage.created_at.asc())
        .all()
    )

    return [
        {
            "role": m.role,
            "content": m.content,
        }
        for m in messages
    ]