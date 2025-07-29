# backend/app/api/health.py
"""
ヘルスチェックAPI
システム状態とデータベース接続を確認
"""

from fastapi import APIRouter, Depends
from typing import Dict, Any

from app.models.common import HealthResponse, SuccessResponse
from app.core.dependencies import DatabaseServiceDep, QuizServiceDep
from app.core.service_factory import get_services_status, health_check_all_services
from app.config import get_settings
from utils.logger import get_logger

router = APIRouter()
logger = get_logger()


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """基本ヘルスチェック"""
    try:
        settings = get_settings()
        
        return HealthResponse(
            status="healthy",
            version="1.0.0",
            database_status="unknown",  # 詳細は /health/detailed で確認
            timestamp=None  # 自動設定
        )
        
    except Exception as e:
        logger.error(f"ヘルスチェックエラー: {e}")
        return HealthResponse(
            status="unhealthy",
            version="1.0.0",
            database_status="error"
        )


@router.get("/health/detailed", response_model=SuccessResponse[Dict[str, Any]])
async def detailed_health_check(
    db_service: DatabaseServiceDep,
    quiz_service: QuizServiceDep
):
    """詳細ヘルスチェック"""
    try:
        # 設定情報
        settings = get_settings()
        
        # サービス状態
        services_status = get_services_status()
        
        # 全サービスヘルスチェック
        health_status = health_check_all_services()
        
        # データベース詳細情報
        db_health = db_service.health_check()
        db_info = db_service.get_database_info()
        
        # 問題数確認
        question_count = quiz_service.get_question_count()
        categories = quiz_service.get_available_categories()
        difficulties = quiz_service.get_available_difficulties()
        
        # 統計情報
        try:
            stats = quiz_service.get_statistics()
            statistics = {
                "total_sessions": stats.total_sessions,
                "total_questions_answered": stats.total_questions_answered,
                "overall_accuracy": stats.overall_accuracy
            }
        except Exception:
            statistics = {"error": "統計情報取得失敗"}
        
        health_data = {
            "system": {
                "status": "healthy" if health_status.get('status') == 'healthy' else "degraded",
                "version": "1.0.0",
                "environment": "development" if settings.api_debug else "production",
                "api_url": settings.get_api_url()
            },
            "services": {
                "status": services_status,
                "health": health_status
            },
            "database": {
                "health": db_health,
                "info": db_info,
                "connection_url": settings.database_url
            },
            "content": {
                "question_count": question_count,
                "categories": categories,
                "difficulties": difficulties,
                "statistics": statistics
            },
            "configuration": {
                "log_level": settings.log_level,
                "debug_mode": settings.api_debug,
                "cors_origins": settings.api_cors_origins
            }
        }
        
        # 全体ステータス判定
        overall_status = "healthy"
        if health_status.get('status') != 'healthy':
            overall_status = "unhealthy"
        elif question_count == 0:
            overall_status = "degraded"
        elif db_health.get('status') != 'healthy':
            overall_status = "degraded"
        
        message = {
            "healthy": "すべてのシステムが正常に動作しています",
            "degraded": "一部のシステムに問題がありますが、基本機能は利用可能です",
            "unhealthy": "システムに重大な問題があります"
        }.get(overall_status, "状態不明")
        
        return SuccessResponse(
            data=health_data,
            message=message
        )
        
    except Exception as e:
        logger.error(f"詳細ヘルスチェックエラー: {e}")
        
        error_data = {
            "system": {"status": "error", "error": str(e)},
            "services": {"status": "unknown"},
            "database": {"status": "unknown"},
            "content": {"status": "unknown"}
        }
        
        return SuccessResponse(
            data=error_data,
            message="ヘルスチェック実行中にエラーが発生しました"
        )


@router.get("/health/database")
async def database_health_check(db_service: DatabaseServiceDep):
    """データベース専用ヘルスチェック"""
    try:
        health = db_service.health_check()
        info = db_service.get_database_info()
        
        return {
            "status": health.get("status", "unknown"),
            "health": health,
            "info": info,
            "message": "データベース接続正常" if health.get("status") == "healthy" else "データベース接続に問題があります"
        }
        
    except Exception as e:
        logger.error(f"データベースヘルスチェックエラー: {e}")
        return {
            "status": "error",
            "error": str(e),
            "message": "データベースヘルスチェック失敗"
        }


@router.get("/health/services")
async def services_health_check():
    """サービス状態チェック"""
    try:
        services_status = get_services_status()
        health_status = health_check_all_services()
        
        return {
            "services_status": services_status,
            "health_status": health_status,
            "message": "サービス状態を取得しました"
        }
        
    except Exception as e:
        logger.error(f"サービスヘルスチェックエラー: {e}")
        return {
            "status": "error",
            "error": str(e),
            "message": "サービス状態取得失敗"
        }


@router.get("/health/ready")
async def readiness_check(quiz_service: QuizServiceDep):
    """レディネスチェック（アプリケーション利用可能性）"""
    try:
        # 基本的なサービス確認
        question_count = quiz_service.get_question_count()
        
        if question_count == 0:
            return {
                "ready": False,
                "reason": "問題データが登録されていません",
                "suggestion": "admin.py を使用してCSVファイルをインポートしてください",
                "question_count": 0
            }
        
        # カテゴリと難易度の確認
        categories = quiz_service.get_available_categories()
        difficulties = quiz_service.get_available_difficulties()
        
        return {
            "ready": True,
            "message": "アプリケーションは利用可能です",
            "question_count": question_count,
            "categories_count": len(categories),
            "difficulties_count": len(difficulties)
        }
        
    except Exception as e:
        logger.error(f"レディネスチェックエラー: {e}")
        return {
            "ready": False,
            "reason": f"システムエラー: {str(e)}",
            "suggestion": "システム管理者に連絡してください"
        }


@router.get("/version")
async def get_version():
    """バージョン情報取得"""
    settings = get_settings()
    
    return {
        "version": "1.0.0",
        "api_version": "v1",
        "environment": "development" if settings.api_debug else "production",
        "debug_mode": settings.api_debug,
        "build_info": {
            "python_version": "3.11+",
            "framework": "FastAPI",
            "database": "SQLite",
            "features": ["quiz", "statistics", "csv_import"]
        }
    }