from fastapi import APIRouter, HTTPException

from pydantic import BaseModel

from services.rag_engine import RAGEngine



router = APIRouter()

rag_engine = RAGEngine()



# Định nghĩa cấu trúc cục dữ liệu JSON mà Camera sẽ gửi lên

class GestureRequest(BaseModel):

    gesture_id: int  # Ví dụ: 1, 2, hoặc 5



@router.get("/quiz")

async def create_quiz():

    """API gọi LLM sinh câu hỏi trắc nghiệm dựa trên file đã upload"""

    try:

        quiz_content = rag_engine.generate_quiz()

        return {

            "status": "success", 

            "quiz": quiz_content

        }

    except Exception as e:

        raise HTTPException(status_code=500, detail=str(e))



@router.post("/action")

async def handle_gesture(request: GestureRequest):

    """API nhận số ngón tay từ Camera và trả về câu trả lời RAG"""

    try:

        result = rag_engine.execute_gesture_command(request.gesture_id)

        return {

            "status": "success", 

            "gesture_received": request.gesture_id, 

            "ai_response": result

        }

    except Exception as e:

        raise HTTPException(status_code=500, detail=str(e))