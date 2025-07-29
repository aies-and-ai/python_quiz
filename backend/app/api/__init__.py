# backend/app/api/__init__.py
"""
API層の初期化
FastAPI用エンドポイントの管理
"""

from fastapi import APIRouter
from .quiz import router as quiz_router
from .health import router as health_router

# APIルーターの統合
api_router = APIRouter(prefix="/api/v1")

# 各エンドポイントを登録
api_router.include_router(health_router, tags=["health"])
api_router.include_router(quiz_router, tags=["quiz"])

# エクスポート
__all__ = [
    "api_router",
    "quiz_router", 
    "health_router"
]