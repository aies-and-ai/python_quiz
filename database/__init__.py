# database/__init__.py
"""
データベースパッケージの初期化
主要クラスとファンクションのエクスポート
"""

from database.models import (
    Base,
    DatabaseQuestion,
    DatabaseQuizSession, 
    DatabaseQuizAnswer,
    DatabaseUserHistory,
    DatabaseStatistics
)

from database.connection import (
    DatabaseConnection,
    get_database_connection,
    get_db_session,
    initialize_database,
    reset_database_connection
)

# バージョン情報
__version__ = "1.0.0"

# パッケージメタ情報
__author__ = "Quiz App Team"
__description__ = "SQLite database integration for Quiz Application"

# エクスポートする主要な要素
__all__ = [
    # モデル
    "Base",
    "DatabaseQuestion",
    "DatabaseQuizSession", 
    "DatabaseQuizAnswer",
    "DatabaseUserHistory",
    "DatabaseStatistics",
    
    # 接続管理
    "DatabaseConnection",
    "get_database_connection",
    "get_db_session", 
    "initialize_database",
    "reset_database_connection",
    
    # 便利関数
    "setup_database",
    "get_database_status"
]


def setup_database(database_url: str = None, reset: bool = False) -> DatabaseConnection:
    """
    データベースのセットアップを行う便利関数
    
    Args:
        database_url: データベースURL（Noneの場合デフォルト）
        reset: Trueの場合、既存接続をリセットしてから初期化
    
    Returns:
        DatabaseConnection: 初期化されたデータベース接続
    
    使用例:
        from database import setup_database
        db = setup_database("sqlite:///quiz_app.db")
    """
    from logger import get_logger
    
    logger = get_logger()
    
    try:
        if reset:
            reset_database_connection()
            logger.info("Database connection reset")
        
        db_connection = initialize_database(database_url)
        logger.info("Database setup completed successfully")
        
        return db_connection
        
    except Exception as e:
        logger.error(f"Database setup failed: {e}")
        raise


def get_database_status() -> dict:
    """
    データベースの現在状態を取得
    
    Returns:
        dict: データベース状態情報
    
    使用例:
        from database import get_database_status
        status = get_database_status()
        print(f"Status: {status['connection_status']}")
    """
    try:
        # 既存接続があるかチェック
        from database.connection import _db_connection
        
        if _db_connection is None:
            return {
                "connection_status": "not_initialized",
                "message": "Database connection not initialized"
            }
        
        # ヘルスチェック実行
        health = _db_connection.health_check()
        db_info = _db_connection.get_database_info()
        
        return {
            "connection_status": "initialized",
            "health": health,
            "info": db_info,
            "database_url": _db_connection.database_url
        }
        
    except Exception as e:
        return {
            "connection_status": "error",
            "error": str(e)
        }


# パッケージレベルでの初期化ログ
def _log_package_info():
    """パッケージ読み込み時の情報ログ"""
    try:
        from logger import get_logger
        logger = get_logger()
        logger.debug(f"Database package loaded - version {__version__}")
    except:
        # loggerが利用できない場合は無視
        pass

# パッケージ読み込み時に実行
_log_package_info()