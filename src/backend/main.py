import google.generativeai as genai
from database.db_config import init_db
from api.auth_api import router as auth_router
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from core.config import settings
from services.llm_factory import LLMFactory

# --- IMPORT CÁC NHÁNH API ---
from api.document_api import router as document_router
from api.gesture_api import router as gesture_router  # Đã cắm dây Gesture API

app = FastAPI(
    title="AI Gesture QA API",
    description="Hệ thống Backend RAG điều khiển bằng cử chỉ tay.",
    version="1.0.0"
)
init_db()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],  
    allow_headers=["*"],  
)

# --- ĐĂNG KÝ CÁC CỔNG API LÊN SWAGGER UI ---
app.include_router(
    document_router, 
    prefix="/api/v1/documents", 
    tags=["Document Processing"]
)

# Đăng ký cổng Gesture xuất hiện trên web
app.include_router(
    gesture_router, 
    prefix="/api/v1/gestures", 
    tags=["Gesture Action & Quiz"]
)
app.include_router(auth_router,
                    prefix="/api/v1/auth",
                    tags=["Authentication"]
)

# --- CÁC API KIỂM TRA HỆ THỐNG ---
@app.get("/", tags=["System Health"])
async def health_check():
    return {"status": "success", "message": "Backend đang hoạt động!"}

@app.get("/test-ai", tags=["AI Core Testing"])
async def test_ai():
    try:
        api_key = settings.GEMINI_API_KEY
        llm = LLMFactory.get_llm(provider_name="gemini", api_key=api_key)
        response = llm.invoke("Hãy nói 'Xin chào' bằng tiếng Việt.")
        return {"status": "success", "ai_response": response.content}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.get("/list-models", tags=["AI Core Infrastructure"])
async def list_models():
    try:
        genai.configure(api_key=settings.GEMINI_API_KEY)
        models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_generation_methods]
        return {"status": "success", "available_models": models}
    except Exception as e:
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    import uvicorn
    # Tắt reload=False để tránh lỗi tràn RAM ảo (Page file 1455) của Windows khi load mô hình AI
    uvicorn.run("main:app", host="127.0.0.1", port=8080, reload=False)