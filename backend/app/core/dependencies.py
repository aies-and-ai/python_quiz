# app/core/dependencies.py
"""
依存性注入設定
FastAPI用の依存性注入とサービス提供
"""

from typing import Annotated
from fastapi import Depends
from app.core.interfaces import (
    QuizServiceInterface,
    CSVImportServiceInterface,
    DatabaseServiceInterface
)
from app.core.service_factory import get_service_factory


def get_quiz_service() -> QuizServiceInterface:
    """クイズサービスを取得"""
    factory = get_service_factory()
    return factory.get_quiz_service()


def get_csv_import_service() -> CSVImportServiceInterface:
    """CSVインポートサービスを取得"""
    factory = get_service_factory()
    return factory.get_csv_importer()


def get_database_service() -> DatabaseServiceInterface:
    """データベースサービスを取得"""
    factory = get_service_factory()
    return factory.get_database_service()


# FastAPI依存性注入用のタイプエイリアス
QuizServiceDep = Annotated[QuizServiceInterface, Depends(get_quiz_service)]
CSVImportServiceDep = Annotated[CSVImportServiceInterface, Depends(get_csv_import_service)]
DatabaseServiceDep = Annotated[DatabaseServiceInterface, Depends(get_database_service)]


class DependencyManager:
    """依存性管理クラス（シングルトン）"""
    
    _instance = None
    _initialized = False
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if not self._initialized:
            self._quiz_service = None
            self._csv_import_service = None
            self._database_service = None
            self._initialized = True
    
    def set_quiz_service(self, service: QuizServiceInterface):
        """クイズサービスを設定（テスト用）"""
        self._quiz_service = service
    
    def set_csv_import_service(self, service: CSVImportServiceInterface):
        """CSVインポートサービスを設定（テスト用）"""
        self._csv_import_service = service
    
    def set_database_service(self, service: DatabaseServiceInterface):
        """データベースサービスを設定（テスト用）"""
        self._database_service = service
    
    def get_quiz_service(self) -> QuizServiceInterface:
        """クイズサービスを取得"""
        if self._quiz_service:
            return self._quiz_service
        return get_quiz_service()
    
    def get_csv_import_service(self) -> CSVImportServiceInterface:
        """CSVインポートサービスを取得"""
        if self._csv_import_service:
            return self._csv_import_service
        return get_csv_import_service()
    
    def get_database_service(self) -> DatabaseServiceInterface:
        """データベースサービスを取得"""
        if self._database_service:
            return self._database_service
        return get_database_service()
    
    def reset(self):
        """依存性をリセット（テスト用）"""
        self._quiz_service = None
        self._csv_import_service = None
        self._database_service = None


# グローバル依存性マネージャー
_dependency_manager = DependencyManager()


def get_dependency_manager() -> DependencyManager:
    """依存性マネージャーを取得"""
    return _dependency_manager


def reset_dependencies():
    """依存性をリセット（テスト用）"""
    _dependency_manager.reset()


# FastAPI用のライフサイクル管理
async def initialize_dependencies():
    """依存性を初期化（FastAPI起動時）"""
    try:
        from app.core.service_factory import initialize_services
        initialize_services()
    except Exception as e:
        raise RuntimeError(f"Failed to initialize dependencies: {e}")


async def shutdown_dependencies():
    """依存性をシャットダウン（FastAPI終了時）"""
    try:
        from app.core.service_factory import shutdown_services
        shutdown_services()
        reset_dependencies()
    except Exception as e:
        # ログエラーは出力するが、シャットダウンは継続
        print(f"Warning: Failed to shutdown dependencies: {e}")


# Web API用の検証関数
def validate_dependencies() -> dict:
    """依存性の状態を検証"""
    try:
        quiz_service = get_quiz_service()
        csv_service = get_csv_import_service()
        db_service = get_database_service()
        
        return {
            "status": "healthy",
            "services": {
                "quiz_service": quiz_service is not None,
                "csv_import_service": csv_service is not None,
                "database_service": db_service is not None
            }
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "services": {
                "quiz_service": False,
                "csv_import_service": False,
                "database_service": False
            }
        }