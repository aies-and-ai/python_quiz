# database/connection.py
"""
SQLite データベース接続管理
セッション管理、初期化、ヘルスチェック機能
"""

import os
from pathlib import Path
from typing import Optional, Generator
from contextlib import contextmanager
from sqlalchemy import create_engine, event, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import OperationalError, IntegrityError
from logger import get_logger
from enhanced_exceptions import ConfigurationError


class DatabaseConnection:
    """SQLiteデータベース接続管理クラス"""
    
    def __init__(self, database_url: Optional[str] = None, database_path: Optional[str] = None):
        """
        初期化
        
        Args:
            database_url: SQLAlchemy用データベースURL
            database_path: SQLiteファイルパス（database_urlの代替）
        """
        self.logger = get_logger()
        
        # データベースURLの決定
        if database_url:
            self.database_url = database_url
        elif database_path:
            # パスからURLを構築
            path = Path(database_path).resolve()
            self.database_url = f"sqlite:///{path}"
        else:
            # デフォルトパス
            default_path = Path("quiz_app.db").resolve()
            self.database_url = f"sqlite:///{default_path}"
        
        self.logger.info(f"Database URL: {self.database_url}")
        
        # エンジンとセッションファクトリの初期化
        self.engine: Optional[Engine] = None
        self.SessionLocal: Optional[sessionmaker] = None
        
        # 接続状態
        self._is_initialized = False
        
    def initialize(self) -> None:
        """データベース接続を初期化"""
        try:
            # SQLiteファイルのディレクトリを作成
            self._ensure_database_directory()
            
            # エンジン作成
            self.engine = create_engine(
                self.database_url,
                # SQLite最適化設定
                connect_args={
                    "check_same_thread": False,  # マルチスレッド対応
                    "timeout": 30,  # 30秒でタイムアウト
                },
                # 接続プール設定
                pool_pre_ping=True,  # 接続確認
                pool_recycle=3600,   # 1時間で接続リサイクル
                echo=False  # SQLログ出力（デバッグ時はTrue）
            )
            
            # SQLite固有の設定を適用
            self._configure_sqlite_engine()
            
            # セッションファクトリ作成
            self.SessionLocal = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine
            )
            
            # データベーステーブル作成
            self._create_tables()
            
            # 接続テスト
            self._test_connection()
            
            self._is_initialized = True
            self.logger.info("Database connection initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize database: {e}")
            raise ConfigurationError(
                message=f"Database initialization failed: {str(e)}",
                original_error=e,
                user_message="データベースの初期化に失敗しました。ファイルの権限を確認してください。"
            )
    
    def _ensure_database_directory(self) -> None:
        """データベースファイルのディレクトリを確保"""
        if self.database_url.startswith("sqlite:///"):
            db_path = self.database_url.replace("sqlite:///", "")
            db_dir = Path(db_path).parent
            
            if not db_dir.exists():
                db_dir.mkdir(parents=True, exist_ok=True)
                self.logger.info(f"Created database directory: {db_dir}")
    
    def _configure_sqlite_engine(self) -> None:
        """SQLite固有の設定を適用"""
        @event.listens_for(self.engine, "connect")
        def set_sqlite_pragma(dbapi_connection, connection_record):
            """SQLite接続時の最適化設定"""
            cursor = dbapi_connection.cursor()
            
            # パフォーマンス最適化
            cursor.execute("PRAGMA foreign_keys=ON")      # 外部キー制約有効
            cursor.execute("PRAGMA journal_mode=WAL")     # WALモード（高速化）
            cursor.execute("PRAGMA synchronous=NORMAL")   # 同期レベル調整
            cursor.execute("PRAGMA cache_size=10000")     # キャッシュサイズ増加
            cursor.execute("PRAGMA temp_store=MEMORY")    # 一時テーブルをメモリに
            cursor.execute("PRAGMA mmap_size=268435456")  # メモリマップサイズ（256MB）
            
            cursor.close()
            
        self.logger.debug("SQLite engine configured with performance optimizations")
    
    def _create_tables(self) -> None:
        """データベーステーブルを作成"""
        try:
            # modelsをインポート（循環インポート回避）
            from database.models import Base
            
            # テーブル作成
            Base.metadata.create_all(bind=self.engine)
            self.logger.info("Database tables created successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to create tables: {e}")
            raise
    
    def _test_connection(self) -> None:
        """データベース接続をテスト"""
        try:
            with self.get_session() as session:
                # 簡単なクエリで接続確認
                result = session.execute(text("SELECT 1")).scalar()
                if result != 1:
                    raise OperationalError("Connection test failed", None, None)
                
            self.logger.debug("Database connection test passed")
            
        except Exception as e:
            self.logger.error(f"Database connection test failed: {e}")
            raise
    
    @contextmanager
    def get_session(self) -> Generator[Session, None, None]:
        """
        データベースセッションを取得（コンテキストマネージャー）
        
        使用例:
            with db_connection.get_session() as session:
                result = session.query(DatabaseQuestion).all()
        """
        if not self._is_initialized:
            self.initialize()
        
        session = self.SessionLocal()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            self.logger.error(f"Database session error: {e}")
            raise
        finally:
            session.close()
    
    def get_session_factory(self) -> sessionmaker:
        """セッションファクトリを取得"""
        if not self._is_initialized:
            self.initialize()
        return self.SessionLocal
    
    def get_engine(self) -> Engine:
        """SQLAlchemyエンジンを取得"""
        if not self._is_initialized:
            self.initialize()
        return self.engine
    
    def health_check(self) -> dict:
        """データベースヘルスチェック"""
        try:
            with self.get_session() as session:
                # 基本接続確認
                session.execute(text("SELECT 1")).scalar()
                
                # テーブル存在確認
                tables_query = text("""
                    SELECT name FROM sqlite_master 
                    WHERE type='table' AND name NOT LIKE 'sqlite_%'
                """)
                tables = [row[0] for row in session.execute(tables_query)]
                
                # データベースサイズ確認
                size_query = text("SELECT page_count * page_size as size FROM pragma_page_count(), pragma_page_size()")
                db_size = session.execute(size_query).scalar()
                
                return {
                    "status": "healthy",
                    "database_url": self.database_url,
                    "tables": tables,
                    "database_size_bytes": db_size,
                    "database_size_mb": round(db_size / 1024 / 1024, 2) if db_size else 0
                }
                
        except Exception as e:
            self.logger.error(f"Database health check failed: {e}")
            return {
                "status": "unhealthy",
                "error": str(e),
                "database_url": self.database_url
            }
    
    def optimize_database(self) -> None:
        """データベース最適化を実行"""
        try:
            with self.get_session() as session:
                self.logger.info("Starting database optimization...")
                
                # VACUUM - データベースの最適化
                session.execute(text("VACUUM"))
                
                # ANALYZE - クエリプランナーの統計更新
                session.execute(text("ANALYZE"))
                
                self.logger.info("Database optimization completed")
                
        except Exception as e:
            self.logger.error(f"Database optimization failed: {e}")
            raise
    
    def get_database_info(self) -> dict:
        """データベース情報を取得"""
        try:
            with self.get_session() as session:
                info = {}
                
                # SQLiteバージョン
                version_result = session.execute(text("SELECT sqlite_version()")).scalar()
                info["sqlite_version"] = version_result
                
                # データベースサイズ
                size_query = text("""
                    SELECT page_count * page_size as size 
                    FROM pragma_page_count(), pragma_page_size()
                """)
                size = session.execute(size_query).scalar()
                info["database_size_bytes"] = size
                info["database_size_mb"] = round(size / 1024 / 1024, 2) if size else 0
                
                # テーブル数
                table_count_query = text("""
                    SELECT COUNT(*) FROM sqlite_master 
                    WHERE type='table' AND name NOT LIKE 'sqlite_%'
                """)
                table_count = session.execute(table_count_query).scalar()
                info["table_count"] = table_count
                
                # 設定情報
                pragma_queries = [
                    "PRAGMA foreign_keys",
                    "PRAGMA journal_mode", 
                    "PRAGMA synchronous",
                    "PRAGMA cache_size"
                ]
                
                pragmas = {}
                for pragma in pragma_queries:
                    try:
                        result = session.execute(text(pragma)).scalar()
                        pragma_name = pragma.replace("PRAGMA ", "")
                        pragmas[pragma_name] = result
                    except:
                        pass
                
                info["sqlite_settings"] = pragmas
                info["database_url"] = self.database_url
                
                return info
                
        except Exception as e:
            self.logger.error(f"Failed to get database info: {e}")
            return {"error": str(e)}
    
    def close(self) -> None:
        """データベース接続を閉じる"""
        if self.engine:
            self.engine.dispose()
            self.logger.info("Database connection closed")
        
        self._is_initialized = False


# グローバルデータベース接続インスタンス
_db_connection: Optional[DatabaseConnection] = None


def get_database_connection(database_url: Optional[str] = None) -> DatabaseConnection:
    """
    グローバルデータベース接続インスタンスを取得
    
    Args:
        database_url: データベースURL（初回のみ有効）
    
    Returns:
        DatabaseConnection: データベース接続インスタンス
    """
    global _db_connection
    
    if _db_connection is None:
        _db_connection = DatabaseConnection(database_url=database_url)
        _db_connection.initialize()
    
    return _db_connection


def reset_database_connection() -> None:
    """グローバル接続をリセット（テスト用）"""
    global _db_connection
    if _db_connection:
        _db_connection.close()
    _db_connection = None


# 便利関数
@contextmanager
def get_db_session(database_url: Optional[str] = None) -> Generator[Session, None, None]:
    """
    データベースセッションを取得する便利関数
    
    使用例:
        with get_db_session() as session:
            questions = session.query(DatabaseQuestion).all()
    """
    db_connection = get_database_connection(database_url)
    with db_connection.get_session() as session:
        yield session


def initialize_database(database_url: Optional[str] = None) -> DatabaseConnection:
    """
    データベースを初期化する便利関数
    
    Args:
        database_url: データベースURL
    
    Returns:
        DatabaseConnection: 初期化されたデータベース接続
    """
    return get_database_connection(database_url)