# tests/test_integration.py
"""
統合テスト（End-to-End）
アプリケーション全体のワークフローとユーザーシナリオをテスト
"""

import os
import sys
import pytest
import tempfile
import sqlite3
from pathlib import Path
from unittest.mock import patch, Mock
import json
import csv
import warnings

# プロジェクトルートを取得
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "backend"))


class TestFullQuizWorkflow:
    """完全なクイズワークフローテスト"""
    
    @pytest.fixture
    def temp_database(self):
        """テスト用一時データベース"""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_file:
            db_path = tmp_file.name
        
        yield db_path
        
        # クリーンアップ
        try:
            os.unlink(db_path)
        except FileNotFoundError:
            pass
    
    @pytest.fixture
    def sample_questions_csv(self):
        """テスト用サンプル問題CSV"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as tmp_file:
            writer = csv.writer(tmp_file)
            
            # ヘッダー
            writer.writerow([
                'question', 'option1', 'option2', 'option3', 'option4', 
                'correct_answer', 'explanation', 'genre', 'difficulty'
            ])
            
            # サンプル問題
            sample_questions = [
                ['2 + 2 = ?', '3', '4', '5', '6', '2', '2 + 2 = 4です', '数学', '初級'],
                ['日本の首都は？', '東京', '大阪', '京都', '名古屋', '1', '日本の首都は東京です', '地理', '初級'],
                ['1 + 1 = ?', '1', '2', '3', '4', '2', '1 + 1 = 2です', '数学', '初級'],
                ['富士山の標高は？', '3776m', '3000m', '4000m', '3500m', '1', '富士山は3776mです', '地理', '中級'],
                ['3 × 3 = ?', '6', '9', '12', '15', '2', '3 × 3 = 9です', '数学', '中級']
            ]
            
            for question in sample_questions:
                writer.writerow(question)
        
        yield tmp_file.name
        
        # クリーンアップ
        try:
            os.unlink(tmp_file.name)
        except FileNotFoundError:
            pass
    
    def test_csv_import_workflow(self, temp_database, sample_questions_csv):
        """CSV インポートワークフローテスト"""
        try:
            # 設定をモック
            with patch('app.config.get_settings') as mock_settings:
                mock_settings.return_value.database_url = f"sqlite:///{temp_database}"
                mock_settings.return_value.log_level = "INFO"
                
                # CSVインポートサービスをテスト
                from app.core.service_factory import get_service_factory
                
                factory = get_service_factory()
                factory.initialize(f"sqlite:///{temp_database}")
                
                csv_importer = factory.get_csv_importer()
                
                # CSVファイルインポート
                result = csv_importer.import_from_csv(sample_questions_csv, overwrite=False)
                
                # インポート結果確認
                assert result['success'] == True, f"インポート失敗: {result['errors']}"
                assert result['imported_count'] > 0, "問題がインポートされていません"
                assert result['imported_count'] == 5, f"期待される問題数と異なります: {result['imported_count']}/5"
                
                # データベースから問題を取得して確認
                db_service = factory.get_database_service()
                questions = db_service.get_questions()
                
                assert len(questions) == 5, f"データベースの問題数が異なります: {len(questions)}/5"
                
                # 問題内容の確認
                math_questions = db_service.get_questions(category="数学")
                geo_questions = db_service.get_questions(category="地理")
                
                assert len(math_questions) == 3, f"数学問題数が異なります: {len(math_questions)}/3"
                assert len(geo_questions) == 2, f"地理問題数が異なります: {len(geo_questions)}/2"
                
                print("✅ CSV インポートワークフロー成功")
                
        except ImportError as e:
            pytest.skip(f"必要なモジュールが未インストール: {e}")
        except Exception as e:
            pytest.fail(f"CSV インポートワークフローエラー: {e}")
    
    def test_complete_quiz_session_workflow(self, temp_database, sample_questions_csv):
        """完全なクイズセッションワークフローテスト"""
        try:
            with patch('app.config.get_settings') as mock_settings:
                mock_settings.return_value.database_url = f"sqlite:///{temp_database}"
                mock_settings.return_value.log_level = "INFO"
                
                from app.core.service_factory import get_service_factory
                
                # サービス初期化
                factory = get_service_factory()
                factory.initialize(f"sqlite:///{temp_database}")
                
                # 問題データのインポート
                csv_importer = factory.get_csv_importer()
                import_result = csv_importer.import_from_csv(sample_questions_csv, overwrite=False)
                assert import_result['success'], "問題インポートに失敗"
                
                # クイズサービス取得
                quiz_service = factory.get_quiz_service()
                
                # 1. セッション作成
                session = quiz_service.create_session(
                    question_count=3,
                    category=None,  # 全カテゴリ
                    difficulty=None,  # 全難易度
                    shuffle=False  # 順序固定でテスト
                )
                
                assert session.total_questions == 3, f"問題数が異なります: {session.total_questions}/3"
                assert session.current_index == 0, "初期インデックスが正しくありません"
                assert session.score == 0, "初期スコアが正しくありません"
                assert not session.is_completed, "初期状態で完了になっています"
                
                # 2. 問題取得と回答のサイクル
                correct_answers = 0
                
                for i in range(3):
                    # 現在の問題取得
                    current_question = quiz_service.get_current_question(session.id)
                    assert current_question is not None, f"問題{i+1}が取得できません"
                    assert len(current_question.options) == 4, "選択肢数が正しくありません"
                    
                    # 進行状況確認
                    progress = quiz_service.get_session_progress(session.id)
                    assert progress['current_index'] == i, f"進行状況が正しくありません: {progress['current_index']}/{i}"
                    
                    # 回答送信（正解を選択）
                    answer_result = quiz_service.answer_question(session.id, current_question.correct_answer)
                    
                    assert answer_result['is_correct'] == True, f"問題{i+1}で正解判定が間違っています"
                    assert answer_result['current_score'] == i + 1, f"スコアが正しくありません: {answer_result['current_score']}/{i+1}"
                    
                    correct_answers += 1
                
                # 3. セッション完了確認
                final_progress = quiz_service.get_session_progress(session.id)
                assert final_progress['is_completed'] == True, "セッションが完了していません"
                assert final_progress['score'] == 3, f"最終スコアが正しくありません: {final_progress['score']}/3"
                assert final_progress['accuracy'] == 100.0, f"正答率が正しくありません: {final_progress['accuracy']}/100.0"
                
                # 4. 結果取得
                results = quiz_service.get_session_results(session.id)
                assert results['total_questions'] == 3, "結果の問題数が正しくありません"
                assert results['score'] == 3, "結果のスコアが正しくありません"
                assert results['accuracy'] == 100.0, "結果の正答率が正しくありません"
                assert len(results['wrong_questions']) == 0, "間違えた問題があります"
                
                print("✅ 完全なクイズセッションワークフロー成功")
                
        except ImportError as e:
            pytest.skip(f"必要なモジュールが未インストール: {e}")
        except Exception as e:
            pytest.fail(f"クイズセッションワークフローエラー: {e}")
    
    def test_partial_correct_quiz_workflow(self, temp_database, sample_questions_csv):
        """部分正解のクイズワークフローテスト"""
        try:
            with patch('app.config.get_settings') as mock_settings:
                mock_settings.return_value.database_url = f"sqlite:///{temp_database}"
                
                from app.core.service_factory import get_service_factory
                
                factory = get_service_factory()
                factory.initialize(f"sqlite:///{temp_database}")
                
                # 問題インポート
                csv_importer = factory.get_csv_importer()
                csv_importer.import_from_csv(sample_questions_csv, overwrite=False)
                
                quiz_service = factory.get_quiz_service()
                
                # セッション作成
                session = quiz_service.create_session(question_count=3, shuffle=False)
                
                # 最初の問題: 正解
                question1 = quiz_service.get_current_question(session.id)
                result1 = quiz_service.answer_question(session.id, question1.correct_answer)
                assert result1['is_correct'] == True
                
                # 2番目の問題: 不正解
                question2 = quiz_service.get_current_question(session.id)
                wrong_answer = (question2.correct_answer + 1) % 4  # 正解以外の選択肢
                result2 = quiz_service.answer_question(session.id, wrong_answer)
                assert result2['is_correct'] == False
                
                # 3番目の問題: 正解
                question3 = quiz_service.get_current_question(session.id)
                result3 = quiz_service.answer_question(session.id, question3.correct_answer)
                assert result3['is_correct'] == True
                
                # 最終結果確認
                results = quiz_service.get_session_results(session.id)
                assert results['score'] == 2, f"スコアが正しくありません: {results['score']}/2"
                assert results['wrong_count'] == 1, f"間違い数が正しくありません: {results['wrong_count']}/1"
                assert len(results['wrong_questions']) == 1, "間違えた問題リストが正しくありません"
                
                # 間違えた問題の詳細確認
                wrong_question = results['wrong_questions'][0]
                assert wrong_question['selected_option'] == wrong_answer, "選択した選択肢が記録されていません"
                assert wrong_question['correct_answer'] == question2.correct_answer, "正解が記録されていません"
                
                print("✅ 部分正解クイズワークフロー成功")
                
        except ImportError as e:
            pytest.skip(f"必要なモジュールが未インストール: {e}")
        except Exception as e:
            pytest.fail(f"部分正解ワークフローエラー: {e}")


class TestAdminCLIIntegration:
    """管理CLI統合テスト"""
    
    @pytest.fixture
    def temp_csv_file(self):
        """テスト用CSVファイル"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as tmp_file:
            writer = csv.writer(tmp_file)
            writer.writerow(['question', 'option1', 'option2', 'option3', 'option4', 'correct_answer'])
            writer.writerow(['テスト問題', '選択肢1', '選択肢2', '選択肢3', '選択肢4', '2'])
        
        yield tmp_file.name
        
        try:
            os.unlink(tmp_file.name)
        except FileNotFoundError:
            pass
    
    def test_admin_cli_structure(self):
        """Admin CLI の構造確認"""
        try:
            # admin.py ファイルの存在確認
            admin_file = PROJECT_ROOT / "admin.py"
            assert admin_file.exists(), "admin.py が見つかりません"
            
            # ファイル内容の基本構造確認
            with open(admin_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            required_elements = [
                'class AdminCLI',
                'def import_csv',
                'def show_database_info',
                'def main(',
                'if __name__ == "__main__"'
            ]
            
            missing_elements = []
            for element in required_elements:
                if element not in content:
                    missing_elements.append(element)
            
            assert not missing_elements, f"admin.py に必要な要素がありません: {missing_elements}"
            
        except Exception as e:
            pytest.fail(f"Admin CLI 構造確認エラー: {e}")
    
    def test_admin_import_functionality(self, temp_csv_file):
        """Admin CLI インポート機能テスト"""
        try:
            # 一時データベース
            with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_db:
                db_path = tmp_db.name
            
            # 設定をモック
            with patch('app.config.get_settings') as mock_settings:
                mock_settings.return_value.database_url = f"sqlite:///{db_path}"
                mock_settings.return_value.log_level = "INFO"
                
                # AdminCLI のインポート機能をテスト
                from admin import AdminCLI
                
                admin_cli = AdminCLI()
                
                # CSVインポート実行
                result = admin_cli.import_csv(temp_csv_file, overwrite=False)
                assert result == True, "CSV インポートが失敗しました"
                
                # データベース情報確認
                # （標準出力への出力なので、例外が発生しないことを確認）
                try:
                    admin_cli.show_database_info()
                except Exception as e:
                    pytest.fail(f"データベース情報表示エラー: {e}")
            
            # クリーンアップ
            try:
                os.unlink(db_path)
            except FileNotFoundError:
                pass
                
        except ImportError as e:
            pytest.skip(f"Admin CLI 未インストール: {e}")
        except Exception as e:
            pytest.fail(f"Admin CLI 機能テストエラー: {e}")


class TestDataConsistency:
    """データ整合性テスト"""
    
    def test_database_schema_creation(self):
        """データベーススキーマ作成テスト"""
        try:
            with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp_db:
                db_path = tmp_db.name
            
            # データベース接続とテーブル作成
            from database.connection import DatabaseConnection
            
            db_conn = DatabaseConnection(database_url=f"sqlite:///{db_path}")
            db_conn.initialize()
            
            # テーブル存在確認
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            expected_tables = ['questions', 'quiz_sessions', 'quiz_answers', 'user_history']
            missing_tables = []
            
            for table in expected_tables:
                if table not in tables:
                    missing_tables.append(table)
            
            conn.close()
            
            assert not missing_tables, f"期待されるテーブルが見つかりません: {missing_tables}"
            
            # クリーンアップ
            try:
                os.unlink(db_path)
            except FileNotFoundError:
                pass
                
        except ImportError as e:
            pytest.skip(f"データベース未インストール: {e}")
        except Exception as e:
            pytest.fail(f"データベーススキーマテストエラー: {e}")
    
    def test_data_persistence(self, temp_database, sample_questions_csv):
        """データ永続化テスト"""
        try:
            with patch('app.config.get_settings') as mock_settings:
                mock_settings.return_value.database_url = f"sqlite:///{temp_database}"
                
                from app.core.service_factory import get_service_factory
                
                # 最初のセッション: データ作成
                factory1 = get_service_factory()
                factory1.initialize(f"sqlite:///{temp_database}")
                
                csv_importer1 = factory1.get_csv_importer()
                result1 = csv_importer1.import_from_csv(sample_questions_csv)
                assert result1['success'], "データインポートに失敗"
                
                original_question_count = result1['imported_count']
                
                # ファクトリーをリセット（メモリキャッシュクリア）
                factory1.shutdown()
                
                # 2番目のセッション: データ読み込み
                factory2 = get_service_factory()
                factory2.initialize(f"sqlite:///{temp_database}")
                
                db_service2 = factory2.get_database_service()
                questions2 = db_service2.get_questions()
                
                assert len(questions2) == original_question_count, "データが永続化されていません"
                
                # データ内容の確認
                question_texts = [q.text for q in questions2]
                assert '2 + 2 = ?' in question_texts, "具体的な問題データが見つかりません"
                
                factory2.shutdown()
                
        except ImportError as e:
            pytest.skip(f"必要なモジュールが未インストール: {e}")
        except Exception as e:
            pytest.fail(f"データ永続化テストエラー: {e}")


class TestConcurrencyAndEdgeCases:
    """並行性とエッジケーステスト"""
    
    def test_multiple_sessions_isolation(self, temp_database, sample_questions_csv):
        """複数セッションの分離テスト"""
        try:
            with patch('app.config.get_settings') as mock_settings:
                mock_settings.return_value.database_url = f"sqlite:///{temp_database}"
                
                from app.core.service_factory import get_service_factory
                
                factory = get_service_factory()
                factory.initialize(f"sqlite:///{temp_database}")
                
                # 問題データインポート
                csv_importer = factory.get_csv_importer()
                csv_importer.import_from_csv(sample_questions_csv)
                
                quiz_service = factory.get_quiz_service()
                
                # 2つの独立したセッションを作成
                session1 = quiz_service.create_session(question_count=2, shuffle=False)
                session2 = quiz_service.create_session(question_count=2, shuffle=False)
                
                assert session1.id != session2.id, "セッションIDが重複しています"
                
                # セッション1で回答
                q1_s1 = quiz_service.get_current_question(session1.id)
                quiz_service.answer_question(session1.id, q1_s1.correct_answer)
                
                # セッション2の状態は影響を受けないことを確認
                progress2 = quiz_service.get_session_progress(session2.id)
                assert progress2['current_index'] == 0, "セッション2が影響を受けています"
                assert progress2['score'] == 0, "セッション2のスコアが変更されています"
                
                # セッション2で回答
                q1_s2 = quiz_service.get_current_question(session2.id)
                quiz_service.answer_question(session2.id, q1_s2.correct_answer)
                
                # セッション1の状態確認
                progress1 = quiz_service.get_session_progress(session1.id)
                assert progress1['current_index'] == 1, "セッション1の状態が変更されています"
                assert progress1['score'] == 1, "セッション1のスコアが変更されています"
                
        except ImportError as e:
            pytest.skip(f"必要なモジュールが未インストール: {e}")
        except Exception as e:
            pytest.fail(f"セッション分離テストエラー: {e}")
    
    def test_invalid_input_handling(self, temp_database, sample_questions_csv):
        """無効入力の処理テスト"""
        try:
            with patch('app.config.get_settings') as mock_settings:
                mock_settings.return_value.database_url = f"sqlite:///{temp_database}"
                
                from app.core.service_factory import get_service_factory
                from app.core.exceptions import SessionError, InvalidAnswerError
                
                factory = get_service_factory()
                factory.initialize(f"sqlite:///{temp_database}")
                
                csv_importer = factory.get_csv_importer()
                csv_importer.import_from_csv(sample_questions_csv)
                
                quiz_service = factory.get_quiz_service()
                session = quiz_service.create_session(question_count=1)
                
                # 無効な選択肢で回答
                with pytest.raises((InvalidAnswerError, ValueError)):
                    quiz_service.answer_question(session.id, 5)  # 範囲外
                
                with pytest.raises((InvalidAnswerError, ValueError)):
                    quiz_service.answer_question(session.id, -1)  # 負の値
                
                # 存在しないセッションID
                with pytest.raises(SessionError):
                    quiz_service.get_current_question("nonexistent-session-id")
                
        except ImportError as e:
            pytest.skip(f"必要なモジュールが未インストール: {e}")
        except Exception as e:
            pytest.fail(f"無効入力処理テストエラー: {e}")


def run_integration_tests():
    """統合テストの実行"""
    print("🔗 統合テスト開始...")
    
    # pytestを使用してテストを実行
    result = pytest.main([
        __file__,
        "-v",  # 詳細出力
        "--tb=short",  # 短いトレースバック
        "-W", "ignore::DeprecationWarning",  # 非推奨警告を無視
        "--maxfail=3",  # 3回失敗で停止
    ])
    
    if result == 0:
        print("✅ 統合テスト: 全て通過")
        return True
    else:
        print("❌ 統合テスト: 失敗")
        return False


if __name__ == "__main__":
    # スタンドアローン実行時
    success = run_integration_tests()
    sys.exit(0 if success else 1)