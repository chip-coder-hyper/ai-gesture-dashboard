import os

import google.generativeai as genai
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.auth_api import router as auth_router
from api.document_api import router as document_router
from api.gesture_api import router as gesture_router
from core.config import settings
from database.db_config import init_db
from services.llm_factory import LLMFactory


app = FastAPI(
    title="AI Gesture QA API",
    description="Hệ thống Backend RAG điều khiển bằng cử chỉ tay.",
    version="1.0.0",
)

init_db()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(
    auth_router,
    prefix="/api/v1/auth",
    tags=["Authentication"],
)

app.include_router(
    document_router,
    prefix="/api/v1/documents",
    tags=["Document Processing"],
)

app.include_router(
    gesture_router,
    prefix="/api/v1/gestures",
    tags=["Gesture Action & Quiz"],
)


@app.get("/", tags=["System Health"])
async def health_check():
    return {
        "status": "success",
        "message": "Backend đang hoạt động!",
    }


@app.get("/health", tags=["System Health"])
async def health():
    return {
        "status": "ok",
    }


@app.get("/api/v1/health", tags=["System Health"])
async def api_health():
    return {
        "status": "ok",
        "api_version": "v1",
    }


@app.get("/test-ai", tags=["AI Core Testing"])
async def test_ai():
    try:
        api_key = settings.GEMINI_API_KEY

        llm = LLMFactory.get_llm(
            provider_name="gemini",
            api_key=api_key,
        )

        response = llm.invoke("Hãy nói 'Xin chào' bằng tiếng Việt.")

        return {
            "status": "success",
            "ai_response": response.content,
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
        }


@app.get("/list-models", tags=["AI Core Infrastructure"])
async def list_models():
    try:
        genai.configure(api_key=settings.GEMINI_API_KEY)

        models = [
            m.name
            for m in genai.list_models()
            if "generateContent" in m.supported_generation_methods
        ]

        return {
            "status": "success",
            "available_models": models,
        }

    except Exception as e:
        return {
            "status": "error",
            "message": str(e),
        }


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", "8080"))

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=False,
    )