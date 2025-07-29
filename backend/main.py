# backend/main.py
"""
FastAPI メインアプリケーション
ローカル検証用のシンプルなクイズWebアプリ
"""

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from contextlib import asynccontextmanager
import uvicorn
import os
from pathlib import Path

from app.config import get_settings
from app.core.service_factory import initialize_services, shutdown_services
from app.api.quiz import router as quiz_router
from app.api.health import router as health_router
from utils.logger import get_logger, setup_fastapi_logging


@asynccontextmanager
async def lifespan(app: FastAPI):
    """アプリケーションライフサイクル管理"""
    logger = get_logger()
    settings = get_settings()
    
    try:
        # 起動時処理
        logger.info("FastAPI アプリケーション起動中...")
        
        # サービス初期化
        initialize_services(settings.database_url)
        logger.info("サービス初期化完了")
        
        # FastAPIログ設定
        setup_fastapi_logging()
        
        yield
        
    except Exception as e:
        logger.error(f"アプリケーション起動エラー: {e}")
        raise
    finally:
        # 終了時処理
        logger.info("FastAPI アプリケーション終了中...")
        shutdown_services()
        logger.info("サービス終了完了")


def create_app() -> FastAPI:
    """FastAPIアプリケーションを作成"""
    settings = get_settings()
    
    app = FastAPI(
        title="クイズアプリケーション",
        description="ローカル検証用のシンプルなクイズWebアプリ",
        version="1.0.0",
        lifespan=lifespan,
        # 本番環境では無効化
        docs_url="/docs" if settings.api_debug else None,
        redoc_url="/redoc" if settings.api_debug else None
    )
    
    # CORS設定（開発用）
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.api_cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE"],
        allow_headers=["*"],
    )
    
    # APIルーター
    app.include_router(health_router, prefix="/api/v1", tags=["health"])
    app.include_router(quiz_router, prefix="/api/v1", tags=["quiz"])
    
    # 静的ファイル配信（React build）
    frontend_build_path = Path("frontend/build")
    if frontend_build_path.exists():
        app.mount("/static", StaticFiles(directory=str(frontend_build_path / "static")), name="static")
        
        @app.get("/{full_path:path}")
        async def serve_react_app(full_path: str):
            """React アプリケーションの配信（SPA対応）"""
            # API パスは除外
            if full_path.startswith("api/"):
                raise HTTPException(status_code=404, detail="Not found")
            
            # ファイルが存在する場合はそのまま配信
            file_path = frontend_build_path / full_path
            if file_path.is_file():
                return FileResponse(file_path)
            
            # それ以外はindex.htmlを配信（SPA ルーティング対応）
            index_path = frontend_build_path / "index.html"
            if index_path.exists():
                return FileResponse(index_path)
            
            raise HTTPException(status_code=404, detail="Frontend not found")
    
    return app


# アプリケーションインスタンス
app = create_app()


def main():
    """開発サーバー起動"""
    settings = get_settings()
    
    print(f"""
🚀 クイズアプリケーション起動中...

📊 設定情報:
   - API: http://{settings.api_host}:{settings.api_port}
   - データベース: {settings.database_url}
   - デバッグモード: {settings.api_debug}
   - ログレベル: {settings.log_level}

📋 管理機能:
   - 問題管理: python admin.py
   - API文書: http://{settings.api_host}:{settings.api_port}/docs

🌐 アクセス:
   - ブラウザで http://localhost:{settings.api_port} を開いてください
    """)
    
    # 開発サーバー起動
    uvicorn.run(
        "main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.api_reload,
        log_level=settings.log_level.lower(),
        # アクセスログを簡素化
        access_log=settings.api_debug
    )


if __name__ == "__main__":
    main()