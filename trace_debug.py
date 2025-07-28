"""
一行一行の実行をトレースするデバッグスクリプト
"""

import sys
import os
import tempfile
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

def trace_database_connection():
    """データベース接続の一行一行をトレース"""
    print("🔍 データベース接続トレース開始")
    print("=" * 50)
    
    # テスト用一時データベース
    test_dir = tempfile.mkdtemp(prefix="trace_test_")
    test_db = os.path.join(test_dir, "test.db")
    test_url = f"sqlite:///{test_db}"
    
    print(f"Step 1: テストDB URL作成")
    print(f"        URL: {test_url}")
    
    try:
        print(f"Step 2: DatabaseConnectionインポート")
        from database.connection import DatabaseConnection
        print(f"        ✅ インポート成功")
        
        print(f"Step 3: DatabaseConnectionインスタンス作成")
        conn = DatabaseConnection(test_url)
        print(f"        ✅ インスタンス作成成功")
        print(f"        database_url: {conn.database_url}")
        print(f"        _is_initialized: {conn._is_initialized}")
        
        print(f"Step 4: initialize()呼び出し")
        print(f"        initialize()メソッド開始...")
        
        # initialize()の各ステップをトレース
        print(f"Step 4.1: _ensure_database_directory()呼び出し")
        conn._ensure_database_directory()
        print(f"        ✅ ディレクトリ確保完了")
        
        print(f"Step 4.2: エンジン作成")
        from sqlalchemy import create_engine
        conn.engine = create_engine(
            conn.database_url,
            connect_args={"check_same_thread": False, "timeout": 30},
            pool_pre_ping=True,
            pool_recycle=3600,
            echo=False
        )
        print(f"        ✅ エンジン作成完了")
        
        print(f"Step 4.3: SQLite設定適用")
        conn._configure_sqlite_engine()
        print(f"        ✅ SQLite設定適用完了")
        
        print(f"Step 4.4: セッションファクトリ作成")
        from sqlalchemy.orm import sessionmaker
        conn.SessionLocal = sessionmaker(
            autocommit=False,
            autoflush=False,
            bind=conn.engine
        )
        print(f"        ✅ セッションファクトリ作成完了")
        
        print(f"Step 4.5: _create_tables()呼び出し - ここが問題の箇所！")
        print(f"        _create_tables()メソッド開始...")
        
        # _create_tables()を手動で実行してトレース
        try:
            print(f"Step 4.5.1: database.modelsインポート")
            from database.models import Base
            print(f"        ✅ modelsインポート成功")
            
            print(f"Step 4.5.2: Base.metadata.create_all()呼び出し")
            print(f"        この時点でログが出力されるはず...")
            Base.metadata.create_all(bind=conn.engine)
            print(f"        ✅ テーブル作成完了")
            
        except Exception as e:
            print(f"        ❌ _create_tables()エラー: {e}")
            raise
        
        print(f"Step 4.6: _test_connection()呼び出し")
        conn._test_connection()
        print(f"        ✅ 接続テスト完了")
        
        print(f"Step 4.7: 初期化フラグ設定")
        conn._is_initialized = True
        print(f"        ✅ 初期化完了")
        
        print(f"Step 5: セッション作成テスト")
        with conn.get_session() as session:
            from sqlalchemy import text
            result = session.execute(text("SELECT 1")).scalar()
            print(f"        ✅ セッションテスト成功: {result}")
        
        print(f"Step 6: クリーンアップ")
        conn.close()
        import shutil
        shutil.rmtree(test_dir)
        print(f"        ✅ クリーンアップ完了")
        
        return True
        
    except Exception as e:
        print(f"❌ トレース中にエラー: {e}")
        import traceback
        traceback.print_exc()
        return False

def trace_global_connection():
    """グローバル接続のトレース"""
    print("\n🔍 グローバル接続トレース開始")
    print("=" * 50)
    
    test_dir = tempfile.mkdtemp(prefix="trace_global_")
    test_db = os.path.join(test_dir, "test.db")
    test_url = f"sqlite:///{test_db}"
    
    try:
        print(f"Step 1: インポート")
        from database.connection import get_database_connection, reset_database_connection, _db_connection
        print(f"        ✅ インポート成功")
        print(f"        初期_db_connection: {_db_connection}")
        
        print(f"Step 2: リセット")
        reset_database_connection()
        print(f"        ✅ リセット完了")
        
        print(f"Step 3: 1回目のget_database_connection()呼び出し")
        conn1 = get_database_connection(test_url)
        print(f"        ✅ 1回目完了: {type(conn1)}")
        
        print(f"Step 4: 2回目のget_database_connection()呼び出し")
        conn2 = get_database_connection(test_url)
        print(f"        ✅ 2回目完了: {type(conn2)}")
        print(f"        同じインスタンス: {conn1 is conn2}")
        
        print(f"Step 5: 3回目のget_database_connection()呼び出し")
        conn3 = get_database_connection(test_url)
        print(f"        ✅ 3回目完了: {type(conn3)}")
        print(f"        同じインスタンス: {conn1 is conn3}")
        
        # クリーンアップ
        reset_database_connection()
        import shutil
        shutil.rmtree(test_dir)
        
        return True
        
    except Exception as e:
        print(f"❌ グローバル接続トレースエラー: {e}")
        import traceback
        traceback.print_exc()
        return False

def trace_get_db_session():
    """get_db_sessionの詳細トレース"""
    print("\n🔍 get_db_sessionトレース開始")
    print("=" * 50)
    
    test_dir = tempfile.mkdtemp(prefix="trace_session_")
    test_db = os.path.join(test_dir, "test.db")
    test_url = f"sqlite:///{test_db}"
    
    try:
        print(f"Step 1: インポートとリセット")
        from database.connection import get_db_session, reset_database_connection
        reset_database_connection()
        print(f"        ✅ 準備完了")
        
        print(f"Step 2: 1回目のget_db_session()呼び出し")
        print(f"        with get_db_session({test_url}) as session:")
        with get_db_session(test_url) as session:
            from sqlalchemy import text
            result = session.execute(text("SELECT 1")).scalar()
            print(f"        ✅ 1回目セッション成功: {result}")
        
        print(f"Step 3: 2回目のget_db_session()呼び出し")
        print(f"        with get_db_session({test_url}) as session:")
        with get_db_session(test_url) as session:
            from sqlalchemy import text
            result = session.execute(text("SELECT 1")).scalar()
            print(f"        ✅ 2回目セッション成功: {result}")
        
        print(f"Step 4: 3回目のget_db_session()呼び出し")
        print(f"        with get_db_session({test_url}) as session:")
        with get_db_session(test_url) as session:
            from sqlalchemy import text
            result = session.execute(text("SELECT 1")).scalar()
            print(f"        ✅ 3回目セッション成功: {result}")
        
        # クリーンアップ
        reset_database_connection()
        import shutil
        shutil.rmtree(test_dir)
        
        return True
        
    except Exception as e:
        print(f"❌ get_db_sessionトレースエラー: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """メイン関数"""
    print("🕵️ 詳細トレースデバッグ開始")
    
    tests = [
        ("データベース接続", trace_database_connection),
        ("グローバル接続", trace_global_connection),
        ("get_db_session", trace_get_db_session)
    ]
    
    for test_name, test_func in tests:
        print(f"\n{'='*60}")
        print(f"テスト: {test_name}")
        print(f"{'='*60}")
        
        try:
            result = test_func()
            if result:
                print(f"\n✅ {test_name}: 成功")
            else:
                print(f"\n❌ {test_name}: 失敗")
                break  # 最初の失敗で停止
        except Exception as e:
            print(f"\n💥 {test_name}: 例外 - {e}")
            break

if __name__ == "__main__":
    main()