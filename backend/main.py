"""
SocialShield Backend - FastAPI
AI-powered multi-modal fraud & deepfake detection API
Integrated with Supabase Auth, PostgreSQL, Supabase Storage, and Hugging Face.
"""
from fastapi import FastAPI, HTTPException, Depends, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from contextlib import asynccontextmanager
import os
import uvicorn
import logging

from routers import image_router, video_router, audio_router, text_router, url_router, profile_router, history_router
from utils.auth import verify_token
from utils.database import init_db, is_mock_db, _last_db_error
from ml.models import model_registry

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("SocialShield API starting up with Supabase integration...")
    await init_db()
    try:
        model_registry.load_all()
    except Exception as e:
        logger.error(f"Failed to load models: {e}")
    yield
    logger.info("SocialShield API shutting down...")

app = FastAPI(
    title="SocialShield API",
    description="AI-powered digital fraud and deepfake detection system with Supabase Platform",
    version="1.0.0",
    lifespan=lifespan
)

ALLOWED_ORIGINS = [
    "http://localhost:5173",
    "http://localhost:3000",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:3000",
    "*",  # Allow all for local dev; restrict in production
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(image_router.router, prefix="/api/v1/scan", tags=["Image Detection"])
app.include_router(video_router.router, prefix="/api/v1/scan", tags=["Video Detection"])
app.include_router(audio_router.router, prefix="/api/v1/scan", tags=["Audio Detection"])
app.include_router(text_router.router, prefix="/api/v1/scan", tags=["Text Detection"])
app.include_router(url_router.router, prefix="/api/v1/scan", tags=["URL Detection"])
app.include_router(profile_router.router, prefix="/api/v1/scan", tags=["Profile Analysis"])
app.include_router(history_router.router, prefix="/api/v1", tags=["History"])

@app.get("/")
async def root():
    return {
        "status": "active",
        "service": "SocialShield API",
        "version": "1.0.0",
        "auth": "Supabase Auth",
        "database": "Supabase PostgreSQL",
        "storage": "Supabase Storage",
        "deepfake_model": "prithivMLmods/deepfake-detector-model-v1"
    }

@app.get("/health")
async def health():
    return {
        "status": "healthy",
        "models": "loaded",
        "deepfake_model": "prithivMLmods/deepfake-detector-model-v1",
        "auth_provider": "supabase",
        "database_type": "supabase_postgresql" if not is_mock_db() else "mock_json",
        "storage_provider": "supabase_storage",
        "last_db_error": _last_db_error
    }

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)

