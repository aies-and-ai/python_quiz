"""
データベース接続の単体テスト
問題の原因を特定するためのデバッグスクリプト
"""

import sys
import os
import tempfile
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.absolute()
sys.path.insert(0, str(project_root))

def test_basic_imports():
    """基本的なインポートテスト"""
    print("=== 基本インポートテスト ===")
    
    try:
        from utils.logger import get_logger
        print("✅ utils.logger インポート成功")
    except Exception as e:
        print(f"❌ utils.logger インポートエラー: {e}")
        return False
    
    try:
        from database.connection import DatabaseConnection
        print("✅ database.connection インポート成功")
    except Exception as e:
        print(f"❌ database.connection インポートエラー: {e}")
        return False
    
    try:
        from database.models import Base, DatabaseQuestion
        print("✅ database.models インポート成功")
    except Exception as e:
        print(f"❌ database.models インポートエラー: {e}")
        return False
    
    return True

def test_single_connection():
    """単一データベース接続テスト"""
    print("\n=== 単一接続テスト ===")
    
    # テスト用一時データベース
    test_dir = tempfile.mkdtemp(prefix="db_test_")
    test_db = os.path.join(test_dir, "test.db")
    test_url = f"sqlite:///{test_db}"
    
    print(f"テストDB: {test_url}")
    
    try:
        from database.connection import DatabaseConnection
        from utils.logger import get_logger
        
        logger = get_logger()
        
        # 1回目の接続
        print("1回目の接続...")
        conn1 = DatabaseConnection(test_url)
        conn1.initialize()
        print("✅ 1回目の接続成功")
        
        # 2回目の接続（同じURL）
        print("2回目の接続...")
        conn2 = DatabaseConnection(test_url)
        conn2.initialize()
        print("✅ 2回目の接続成功")
        
        # セッション作成テスト
        print("セッション作成テスト...")
        with conn1.get_session() as session:
            result = session.execute("SELECT 1").scalar()
            print(f"✅ セッション1成功: {result}")
        
        with conn2.get_session() as session:
            result = session.execute("SELECT 1").scalar()
            print(f"✅ セッション2成功: {result}")
        
        # クリーンアップ
        conn1.close()
        conn2.close()
        
        import shutil
        shutil.rmtree(test_dir)
        
        return True
        
    except Exception as e:
        print(f"❌ 単一接続テストエラー: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_global_connection():
    """グローバル接続テスト"""
    print("\n=== グローバル接続テスト ===")
    
    test_dir = tempfile.mkdtemp(prefix="db_global_test_")
    test_db = os.path.join(test_dir, "test.db")
    test_url = f"sqlite:///{test_db}"
    
    print(f"テストDB: {test_url}")
    
    try:
        from database.connection import get_database_connection, get_db_session, reset_database_connection
        
        # 既存接続をリセット
        reset_database_connection()
        
        # 1回目のグローバル接続
        print("1回目のグローバル接続...")
        conn1 = get_database_connection(test_url)
        print("✅ 1回目のグローバル接続成功")
        
        # 2回目のグローバル接続（同じインスタンスが返されるはず）
        print("2回目のグローバル接続...")
        conn2 = get_database_connection(test_url)
        print(f"✅ 2回目のグローバル接続成功")
        print(f"同じインスタンス: {conn1 is conn2}")
        
        # get_db_sessionテスト
        print("get_db_session テスト...")
        with get_db_session(test_url) as session:
            result = session.execute("SELECT 1").scalar()
            print(f"✅ get_db_session成功: {result}")
        
        # 複数回のget_db_session呼び出し
        print("複数回のget_db_session呼び出し...")
        for i in range(3):
            with get_db_session(test_url) as session:
                result = session.execute("SELECT 1").scalar()
                print(f"  回数{i+1}: {result}")
        
        # クリーンアップ
        reset_database_connection()
        import shutil
        shutil.rmtree(test_dir)
        
        return True
        
    except Exception as e:
        print(f"❌ グローバル接続テストエラー: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_database_service():
    """DatabaseService単体テスト"""
    print("\n=== DatabaseService単体テスト ===")
    
    test_dir = tempfile.mkdtemp(prefix="db_service_test_")
    test_db = os.path.join(test_dir, "test.db")
    test_url = f"sqlite:///{test_db}"
    
    print(f"テストDB: {test_url}")
    
    try:
        from app.core.database import DatabaseService
        
        print("DatabaseService初期化...")
        db_service = DatabaseService(test_url)
        print("✅ DatabaseService初期化成功")
        
        print("get_question_count呼び出し...")
        count1 = db_service.get_question_count()
        print(f"✅ 1回目: {count1}")
        
        print("get_question_count再呼び出し...")
        count2 = db_service.get_question_count()
        print(f"✅ 2回目: {count2}")
        
        print("get_categories呼び出し...")
        categories = db_service.get_categories()
        print(f"✅ カテゴリ: {categories}")
        
        print("get_difficulties呼び出し...")
        difficulties = db_service.get_difficulties()
        print(f"✅ 難易度: {difficulties}")
        
        # クリーンアップ
        import shutil
        shutil.rmtree(test_dir)
        
        return True
        
    except Exception as e:
        print(f"❌ DatabaseServiceテストエラー: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """メイン関数"""
    print("🔍 データベース接続デバッグテスト開始")
    print("=" * 50)
    
    tests = [
        ("基本インポート", test_basic_imports),
        ("単一接続", test_single_connection),
        ("グローバル接続", test_global_connection),
        ("DatabaseService", test_database_service)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            if result:
                print(f"✅ {test_name}: 成功")
                passed += 1
            else:
                print(f"❌ {test_name}: 失敗")
                failed += 1
        except Exception as e:
            print(f"💥 {test_name}: 例外 - {e}")
            failed += 1
    
    print(f"\n📊 デバッグテスト結果")
    print(f"成功: {passed}, 失敗: {failed}")
    print("=" * 50)
    
    if failed == 0:
        print("🎉 すべてのテストが成功しました！")
        print("問題は統合部分にある可能性があります。")
    else:
        print("💥 基本的な問題が見つかりました。")
        print("上記のエラーを修正してください。")

if __name__ == "__main__":
    main()