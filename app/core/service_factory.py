# app/core/service_factory.py
"""
サービスファクトリー - 責任明確化版
依存性注入とインターフェースベースの設計
"""

import sys
import os
from typing import Optional
from pathlib import Path

project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from app.core.interfaces import (
    QuizServiceInterface,
    CSVImportServiceInterface,
    QuestionRepositoryInterface,
    SessionRepositoryInterface,
    DatabaseServiceInterface
)
from app.core.database import DatabaseService
from app.core.quiz import QuizService
from app.core.csv_import import CSVImportService


class ServiceFactory:
    """サービスファクトリー - 依存性注入パターン"""
    
    _instance: Optional['ServiceFactory'] = None
    
    def __new__(cls) -> 'ServiceFactory':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        if hasattr(self, '_initialized') and self._initialized:
            return
            
        try:
            from utils.logger import get_logger
            self.logger = get_logger()
        except ImportError:
            import logging
            self.logger = logging.getLogger(__name__)
        
        # サービスインスタンス
        self._database_service: Optional[DatabaseServiceInterface] = None
        self._quiz_service: Optional[QuizServiceInterface] = None
        self._csv_import_service: Optional[CSVImportServiceInterface] = None
        
        # 初期化フラグ
        self._initialized = False
    
    def initialize(self, database_url: Optional[str] = None) -> None:
        """サービスを初期化 - 依存性注入で構築"""
        if self._initialized:
            return
        
        try:
            # 設定取得
            try:
                from app.config import get_settings
                settings = get_settings()
                db_url = database_url or settings.database_url
            except ImportError:
                db_url = database_url or "sqlite:///quiz.db"
                self.logger.warning("設定ファイルが見つかりません。デフォルト設定を使用します。")
            
            # データベースサービス（基盤レイヤー）
            self._database_service = DatabaseService(db_url)
            
            # リポジトリレイヤー（データベースサービスがリポジトリインターフェースも実装）
            question_repository = self._database_service  # DatabaseServiceがQuestionRepositoryInterfaceを実装
            session_repository = self._database_service   # DatabaseServiceがSessionRepositoryInterfaceを実装
            
            # アプリケーションサービスレイヤー（依存性注入）
            self._quiz_service = QuizService(question_repository, session_repository)
            self._csv_import_service = CSVImportService(question_repository)
            
            self._initialized = True
            self.logger.info("サービスファクトリー初期化完了（依存性注入パターン）")
            
        except Exception as e:
            self.logger.error(f"サービスファクトリー初期化エラー: {e}")
            raise RuntimeError(f"サービスの初期化に失敗しました: {str(e)}")
    
    def get_database_service(self) -> DatabaseServiceInterface:
        """データベースサービスを取得"""
        if not self._initialized:
            self.initialize()
        return self._database_service
    
    def get_quiz_service(self) -> QuizServiceInterface:
        """クイズサービスを取得"""
        if not self._initialized:
            self.initialize()
        return self._quiz_service
    
    def get_csv_importer(self) -> CSVImportServiceInterface:
        """CSVインポートサービスを取得"""
        if not self._initialized:
            self.initialize()
        return self._csv_import_service
    
    def get_question_repository(self) -> QuestionRepositoryInterface:
        """問題リポジトリを取得"""
        if not self._initialized:
            self.initialize()
        return self._database_service  # DatabaseServiceがQuestionRepositoryInterfaceを実装
    
    def get_session_repository(self) -> SessionRepositoryInterface:
        """セッションリポジトリを取得"""
        if not self._initialized:
            self.initialize()
        return self._database_service  # DatabaseServiceがSessionRepositoryInterfaceを実装
    
    def shutdown(self) -> None:
        """リソースのクリーンアップ"""
        try:
            # アクティブセッションのクリーンアップ
            if self._quiz_service and hasattr(self._quiz_service, '_active_sessions'):
                for session_id in list(self._quiz_service._active_sessions.keys()):
                    try:
                        self._quiz_service.abandon_session(session_id)
                    except Exception as e:
                        self.logger.warning(f"セッション終了処理エラー: {e}")
            
            # データベース接続のクリーンアップ
            if self._database_service and hasattr(self._database_service, 'close'):
                try:
                    self._database_service.close()
                except Exception as e:
                    self.logger.warning(f"データベース終了処理エラー: {e}")
            
            self.logger.info("サービスファクトリーシャットダウン完了")
            
        except Exception as e:
            self.logger.warning(f"シャットダウン処理で例外: {e}")
    
    def is_initialized(self) -> bool:
        """初期化済みかどうかを確認"""
        return self._initialized
    
    def reset(self) -> None:
        """ファクトリーをリセット（テスト用）"""
        self.shutdown()
        self._database_service = None
        self._quiz_service = None
        self._csv_import_service = None
        self._initialized = False
    
    def get_services_status(self) -> dict:
        """サービスの状態を取得"""
        return {
            'initialized': self._initialized,
            'services': {
                'database_service': self._database_service is not None,
                'quiz_service': self._quiz_service is not None,
                'csv_import_service': self._csv_import_service is not None
            },
            'service_types': {
                'database_service': type(self._database_service).__name__ if self._database_service else None,
                'quiz_service': type(self._quiz_service).__name__ if self._quiz_service else None,
                'csv_import_service': type(self._csv_import_service).__name__ if self._csv_import_service else None
            }
        }
    
    def health_check(self) -> dict:
        """全サービスのヘルスチェック"""
        if not self._initialized:
            return {
                'status': 'not_initialized',
                'message': 'Services not initialized'
            }
        
        try:
            # データベースヘルスチェック
            db_health = self._database_service.health_check() if self._database_service else {'status': 'unavailable'}
            
            # 問題数チェック
            question_count = 0
            if self._quiz_service:
                try:
                    question_count = self._quiz_service.get_question_count()
                except:
                    question_count = 0
            
            return {
                'status': 'healthy' if db_health.get('status') == 'healthy' else 'unhealthy',
                'database': db_health,
                'question_count': question_count,
                'services_available': {
                    'quiz_service': self._quiz_service is not None,
                    'csv_import_service': self._csv_import_service is not None,
                    'database_service': self._database_service is not None
                }
            }
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e)
            }


# グローバルファクトリーインスタンス
_factory: Optional[ServiceFactory] = None


def get_service_factory() -> ServiceFactory:
    """グローバルサービスファクトリーを取得"""
    global _factory
    if _factory is None:
        _factory = ServiceFactory()
    return _factory


def get_quiz_service() -> QuizServiceInterface:
    """クイズサービスを取得"""
    return get_service_factory().get_quiz_service()


def get_database_service() -> DatabaseServiceInterface:
    """データベースサービスを取得"""
    return get_service_factory().get_database_service()


def get_csv_importer() -> CSVImportServiceInterface:
    """CSVインポートサービスを取得"""
    return get_service_factory().get_csv_importer()


def get_question_repository() -> QuestionRepositoryInterface:
    """問題リポジトリを取得"""
    return get_service_factory().get_question_repository()


def get_session_repository() -> SessionRepositoryInterface:
    """セッションリポジトリを取得"""
    return get_service_factory().get_session_repository()


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
    """サービスをリセット（テスト用）"""
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
    
    status = _factory.get_services_status()
    status['factory_exists'] = True
    
    return status


def health_check_all_services() -> dict:
    """全サービスのヘルスチェック"""
    global _factory
    
    if _factory is None:
        return {
            'status': 'factory_not_created',
            'message': 'Service factory not created'
        }
    
    return _factory.health_check()


# 依存性注入用のヘルパー関数
def create_quiz_service_with_dependencies(
    question_repository: QuestionRepositoryInterface,
    session_repository: SessionRepositoryInterface
) -> QuizServiceInterface:
    """依存性注入でクイズサービスを作成（テスト用）"""
    return QuizService(question_repository, session_repository)


def create_csv_import_service_with_dependencies(
    question_repository: QuestionRepositoryInterface
) -> CSVImportServiceInterface:
    """依存性注入でCSVインポートサービスを作成（テスト用）"""
    return CSVImportService(question_repository)