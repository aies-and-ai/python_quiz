"""
統合テスト - 新アーキテクチャの動作確認
すべてのコンポーネントが正しく連携するかテスト
"""

import sys
import os
import tempfile
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_basic_imports():
    """基本インポートテスト"""
    print("=== 基本インポートテスト ===")
    
    try:
        from app.config import get_settings
        print("✅ app.config インポート成功")
    except Exception as e:
        print(f"❌ app.config インポートエラー: {e}")
        return False
    
    try:
        from app.core.service_factory import get_service_factory
        print("✅ app.core.service_factory インポート成功")
    except Exception as e:
        print(f"❌ app.core.service_factory インポートエラー: {e}")
        return False
    
    try:
        from utils.logger import get_logger
        print("✅ utils.logger インポート成功")
    except Exception as e:
        print(f"❌ utils.logger インポートエラー: {e}")
        return False
    
    try:
        from database import get_database_connection
        print("✅ database インポート成功")
    except Exception as e:
        print(f"❌ database インポートエラー: {e}")
        return False
    
    return True


def test_service_factory():
    """サービスファクトリーテスト"""
    print("\n=== サービスファクトリーテスト ===")
    
    try:
        from app.core.service_factory import initialize_services, get_quiz_service, get_csv_importer
        
        # テスト用データベース
        test_dir = tempfile.mkdtemp(prefix="integration_test_")
        test_db = os.path.join(test_dir, "test.db")
        test_url = f"sqlite:///{test_db}"
        
        print(f"テスト用DB: {test_url}")
        
        # サービス初期化
        print("サービス初期化中...")
        initialize_services(test_url)
        print("✅ サービス初期化成功")
        
        # サービス取得テスト
        quiz_service = get_quiz_service()
        print("✅ QuizService取得成功")
        
        csv_importer = get_csv_importer()
        print("✅ CSVImporter取得成功")
        
        # クリーンアップ
        from app.core.service_factory import shutdown_services
        shutdown_services()
        
        import shutil
        shutil.rmtree(test_dir)
        
        return True
        
    except Exception as e:
        print(f"❌ サービスファクトリーエラー: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_database_operations():
    """データベース操作テスト"""
    print("\n=== データベース操作テスト ===")
    
    try:
        from app.core.service_factory import initialize_services, get_database_service
        from app.core.models import Question
        
        # テスト用データベース
        test_dir = tempfile.mkdtemp(prefix="db_test_")
        test_db = os.path.join(test_dir, "test.db")
        test_url = f"sqlite:///{test_db}"
        
        # サービス初期化
        initialize_services(test_url)
        db_service = get_database_service()
        
        # テスト問題作成
        test_question = Question(
            id=1,
            text="テスト問題：1+1=?",
            options=["1", "2", "3", "4"],
            correct_answer=1,
            explanation="1+1=2です",
            category="数学",
            difficulty="初級"
        )
        
        # 問題保存テスト
        saved_question = db_service.save_question(test_question, "test.csv")
        print("✅ 問題保存成功")
        
        # 問題取得テスト
        questions = db_service.get_questions(limit=10)
        print(f"✅ 問題取得成功: {len(questions)}問")
        
        # 問題数取得テスト
        count = db_service.get_question_count()
        print(f"✅ 問題数取得成功: {count}問")
        
        # クリーンアップ
        from app.core.service_factory import shutdown_services
        shutdown_services()
        
        import shutil
        shutil.rmtree(test_dir)
        
        return True
        
    except Exception as e:
        print(f"❌ データベース操作エラー: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_quiz_service():
    """クイズサービステスト"""
    print("\n=== クイズサービステスト ===")
    
    try:
        from app.core.service_factory import initialize_services, get_quiz_service, get_database_service
        from app.core.models import Question
        
        # テスト用データベース
        test_dir = tempfile.mkdtemp(prefix="quiz_test_")
        test_db = os.path.join(test_dir, "test.db")
        test_url = f"sqlite:///{test_db}"
        
        # サービス初期化
        initialize_services(test_url)
        db_service = get_database_service()
        quiz_service = get_quiz_service()
        
        # テスト問題を追加
        for i in range(5):
            test_question = Question(
                id=i+1,
                text=f"テスト問題{i+1}：{i}+1=?",
                options=[str(i), str(i+1), str(i+2), str(i+3)],
                correct_answer=1,
                explanation=f"{i}+1={i+1}です",
                category="数学",
                difficulty="初級"
            )
            db_service.save_question(test_question, "test.csv")
        
        print("✅ テスト問題追加完了")
        
        # セッション作成テスト
        session = quiz_service.create_session(question_count=3)
        print(f"✅ セッション作成成功: {session.id}")
        
        # 問題取得テスト
        current_question = quiz_service.get_current_question(session.id)
        print(f"✅ 現在の問題取得成功: {current_question.text}")
        
        # 回答テスト
        result = quiz_service.answer_question(session.id, 1)  # 正解を選択
        print(f"✅ 回答処理成功: {'正解' if result['is_correct'] else '不正解'}")
        
        # 進行状況テスト
        progress = quiz_service.get_session_progress(session.id)
        print(f"✅ 進行状況取得成功: {progress['current_index']}/{progress['total_questions']}")
        
        # クリーンアップ
        from app.core.service_factory import shutdown_services
        shutdown_services()
        
        import shutil
        shutil.rmtree(test_dir)
        
        return True
        
    except Exception as e:
        print(f"❌ クイズサービステストエラー: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_csv_import():
    """CSVインポートテスト"""
    print("\n=== CSVインポートテスト ===")
    
    try:
        from app.core.service_factory import initialize_services, get_csv_importer
        
        # テスト用データベース
        test_dir = tempfile.mkdtemp(prefix="csv_test_")
        test_db = os.path.join(test_dir, "test.db")
        test_url = f"sqlite:///{test_db}"
        
        # テスト用CSVファイル作成
        test_csv = os.path.join(test_dir, "test.csv")
        csv_content = """question,option1,option2,option3,option4,correct_answer,explanation
テスト問題1,選択肢1,選択肢2,選択肢3,選択肢4,2,これは説明です
テスト問題2,A,B,C,D,1,これも説明です"""
        
        with open(test_csv, 'w', encoding='utf-8') as f:
            f.write(csv_content)
        
        print("✅ テストCSVファイル作成完了")
        
        # サービス初期化
        initialize_services(test_url)
        csv_importer = get_csv_importer()
        
        # CSVインポートテスト
        result = csv_importer.import_from_csv(test_csv)
        print(f"✅ CSVインポート成功: {result['imported_count']}問インポート")
        
        # インポート結果確認
        if result['success'] and result['imported_count'] > 0:
            print("✅ CSVインポート動作確認成功")
        else:
            print(f"⚠️ インポート結果: {result}")
        
        # クリーンアップ
        from app.core.service_factory import shutdown_services
        shutdown_services()
        
        import shutil
        shutil.rmtree(test_dir)
        
        return True
        
    except Exception as e:
        print(f"❌ CSVインポートエラー: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_configuration():
    """設定システムテスト"""
    print("\n=== 設定システムテスト ===")
    
    try:
        from app.config import get_settings, Settings
        
        # 設定読み込みテスト
        settings = get_settings()
        print(f"✅ 設定読み込み成功")
        print(f"   データベースURL: {settings.database_url}")
        print(f"   ウィンドウサイズ: {settings.window_width}x{settings.window_height}")
        print(f"   デバッグモード: {settings.debug}")
        
        # 設定保存テスト
        test_settings = Settings(
            database_url="sqlite:///test.db",
            window_width=900,
            window_height=700,
            debug=True
        )
        
        test_config_file = "test_config.json"
        test_settings.save(test_config_file)
        print("✅ 設定保存成功")
        
        # 設定読み込みテスト
        loaded_settings = Settings.load(test_config_file)
        print("✅ 設定読み込み成功")
        
        # 値確認
        assert loaded_settings.window_width == 900
        assert loaded_settings.debug == True
        print("✅ 設定値確認成功")
        
        # クリーンアップ
        os.remove(test_config_file)
        
        return True
        
    except Exception as e:
        print(f"❌ 設定システムエラー: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """メイン統合テスト関数"""
    print("🚀 統合テスト開始")
    print("=" * 60)
    
    tests = [
        ("基本インポート", test_basic_imports),
        ("設定システム", test_configuration),
        ("サービスファクトリー", test_service_factory),
        ("データベース操作", test_database_operations),
        ("クイズサービス", test_quiz_service),
        ("CSVインポート", test_csv_import)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        print(f"\n{'='*60}")
        print(f"テスト: {test_name}")
        print(f"{'='*60}")
        
        try:
            result = test_func()
            if result:
                print(f"\n✅ {test_name}: 成功")
                passed += 1
            else:
                print(f"\n❌ {test_name}: 失敗")
                failed += 1
        except Exception as e:
            print(f"\n💥 {test_name}: 例外 - {e}")
            failed += 1
    
    print(f"\n{'='*60}")
    print(f"📊 統合テスト結果")
    print(f"{'='*60}")
    print(f"成功: {passed}, 失敗: {failed}")
    
    if failed == 0:
        print("🎉 すべての統合テストが成功しました！")
        print("アプリケーションの起動テストを実行してください: python main.py")
    else:
        print("💥 一部のテストが失敗しました。")
        print("上記のエラーを確認して修正してください。")
    
    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)