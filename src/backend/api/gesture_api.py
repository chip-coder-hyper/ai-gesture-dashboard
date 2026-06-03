from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.rag_engine import RAGEngine


router = APIRouter()
rag_engine = RAGEngine()


class GestureRequest(BaseModel):
    gesture_id: int


@router.get("/quiz")
async def create_quiz():
    try:
        quiz_content = rag_engine.generate_quiz()

        return {
            "status": "success",
            "quiz": quiz_content,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/action")
async def handle_gesture(request: GestureRequest):
    try:
        result = rag_engine.execute_gesture_command(request.gesture_id)

        return {
            "status": "success",
            "gesture_received": request.gesture_id,
            "ai_response": result,
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))