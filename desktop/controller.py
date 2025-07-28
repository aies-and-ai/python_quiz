"""
デスクトップアプリケーション コントローラー
UIとビジネスロジックの仲介
"""

from typing import Optional, Dict, Any, List
from app.core.service_factory import get_quiz_service, get_csv_importer
from app.core.exceptions import QuizError
from app.config import get_settings
from utils.logger import get_logger


class DesktopController:
    """デスクトップアプリケーション用コントローラー"""
    
    def __init__(self):
        """初期化"""
        self.logger = get_logger()
        self.settings = get_settings()
        self.quiz_service = get_quiz_service()
        self.csv_importer = get_csv_importer()
        
        self.current_session_id: Optional[str] = None
        self.ui_callbacks = {}
        
        self.logger.info("デスクトップコントローラー初期化完了")
    
    def set_ui_callbacks(self, callbacks: Dict[str, Any]) -> None:
        """UIコールバックを設定"""
        self.ui_callbacks = callbacks
    
    # === メインメニュー関連 ===
    
    def get_app_info(self) -> Dict[str, Any]:
        """アプリケーション情報を取得"""
        try:
            question_count = self.quiz_service.get_question_count()
            categories = self.quiz_service.get_available_categories()
            difficulties = self.quiz_service.get_available_difficulties()
            stats = self.quiz_service.get_statistics()
            
            return {
                'question_count': question_count,
                'categories': categories,
                'difficulties': difficulties,
                'total_sessions': stats.total_sessions,
                'best_score': stats.best_score,
                'best_accuracy': stats.best_accuracy,
                'has_questions': question_count > 0
            }
        except Exception as e:
            self.logger.error(f"アプリ情報取得エラー: {e}")
            return {
                'question_count': 0,
                'categories': [],
                'difficulties': [],
                'has_questions': False,
                'error': str(e)
            }
    
    def start_new_quiz(self, 
                      question_count: Optional[int] = None,
                      category: Optional[str] = None,
                      difficulty: Optional[str] = None) -> bool:
        """新しいクイズを開始"""
        try:
            # 既存セッションがあれば終了
            if self.current_session_id:
                self.abandon_current_session()
            
            # デフォルト値の設定
            if question_count is None:
                question_count = self.settings.default_question_count
            
            # セッション作成
            session = self.quiz_service.create_session(
                question_count=question_count,
                category=category,
                difficulty=difficulty,
                shuffle=self.settings.shuffle_questions
            )
            
            self.current_session_id = session.id
            
            self.logger.info(f"新しいクイズ開始: {session.id} ({session.total_questions}問)")
            
            # UIに最初の問題を表示
            self._show_current_question()
            
            return True
            
        except Exception as e:
            self.logger.error(f"クイズ開始エラー: {e}")
            self._show_error(f"クイズの開始に失敗しました: {str(e)}")
            return False
    
    # === クイズ進行関連 ===
    
    def _show_current_question(self) -> None:
        """現在の問題をUIに表示"""
        if not self.current_session_id:
            return
        
        try:
            question = self.quiz_service.get_current_question(self.current_session_id)
            progress = self.quiz_service.get_session_progress(self.current_session_id)
            
            if question:
                # 選択肢シャッフル（設定で有効な場合）
                if self.settings.shuffle_options:
                    question = self.quiz_service.shuffle_options(question)
                
                # UIコールバック実行
                if 'show_question' in self.ui_callbacks:
                    self.ui_callbacks['show_question'](question, progress)
            else:
                # 問題がない場合は結果表示
                self._show_quiz_results()
                
        except Exception as e:
            self.logger.error(f"問題表示エラー: {e}")
            self._show_error(f"問題の表示に失敗しました: {str(e)}")
    
    def answer_question(self, selected_option: int) -> None:
        """問題に回答"""
        if not self.current_session_id:
            self._show_error("セッションが開始されていません")
            return
        
        try:
            result = self.quiz_service.answer_question(self.current_session_id, selected_option)
            
            # 回答結果をUIに表示
            if 'show_answer_result' in self.ui_callbacks:
                self.ui_callbacks['show_answer_result'](result)
            
            self.logger.info(f"回答処理完了: {'正解' if result['is_correct'] else '不正解'}")
            
        except Exception as e:
            self.logger.error(f"回答処理エラー: {e}")
            self._show_error(f"回答の処理に失敗しました: {str(e)}")
    
    def next_question(self) -> None:
        """次の問題へ進む"""
        if not self.current_session_id:
            return
        
        try:
            progress = self.quiz_service.get_session_progress(self.current_session_id)
            
            if progress['is_completed']:
                self._show_quiz_results()
            else:
                self._show_current_question()
                
        except Exception as e:
            self.logger.error(f"次の問題エラー: {e}")
            self._show_error(f"次の問題への移動に失敗しました: {str(e)}")
    
    def _show_quiz_results(self) -> None:
        """クイズ結果を表示"""
        if not self.current_session_id:
            return
        
        try:
            results = self.quiz_service.get_session_results(self.current_session_id)
            
            # UIコールバック実行
            if 'show_results' in self.ui_callbacks:
                self.ui_callbacks['show_results'](results)
            
            self.logger.info(f"結果表示: {results['score']}/{results['total_questions']}")
            
        except Exception as e:
            self.logger.error(f"結果表示エラー: {e}")
            self._show_error(f"結果の表示に失敗しました: {str(e)}")
    
    # === 結果画面関連 ===
    
    def restart_quiz(self) -> None:
        """クイズを最初から再開"""
        if self.current_session_id:
            self.abandon_current_session()
        
        # メインメニューに戻る
        if 'show_main_menu' in self.ui_callbacks:
            self.ui_callbacks['show_main_menu']()
    
    def retry_wrong_questions(self) -> bool:
        """間違えた問題のみで再挑戦"""
        if not self.current_session_id:
            self._show_error("セッションが見つかりません")
            return False
        
        try:
            original_session_id = self.current_session_id
            
            # 再挑戦セッション作成
            retry_session = self.quiz_service.create_retry_session(original_session_id)
            self.current_session_id = retry_session.id
            
            self.logger.info(f"再挑戦セッション開始: {retry_session.total_questions}問")
            
            # 最初の問題を表示
            self._show_current_question()
            
            return True
            
        except Exception as e:
            self.logger.error(f"再挑戦エラー: {e}")
            self._show_error(f"再挑戦の開始に失敗しました: {str(e)}")
            return False
    
    # === 履歴・統計関連 ===
    
    def show_statistics(self) -> None:
        """統計情報を表示"""
        try:
            stats = self.quiz_service.get_statistics()
            
            stats_data = {
                'total_sessions': stats.total_sessions,
                'total_questions_answered': stats.total_questions_answered,
                'total_correct_answers': stats.total_correct_answers,
                'overall_accuracy': stats.overall_accuracy,
                'best_score': stats.best_score,
                'best_accuracy': stats.best_accuracy
            }
            
            if 'show_statistics' in self.ui_callbacks:
                self.ui_callbacks['show_statistics'](stats_data)
            
        except Exception as e:
            self.logger.error(f"統計表示エラー: {e}")
            self._show_error(f"統計情報の取得に失敗しました: {str(e)}")
    
    # === 設定関連 ===
    
    def show_settings(self) -> None:
        """設定画面を表示"""
        current_settings = {
            'shuffle_questions': self.settings.shuffle_questions,
            'shuffle_options': self.settings.shuffle_options,
            'default_question_count': self.settings.default_question_count,
            'window_width': self.settings.window_width,
            'window_height': self.settings.window_height,
            'debug': self.settings.debug
        }
        
        if 'show_settings' in self.ui_callbacks:
            self.ui_callbacks['show_settings'](current_settings)
    
    def save_settings(self, new_settings: Dict[str, Any]) -> bool:
        """設定を保存"""
        try:
            # 設定を更新
            for key, value in new_settings.items():
                if hasattr(self.settings, key):
                    setattr(self.settings, key, value)
            
            # 設定ファイルに保存
            self.settings.save()
            
            self.logger.info("設定保存完了")
            return True
            
        except Exception as e:
            self.logger.error(f"設定保存エラー: {e}")
            self._show_error(f"設定の保存に失敗しました: {str(e)}")
            return False
    
    # === CSVインポート関連 ===
    
    def import_csv_file(self, csv_path: str) -> bool:
        """CSVファイルをインポート"""
        try:
            self.logger.info(f"CSVインポート開始: {csv_path}")
            
            result = self.csv_importer.import_from_csv(csv_path)
            
            success_message = f"インポート完了:\n"
            success_message += f"成功: {result['imported_count']}問\n"
            success_message += f"スキップ: {result['skipped_count']}問\n"
            success_message += f"エラー: {result['error_count']}問"
            
            if result['imported_count'] > 0:
                self._show_info(success_message)
                return True
            else:
                self._show_error(f"インポートに失敗しました:\n{success_message}")
                return False
                
        except Exception as e:
            self.logger.error(f"CSVインポートエラー: {e}")
            self._show_error(f"CSVファイルのインポートに失敗しました: {str(e)}")
            return False
    
    # === セッション管理 ===
    
    def abandon_current_session(self) -> None:
        """現在のセッションを中断"""
        if self.current_session_id:
            try:
                self.quiz_service.abandon_session(self.current_session_id)
                self.logger.info(f"セッション中断: {self.current_session_id}")
            except Exception as e:
                self.logger.warning(f"セッション中断エラー: {e}")
            finally:
                self.current_session_id = None
    
    def get_current_session_info(self) -> Optional[Dict[str, Any]]:
        """現在のセッション情報を取得"""
        if not self.current_session_id:
            return None
        
        try:
            return self.quiz_service.get_session_progress(self.current_session_id)
        except Exception as e:
            self.logger.error(f"セッション情報取得エラー: {e}")
            return None
    
    # === ユーティリティメソッド ===
    
    def _show_error(self, message: str) -> None:
        """エラーメッセージをUIに表示"""
        if 'show_error' in self.ui_callbacks:
            self.ui_callbacks['show_error'](message)
        else:
            self.logger.error(f"UI Error: {message}")
    
    def _show_info(self, message: str) -> None:
        """情報メッセージをUIに表示"""
        if 'show_info' in self.ui_callbacks:
            self.ui_callbacks['show_info'](message)
        else:
            self.logger.info(f"UI Info: {message}")
    
    def quit_application(self) -> None:
        """アプリケーション終了処理"""
        self.logger.info("アプリケーション終了処理開始")
        
        # 現在のセッションを保存
        self.abandon_current_session()
        
        # サービスのシャットダウン
        from app.core.service_factory import shutdown_services
        shutdown_services()
        
        self.logger.info("アプリケーション終了処理完了")
    
    def validate_quiz_start_params(self, 
                                  question_count: int,
                                  category: Optional[str] = None,
                                  difficulty: Optional[str] = None) -> tuple[bool, Optional[str]]:
        """クイズ開始パラメータの妥当性をチェック"""
        try:
            # 問題数チェック
            if question_count <= 0:
                return False, "問題数は1以上である必要があります"
            
            if question_count > 100:
                return False, "問題数は100以下である必要があります"
            
            # 利用可能な問題数チェック
            available_count = self.quiz_service.get_question_count(category, difficulty)
            if available_count == 0:
                return False, "指定された条件に合う問題が見つかりません"
            
            if question_count > available_count:
                return False, f"利用可能な問題数({available_count}問)を超えています"
            
            return True, None
            
        except Exception as e:
            return False, f"パラメータ検証エラー: {str(e)}"