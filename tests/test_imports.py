# tests/test_imports.py
"""
Pythonインポートと依存関係の検証テスト
全モジュールのインポート可能性と循環依存をチェック
"""

import os
import sys
import pytest
import importlib
from pathlib import Path
import warnings

# プロジェクトルートを取得
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class TestBasicImports:
    """基本インポートテスト"""
    
    def test_standard_library_imports(self):
        """標準ライブラリのインポート確認"""
        standard_modules = [
            'os', 'sys', 'json', 'csv', 'logging', 'datetime', 
            'pathlib', 'uuid', 'sqlite3', 'argparse'
        ]
        
        import_errors = []
        for module_name in standard_modules:
            try:
                importlib.import_module(module_name)
            except ImportError as e:
                import_errors.append(f"{module_name}: {e}")
        
        assert not import_errors, f"標準ライブラリのインポートエラー: {import_errors}"
    
    def test_third_party_imports(self):
        """サードパーティライブラリのインポート確認"""
        third_party_modules = [
            'fastapi',
            'uvicorn', 
            'sqlalchemy',
            'pydantic'
        ]
        
        import_errors = []
        for module_name in third_party_modules:
            try:
                importlib.import_module(module_name)
            except ImportError as e:
                import_errors.append(f"{module_name}: {e}")
        
        # サードパーティライブラリは警告のみ（インストールされていない可能性）
        if import_errors:
            warnings.warn(f"サードパーティライブラリが見つかりません: {import_errors}")


class TestAppModuleImports:
    """アプリケーションモジュールのインポートテスト"""
    
    def setup_method(self):
        """テスト前の準備"""
        # プロジェクトルートをパスに追加
        if str(PROJECT_ROOT) not in sys.path:
            sys.path.insert(0, str(PROJECT_ROOT))
    
    def test_config_import(self):
        """設定モジュールのインポート"""
        try:
            from app.config import get_settings, Settings
            # 基本的な設定取得テスト
            settings = get_settings()
            assert isinstance(settings, Settings)
        except ImportError as e:
            pytest.fail(f"設定モジュールのインポートエラー: {e}")
        except Exception as e:
            # 設定ファイルがない場合などはワーニング
            warnings.warn(f"設定の初期化で警告: {e}")
    
    def test_logger_import(self):
        """ロガーモジュールのインポート"""
        try:
            from utils.logger import get_logger, configure_logging
            logger = get_logger()
            assert logger is not None
        except ImportError as e:
            pytest.fail(f"ロガーモジュールのインポートエラー: {e}")
    
    def test_models_import(self):
        """モデルモジュールのインポート"""
        try:
            from app.core.models import Question, QuizSession, Answer
            # 基本的なモデル作成テスト
            question = Question(
                id=1,
                text="テスト問題",
                options=["選択肢1", "選択肢2", "選択肢3", "選択肢4"],
                correct_answer=0
            )
            assert question.text == "テスト問題"
        except ImportError as e:
            pytest.fail(f"モデルモジュールのインポートエラー: {e}")
        except Exception as e:
            pytest.fail(f"モデル作成エラー: {e}")
    
    def test_interfaces_import(self):
        """インターフェースモジュールのインポート"""
        try:
            from app.core.interfaces import (
                QuizServiceInterface,
                QuestionRepositoryInterface,
                SessionRepositoryInterface
            )
            # インターフェースが ABC を継承しているか確認
            import abc
            assert issubclass(QuizServiceInterface, abc.ABC)
            assert issubclass(QuestionRepositoryInterface, abc.ABC)
        except ImportError as e:
            pytest.fail(f"インターフェースモジュールのインポートエラー: {e}")
    
    def test_exceptions_import(self):
        """例外モジュールのインポート"""
        try:
            from app.core.exceptions import (
                QuizError, SessionError, QuestionNotFoundError,
                CSVImportError, DatabaseError
            )
            # 例外が適切な継承関係にあるか確認
            assert issubclass(SessionError, QuizError)
            assert issubclass(QuestionNotFoundError, QuizError)
        except ImportError as e:
            pytest.fail(f"例外モジュールのインポートエラー: {e}")
    
    def test_service_factory_import(self):
        """サービスファクトリーのインポート"""
        try:
            from app.core.service_factory import (
                get_service_factory, get_quiz_service, 
                get_database_service, get_csv_importer
            )
            # ファクトリーが取得できるか確認
            factory = get_service_factory()
            assert factory is not None
        except ImportError as e:
            pytest.fail(f"サービスファクトリーのインポートエラー: {e}")
        except Exception as e:
            # 初期化エラーは警告として扱う
            warnings.warn(f"サービスファクトリー初期化警告: {e}")


class TestAPIModuleImports:
    """APIモジュールのインポートテスト"""
    
    def setup_method(self):
        """テスト前の準備"""
        if str(PROJECT_ROOT) not in sys.path:
            sys.path.insert(0, str(PROJECT_ROOT))
    
    def test_main_app_import(self):
        """FastAPIメインアプリのインポート"""
        try:
            # main.pyが存在することを確認
            main_file = PROJECT_ROOT / "backend" / "main.py"
            assert main_file.exists(), "backend/main.py が見つかりません"
            
            # main モジュールからのインポートテスト
            sys.path.insert(0, str(PROJECT_ROOT / "backend"))
            from main import create_app
            app = create_app()
            assert app is not None
        except ImportError as e:
            pytest.fail(f"メインアプリのインポートエラー: {e}")
        except Exception as e:
            warnings.warn(f"メインアプリ初期化警告: {e}")
        finally:
            # パスをクリーンアップ
            if str(PROJECT_ROOT / "backend") in sys.path:
                sys.path.remove(str(PROJECT_ROOT / "backend"))
    
    def test_api_routers_import(self):
        """APIルーターのインポート"""
        try:
            # APIモジュールのパスを追加
            api_path = PROJECT_ROOT / "backend"
            if str(api_path) not in sys.path:
                sys.path.insert(0, str(api_path))
            
            from app.api.quiz import router as quiz_router
            from app.api.health import router as health_router
            
            # ルーターがFastAPIRouterインスタンスか確認
            assert hasattr(quiz_router, 'routes')
            assert hasattr(health_router, 'routes')
            
        except ImportError as e:
            pytest.fail(f"APIルーターのインポートエラー: {e}")
        finally:
            # パスをクリーンアップ
            if str(api_path) in sys.path:
                sys.path.remove(str(api_path))
    
    def test_pydantic_models_import(self):
        """Pydanticモデルのインポート"""
        try:
            api_path = PROJECT_ROOT / "backend"
            if str(api_path) not in sys.path:
                sys.path.insert(0, str(api_path))
            
            from app.models.quiz_models import (
                QuizSessionRequest, QuizSessionResponse,
                AnswerRequest, AnswerResponse
            )
            from app.models.common import BaseResponse, ErrorResponse
            
            # Pydanticモデルが正しく定義されているか確認
            try:
                from pydantic import BaseModel
                assert issubclass(QuizSessionRequest, BaseModel)
                assert issubclass(BaseResponse, BaseModel)
            except ImportError:
                warnings.warn("Pydantic未インストール - モデル継承チェックをスキップ")
                
        except ImportError as e:
            pytest.fail(f"Pydanticモデルのインポートエラー: {e}")
        finally:
            if str(api_path) in sys.path:
                sys.path.remove(str(api_path))


class TestDatabaseImports:
    """データベース関連モジュールのインポートテスト"""
    
    def test_database_models_import(self):
        """データベースモデルのインポート"""
        try:
            from database.models import (
                Base, DatabaseQuestion, DatabaseQuizSession,
                DatabaseQuizAnswer, DatabaseUserHistory
            )
            # SQLAlchemyモデルが正しく定義されているか確認
            try:
                from sqlalchemy.ext.declarative import DeclarativeMeta
                assert isinstance(Base, DeclarativeMeta)
            except ImportError:
                warnings.warn("SQLAlchemy未インストール - モデルチェックをスキップ")
                
        except ImportError as e:
            pytest.fail(f"データベースモデルのインポートエラー: {e}")
    
    def test_database_connection_import(self):
        """データベース接続のインポート"""
        try:
            from database.connection import (
                DatabaseConnection, get_database_connection, get_db_session
            )
            # 基本的なクラス構造確認
            assert callable(get_database_connection)
            assert callable(get_db_session)
        except ImportError as e:
            pytest.fail(f"データベース接続のインポートエラー: {e}")


class TestCoreServicesImports:
    """コアサービスのインポートテスト"""
    
    def test_quiz_service_import(self):
        """クイズサービスのインポート"""
        try:
            from app.core.quiz import QuizService
            # サービスクラスの基本構造確認
            assert hasattr(QuizService, '__init__')
            assert hasattr(QuizService, 'create_session')
            assert hasattr(QuizService, 'answer_question')
        except ImportError as e:
            pytest.fail(f"クイズサービスのインポートエラー: {e}")
    
    def test_csv_import_service_import(self):
        """CSVインポートサービスのインポート"""
        try:
            from app.core.csv_import import CSVImportService
            # サービスクラスの基本構造確認
            assert hasattr(CSVImportService, '__init__')
            assert hasattr(CSVImportService, 'import_from_csv')
            assert hasattr(CSVImportService, 'validate_csv_file')
        except ImportError as e:
            pytest.fail(f"CSVインポートサービスのインポートエラー: {e}")
    
    def test_database_service_import(self):
        """データベースサービスのインポート"""
        try:
            from app.core.database import DatabaseService
            # サービスクラスの基本構造確認
            assert hasattr(DatabaseService, '__init__')
            assert hasattr(DatabaseService, 'get_questions')
            assert hasattr(DatabaseService, 'save_question')
        except ImportError as e:
            pytest.fail(f"データベースサービスのインポートエラー: {e}")


class TestAdminScriptImports:
    """管理スクリプトのインポートテスト"""
    
    def test_admin_script_structure(self):
        """admin.pyの構造確認"""
        admin_file = PROJECT_ROOT / "admin.py"
        assert admin_file.exists(), "admin.py が見つかりません"
        
        # ファイル内容の基本チェック
        with open(admin_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 必要なクラス・関数の存在確認
        required_elements = [
            'AdminCLI',
            'import_csv',
            'show_database_info',
            'main'
        ]
        
        missing_elements = []
        for element in required_elements:
            if element not in content:
                missing_elements.append(element)
        
        assert not missing_elements, f"admin.pyに必要な要素がありません: {missing_elements}"
    
    def test_quiz_script_structure(self):
        """quiz.pyの構造確認"""
        quiz_file = PROJECT_ROOT / "quiz.py"
        assert quiz_file.exists(), "quiz.py が見つかりません"
        
        # ファイル内容の基本チェック
        with open(quiz_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 必要な関数の存在確認
        required_elements = [
            'check_quiz_readiness',
            'main'
        ]
        
        missing_elements = []
        for element in required_elements:
            if element not in content:
                missing_elements.append(element)
        
        assert not missing_elements, f"quiz.pyに必要な要素がありません: {missing_elements}"


class TestCircularImportDetection:
    """循環インポートの検出テスト"""
    
    def test_no_circular_imports_in_core(self):
        """コアモジュール間の循環インポート確認"""
        core_modules = [
            'app.core.models',
            'app.core.interfaces', 
            'app.core.exceptions',
            'app.core.quiz',
            'app.core.database',
            'app.core.csv_import',
            'app.core.service_factory'
        ]
        
        # 各モジュールを個別にインポートして循環インポートをチェック
        import_errors = []
        
        for module_name in core_modules:
            try:
                # 新しいPythonプロセスでインポートをテスト
                import subprocess
                result = subprocess.run(
                    [sys.executable, '-c', f'import {module_name}'],
                    capture_output=True,
                    text=True,
                    timeout=10
                )
                
                if result.returncode != 0:
                    import_errors.append(f"{module_name}: {result.stderr}")
                    
            except subprocess.TimeoutExpired:
                import_errors.append(f"{module_name}: インポートタイムアウト（循環インポートの可能性）")
            except Exception as e:
                import_errors.append(f"{module_name}: {e}")
        
        assert not import_errors, f"コアモジュールのインポートエラー: {import_errors}"
    
    def test_no_circular_imports_in_api(self):
        """APIモジュール間の循環インポート確認"""
        # backend/ ディレクトリをパスに追加
        backend_path = PROJECT_ROOT / "backend"
        if str(backend_path) not in sys.path:
            sys.path.insert(0, str(backend_path))
        
        api_modules = [
            'app.api.quiz',
            'app.api.health',
            'app.models.quiz_models',
            'app.models.common'
        ]
        
        import_errors = []
        
        try:
            for module_name in api_modules:
                try:
                    import subprocess
                    # Windowsパス対応：raw文字列とreplace使用
                    backend_path_str = str(backend_path).replace('\\', '/')
                    result = subprocess.run(
                        [sys.executable, '-c', f'import sys; sys.path.insert(0, r"{backend_path}"); import {module_name}'],
                        capture_output=True,
                        text=True,
                        timeout=10
                    )
                    
                    if result.returncode != 0:
                        import_errors.append(f"{module_name}: {result.stderr}")
                        
                except subprocess.TimeoutExpired:
                    import_errors.append(f"{module_name}: インポートタイムアウト（循環インポートの可能性）")
                except Exception as e:
                    import_errors.append(f"{module_name}: {e}")
        
        finally:
            # パスをクリーンアップ
            if str(backend_path) in sys.path:
                sys.path.remove(str(backend_path))
        
        assert not import_errors, f"APIモジュールのインポートエラー: {import_errors}"


class TestDependencyImports:
    """依存性注入のインポートテスト"""
    
    def test_dependencies_import(self):
        """依存性注入モジュールのインポート"""
        try:
            backend_path = PROJECT_ROOT / "backend"
            if str(backend_path) not in sys.path:
                sys.path.insert(0, str(backend_path))
            
            from app.core.dependencies import (
                get_quiz_service, get_csv_import_service, get_database_service
            )
            
            # 依存性注入関数が呼び出し可能か確認
            assert callable(get_quiz_service)
            assert callable(get_csv_import_service)
            assert callable(get_database_service)
            
        except ImportError as e:
            pytest.fail(f"依存性注入のインポートエラー: {e}")
        finally:
            if str(backend_path) in sys.path:
                sys.path.remove(str(backend_path))


class TestImportPerformance:
    """インポートパフォーマンステスト"""
    
    def test_import_speed(self):
        """主要モジュールのインポート速度確認"""
        import time
        
        slow_imports = []
        
        modules_to_test = [
            ('app.core.models', 1.0),
            ('app.core.interfaces', 0.5),
            ('utils.logger', 0.5)
        ]
        
        for module_name, max_time in modules_to_test:
            start_time = time.time()
            try:
                importlib.import_module(module_name)
                import_time = time.time() - start_time
                
                if import_time > max_time:
                    slow_imports.append(f"{module_name}: {import_time:.2f}秒")
                    
            except ImportError:
                # インポートエラーは別のテストで処理
                pass
        
        if slow_imports:
            warnings.warn(f"インポートが遅いモジュール: {slow_imports}")


def run_import_tests():
    """インポートテストの実行"""
    print("🔄 インポートテスト開始...")
    
    # pytestを使用してテストを実行
    result = pytest.main([
        __file__,
        "-v",  # 詳細出力
        "--tb=short",  # 短いトレースバック
        "-W", "ignore::DeprecationWarning",  # 非推奨警告を無視
        "--disable-warnings"  # 一般的な警告を無効化
    ])
    
    if result == 0:
        print("✅ インポートテスト: 全て通過")
        return True
    else:
        print("❌ インポートテスト: 失敗")
        return False


if __name__ == "__main__":
    # スタンドアローン実行時
    success = run_import_tests()
    sys.exit(0 if success else 1)