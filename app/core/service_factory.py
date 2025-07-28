# app/core/service_factory.py
"""
サービスファクトリー
依存性注入とサービスインスタンス管理
"""

import sys
import os
from typing import Optional
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from app.core.database import DatabaseService
from app.core.quiz import QuizService  
from app.core.csv_import import CSVImporter


class ServiceFactory:
    """サービスファクトリー - シングルトンパターン"""
    
    _instance: Optional['ServiceFactory'] = None
    _db_service: Optional[DatabaseService] = None
    _quiz_service: Optional[QuizService] = None
    _csv_importer: Optional[CSVImporter] = None
    
    def __new__(cls) -> 'ServiceFactory':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        try:
            from utils.logger import get_logger
            self.logger = get_logger()
        except ImportError:
            import logging
            self.logger = logging.getLogger(__name__)
        
        self._initialized = False
    
    def initialize(self, database_url: Optional[str] = None) -> None:
        """サービスを初期化"""
        if self._initialized:
            return
        
        try:
            try:
                from app.config import get_settings
                settings = get_settings()
                db_url = database_url or settings.database_url
            except ImportError:
                db_url = database_url or "sqlite:///quiz.db"
                self.logger.warning("設定ファイルが見つかりません。デフォルト設定を使用します。")
            
            self._db_service = DatabaseService(db_url)
            self._quiz_service = QuizService(self._db_service)
            self._csv_importer = CSVImporter(self._db_service)
            
            self._initialized = True
            self.logger.info("サービスファクトリー初期化完了")
            
        except Exception as e:
            self.logger.error(f"サービスファクトリー初期化エラー: {e}")
            raise RuntimeError(f"サービスの初期化に失敗しました: {str(e)}")
    
    def get_database_service(self) -> DatabaseService:
        """データベースサービスを取得"""
        if not self._initialized:
            self.initialize()
        return self._db_service
    
    def get_quiz_service(self) -> QuizService:
        """クイズサービスを取得"""
        if not self._initialized:
            self.initialize()
        return self._quiz_service
    
    def get_csv_importer(self) -> CSVImporter:
        """CSVインポーターを取得"""
        if not self._initialized:
            self.initialize()
        return self._csv_importer
    
    def shutdown(self) -> None:
        """リソースのクリーンアップ"""
        if self._quiz_service:
            try:
                if hasattr(self._quiz_service, '_active_sessions'):
                    for session_id in list(self._quiz_service._active_sessions.keys()):
                        try:
                            self._quiz_service.abandon_session(session_id)
                        except Exception as e:
                            self.logger.warning(f"セッション終了処理エラー: {e}")
            except Exception as e:
                self.logger.warning(f"セッション終了処理で例外: {e}")
        
        self.logger.info("サービスファクトリーシャットダウン完了")
    
    def is_initialized(self) -> bool:
        """初期化済みかどうかを確認"""
        return self._initialized
    
    def reset(self) -> None:
        """ファクトリーをリセット"""
        self.shutdown()
        self._db_service = None
        self._quiz_service = None
        self._csv_importer = None
        self._initialized = False


# グローバルファクトリーインスタンス
_factory: Optional[ServiceFactory] = None


def get_service_factory() -> ServiceFactory:
    """グローバルサービスファクトリーを取得"""
    global _factory
    if _factory is None:
        _factory = ServiceFactory()
    return _factory


def get_quiz_service() -> QuizService:
    """クイズサービスを取得"""
    return get_service_factory().get_quiz_service()


def get_database_service() -> DatabaseService:
    """データベースサービスを取得"""
    return get_service_factory().get_database_service()


def get_csv_importer() -> CSVImporter:
    """CSVインポーターを取得"""
    return get_service_factory().get_csv_importer()


def initialize_services(database_url: Optional[str] = None) -> None:
    """サービスを初期化"""
    get_service_factory().initialize(database_url)


def shutdown_services() -> None:
    """サービスをシャットダウン"""
    global _factory
    if _factory:
        _factory.shutdown()
        _factory = None


def reset_services() -> None:
    """サービスをリセット"""
    global _factory
    if _factory:
        _factory.reset()
    _factory = None


def is_services_initialized() -> bool:
    """サービスが初期化済みかどうかを確認"""
    global _factory
    return _factory is not None and _factory.is_initialized()


def get_services_status() -> dict:
    """サービスの状態を取得"""
    global _factory
    
    if _factory is None:
        return {
            'factory_exists': False,
            'initialized': False,
            'services': {}
        }
    
    return {
        'factory_exists': True,
        'initialized': _factory.is_initialized(),
        'services': {
            'database_service': _factory._db_service is not None,
            'quiz_service': _factory._quiz_service is not None,
            'csv_importer': _factory._csv_importer is not None
        }
    }