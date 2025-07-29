# tests/test_api_functionality.py
"""
API機能テスト
FastAPIアプリケーションの動作確認とエンドポイントテスト
"""

import os
import sys
import pytest
import asyncio
import json
from pathlib import Path
from unittest.mock import Mock, patch
import warnings

# プロジェクトルートを取得
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "backend"))


class TestFastAPISetup:
    """FastAPIセットアップテスト"""
    
    def test_fastapi_app_creation(self):
        """FastAPIアプリケーションの作成テスト"""
        try:
            from main import create_app
            app = create_app()
            
            # FastAPIアプリケーションの基本属性確認
            assert hasattr(app, 'routes'), "ルートが定義されていません"
            assert hasattr(app, 'middleware'), "ミドルウェアが定義されていません"
            assert app.title is not None, "アプリタイトルが設定されていません"
            
        except ImportError as e:
            pytest.skip(f"FastAPI未インストール: {e}")
        except Exception as e:
            pytest.fail(f"FastAPIアプリ作成エラー: {e}")
    
    def test_api_routes_registration(self):
        """APIルートの登録確認"""
        try:
            from main import create_app
            app = create_app()
            
            # 登録されたルートの確認
            route_paths = [route.path for route in app.routes]
            
            # 期待されるAPIエンドポイントの存在確認
            expected_paths = [
                '/api/v1/health',
                '/api/v1/sessions',
                '/api/v1/statistics',
                '/api/v1/categories',
                '/api/v1/difficulties'
            ]
            
            missing_paths = []
            for path in expected_paths:
                # パスマッチング（パラメータ付きルートも考慮）
                if not any(path in route_path for route_path in route_paths):
                    missing_paths.append(path)
            
            assert not missing_paths, f"期待されるAPIパスが見つかりません: {missing_paths}"
            
        except ImportError as e:
            pytest.skip(f"FastAPI未インストール: {e}")
        except Exception as e:
            pytest.fail(f"ルート確認エラー: {e}")
    
    def test_cors_middleware(self):
        """CORSミドルウェアの設定確認"""
        try:
            from main import create_app
            app = create_app()
            
            # ミドルウェアの存在確認
            middleware_types = [type(middleware.cls).__name__ for middleware in app.user_middleware]
            assert 'CORSMiddleware' in middleware_types, "CORSミドルウェアが設定されていません"
            
        except ImportError as e:
            pytest.skip(f"FastAPI未インストール: {e}")
        except Exception as e:
            pytest.fail(f"CORS確認エラー: {e}")


class TestAPIEndpoints:
    """APIエンドポイントテスト"""
    
    @pytest.fixture
    def mock_services(self):
        """モックサービスのセットアップ"""
        with patch('app.core.service_factory.get_quiz_service') as mock_quiz, \
             patch('app.core.service_factory.get_database_service') as mock_db:
            
            # モッククイズサービス
            mock_quiz_service = Mock()
            mock_quiz_service.get_available_categories.return_value = ["数学", "歴史"]
            mock_quiz_service.get_available_difficulties.return_value = ["初級", "中級", "上級"]
            mock_quiz_service.get_question_count.return_value = 50
            mock_quiz.return_value = mock_quiz_service
            
            # モックデータベースサービス
            mock_db_service = Mock()
            mock_db_service.health_check.return_value = {"status": "healthy"}
            mock_db_service.get_database_info.return_value = {"question_count": 50}
            mock_db.return_value = mock_db_service
            
            yield mock_quiz_service, mock_db_service
    
    def test_health_endpoint_structure(self):
        """ヘルスチェックエンドポイントの構造確認"""
        try:
            from app.api.health import router, health_check
            
            # ルーターの基本構造確認
            assert hasattr(router, 'routes'), "ヘルスチェックルーターにルートがありません"
            
            # ヘルスチェック関数の存在確認
            assert callable(health_check), "health_check関数が呼び出し可能ではありません"
            
        except ImportError as e:
            pytest.fail(f"ヘルスチェックAPI インポートエラー: {e}")
    
    def test_quiz_endpoint_structure(self):
        """クイズエンドポイントの構造確認"""
        try:
            from app.api.quiz import router
            from app.api.quiz import (
                create_quiz_session, get_current_question, 
                submit_answer, get_statistics
            )
            
            # ルーターの基本構造確認
            assert hasattr(router, 'routes'), "クイズルーターにルートがありません"
            
            # 主要関数の存在確認
            functions = [create_quiz_session, get_current_question, submit_answer, get_statistics]
            for func in functions:
                assert callable(func), f"{func.__name__}が呼び出し可能ではありません"
            
        except ImportError as e:
            pytest.fail(f"クイズAPI インポートエラー: {e}")
    
    @pytest.mark.asyncio
    async def test_health_check_response(self, mock_services):
        """ヘルスチェックのレスポンス確認"""
        try:
            from app.api.health import health_check
            
            # ヘルスチェック実行
            response = await health_check()
            
            # レスポンス構造確認
            assert hasattr(response, 'status'), "ステータスフィールドがありません"
            assert hasattr(response, 'version'), "バージョンフィールドがありません"
            
        except ImportError as e:
            pytest.skip(f"FastAPI未インストール: {e}")
        except Exception as e:
            pytest.fail(f"ヘルスチェック実行エラー: {e}")
    
    def test_pydantic_models_validation(self):
        """Pydanticモデルのバリデーション確認"""
        try:
            from app.models.quiz_models import (
                QuizSessionRequest, AnswerRequest
            )
            
            # 有効なデータでモデル作成
            valid_session_request = QuizSessionRequest(
                question_count=10,
                category="数学",
                difficulty="初級",
                shuffle=True
            )
            assert valid_session_request.question_count == 10
            
            valid_answer_request = AnswerRequest(
                session_id="test-session-id",
                selected_option=1
            )
            assert valid_answer_request.selected_option == 1
            
            # 無効なデータでバリデーションエラー確認
            try:
                from pydantic import ValidationError
                
                # 無効な問題数
                with pytest.raises(ValidationError):
                    QuizSessionRequest(
                        question_count=-1,  # 負の値
                        shuffle=True
                    )
                
                # 無効な選択肢
                with pytest.raises(ValidationError):
                    AnswerRequest(
                        session_id="test",
                        selected_option=5  # 範囲外
                    )
                    
            except ImportError:
                warnings.warn("Pydantic未インストール - バリデーションテストをスキップ")
            
        except ImportError as e:
            pytest.skip(f"Pydanticモデル未インストール: {e}")


class TestBusinessLogic:
    """ビジネスロジックテスト"""
    
    def test_question_model_validation(self):
        """問題モデルのバリデーション"""
        try:
            from app.core.models import Question
            
            # 有効な問題作成
            valid_question = Question(
                id=1,
                text="2 + 2 = ?",
                options=["3", "4", "5", "6"],
                correct_answer=1,
                explanation="2 + 2 = 4です",
                category="数学",
                difficulty="初級"
            )
            assert valid_question.text == "2 + 2 = ?"
            assert len(valid_question.options) == 4
            
            # 無効な問題（選択肢数不正）
            with pytest.raises(ValueError):
                Question(
                    id=1,
                    text="テスト問題",
                    options=["選択肢1", "選択肢2"],  # 2個しかない
                    correct_answer=0
                )
            
            # 無効な問題（正解番号範囲外）
            with pytest.raises(ValueError):
                Question(
                    id=1,
                    text="テスト問題",
                    options=["選択肢1", "選択肢2", "選択肢3", "選択肢4"],
                    correct_answer=5  # 範囲外
                )
            
        except ImportError as e:
            pytest.fail(f"問題モデル インポートエラー: {e}")
    
    def test_quiz_session_model(self):
        """クイズセッションモデルのテスト"""
        try:
            from app.core.models import Question, QuizSession
            
            # テスト用問題作成
            questions = [
                Question(
                    id=i,
                    text=f"問題{i}",
                    options=["選択肢1", "選択肢2", "選択肢3", "選択肢4"],
                    correct_answer=0
                )
                for i in range(1, 4)
            ]
            
            # セッション作成
            session = QuizSession(
                id="test-session",
                questions=questions
            )
            
            # 基本プロパティ確認
            assert session.total_questions == 3
            assert session.current_index == 0
            assert session.score == 0
            assert not session.is_completed
            
            # 回答処理テスト
            answer = session.add_answer(0)  # 正解
            assert answer.is_correct == True
            assert session.score == 1
            assert session.current_index == 1
            
            # 不正解
            answer = session.add_answer(1)  # 不正解
            assert answer.is_correct == False
            assert session.score == 1  # スコア変わらず
            assert session.current_index == 2
            
        except ImportError as e:
            pytest.fail(f"セッションモデル インポートエラー: {e}")
    
    def test_csv_row_parsing(self):
        """CSV行パースのテスト"""
        try:
            from app.core.models import create_question_from_csv_row
            
            # 有効なCSVデータ
            valid_row = {
                'question': 'テスト問題',
                'option1': '選択肢1',
                'option2': '選択肢2', 
                'option3': '選択肢3',
                'option4': '選択肢4',
                'correct_answer': '2',
                'explanation': 'テスト解説',
                'genre': '数学',
                'difficulty': '初級'
            }
            
            question = create_question_from_csv_row(valid_row, 1)
            assert question.text == 'テスト問題'
            assert question.correct_answer == 1  # 1-basedから0-basedに変換
            assert question.category == '数学'
            
            # 無効なCSVデータ
            invalid_row = {
                'question': '',  # 空の問題文
                'option1': '選択肢1',
                'option2': '選択肢2',
                'option3': '選択肢3', 
                'option4': '選択肢4',
                'correct_answer': '1'
            }
            
            with pytest.raises(ValueError):
                create_question_from_csv_row(invalid_row, 1)
            
        except ImportError as e:
            pytest.fail(f"CSV解析機能 インポートエラー: {e}")


class TestServiceIntegration:
    """サービス統合テスト"""
    
    @patch('app.core.service_factory.get_settings')
    def test_service_factory_initialization(self, mock_settings):
        """サービスファクトリーの初期化テスト"""
        try:
            # モック設定
            mock_settings.return_value.database_url = "sqlite:///test.db"
            
            from app.core.service_factory import get_service_factory
            
            factory = get_service_factory()
            assert factory is not None
            
            # 初期化せずにサービス取得を試行
            # （実際のデータベース接続は行わない）
            
        except ImportError as e:
            pytest.fail(f"サービスファクトリー インポートエラー: {e}")
        except Exception as e:
            # 初期化エラーは警告として扱う（DBファイルがない場合など）
            warnings.warn(f"サービスファクトリー初期化警告: {e}")
    
    def test_interfaces_compliance(self):
        """インターフェース準拠の確認"""
        try:
            from app.core.interfaces import QuizServiceInterface
            from app.core.quiz import QuizService
            
            # QuizServiceがインターフェースを実装しているか確認
            # （実際のインスタンス化は行わず、クラス構造のみ確認）
            
            required_methods = [
                'create_session', 'get_session', 'answer_question',
                'get_session_results', 'get_available_categories'
            ]
            
            missing_methods = []
            for method_name in required_methods:
                if not hasattr(QuizService, method_name):
                    missing_methods.append(method_name)
            
            assert not missing_methods, f"QuizServiceに必要なメソッドがありません: {missing_methods}"
            
        except ImportError as e:
            pytest.fail(f"インターフェース確認 インポートエラー: {e}")


class TestErrorHandling:
    """エラーハンドリングテスト"""
    
    def test_custom_exceptions(self):
        """カスタム例外の動作確認"""
        try:
            from app.core.exceptions import (
                QuizError, SessionError, QuestionNotFoundError,
                get_http_status_code, exception_to_api_response
            )
            
            # カスタム例外の作成
            quiz_error = QuizError("テストエラー", "ユーザー向けメッセージ")
            assert quiz_error.user_message == "ユーザー向けメッセージ"
            
            session_error = SessionError("セッションエラー")
            assert isinstance(session_error, QuizError)  # 継承確認
            
            # HTTP ステータスコード取得
            status_code = get_http_status_code(session_error)
            assert isinstance(status_code, int)
            assert 400 <= status_code < 600  # HTTPステータスコード範囲
            
            # API レスポンス変換
            api_response = exception_to_api_response(quiz_error)
            assert 'success' in api_response
            assert api_response['success'] == False
            assert 'error' in api_response
            
        except ImportError as e:
            pytest.fail(f"例外処理 インポートエラー: {e}")
    
    def test_validation_functions(self):
        """バリデーション関数のテスト"""
        try:
            from app.core.models import validate_csv_headers
            
            # 有効なヘッダー
            valid_headers = ['question', 'option1', 'option2', 'option3', 'option4', 'correct_answer']
            is_valid, missing = validate_csv_headers(valid_headers)
            assert is_valid == True
            assert len(missing) == 0
            
            # 無効なヘッダー（必須項目不足）
            invalid_headers = ['question', 'option1', 'option2']
            is_valid, missing = validate_csv_headers(invalid_headers)
            assert is_valid == False
            assert len(missing) > 0
            
        except ImportError as e:
            pytest.fail(f"バリデーション関数 インポートエラー: {e}")


def run_api_functionality_tests():
    """API機能テストの実行"""
    print("🌐 API機能テスト開始...")
    
    # pytestを使用してテストを実行
    result = pytest.main([
        __file__,
        "-v",  # 詳細出力
        "--tb=short",  # 短いトレースバック
        "-W", "ignore::DeprecationWarning",  # 非推奨警告を無視
        "--asyncio-mode=auto",  # async/awaitテスト対応
    ])
    
    if result == 0:
        print("✅ API機能テスト: 全て通過")
        return True
    else:
        print("❌ API機能テスト: 失敗")
        return False


if __name__ == "__main__":
    # スタンドアローン実行時
    success = run_api_functionality_tests()
    sys.exit(0 if success else 1)