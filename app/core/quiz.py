"""
クイズサービス
ビジネスロジックの中核（インポートエラー修正版）
"""

import random
import sys
import os
from pathlib import Path
from typing import List, Optional, Dict, Any

# パッケージルートをパスに追加（相対インポートエラー回避）
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# 絶対インポートで修正
from app.core.models import Question, QuizSession, Answer, QuizStatistics
from app.core.database import DatabaseService
from app.core.exceptions import SessionError, QuestionNotFoundError, InvalidAnswerError
from utils.logger import get_logger


class QuizService:
    """クイズ管理サービス"""
    
    def __init__(self, db_service: DatabaseService):
        """初期化"""
        self.db = db_service
        self.logger = get_logger()
        self._active_sessions: Dict[str, QuizSession] = {}
    
    def create_session(self, 
                      question_count: int = 10,
                      category: Optional[str] = None,
                      difficulty: Optional[str] = None,
                      shuffle: bool = True) -> QuizSession:
        """
        新しいクイズセッションを作成
        
        Args:
            question_count: 出題する問題数
            category: カテゴリ絞り込み
            difficulty: 難易度絞り込み
            shuffle: 問題をシャッフルするか
            
        Returns:
            作成されたクイズセッション
        """
        try:
            # 問題を取得
            questions = self.db.get_questions(
                category=category,
                difficulty=difficulty,
                limit=question_count,
                shuffle=shuffle
            )
            
            if not questions:
                raise SessionError("利用可能な問題が見つかりません")
            
            if len(questions) < question_count:
                self.logger.warning(f"要求された問題数({question_count})より少ない問題数({len(questions)})で開始します")
            
            # セッション作成
            session = QuizSession(
                id="",  # __post_init__で自動生成
                questions=questions
            )
            
            # アクティブセッションに追加
            self._active_sessions[session.id] = session
            
            self.logger.info(f"クイズセッション作成: {session.id} ({len(questions)}問)")
            
            return session
            
        except Exception as e:
            self.logger.error(f"セッション作成エラー: {e}")
            if isinstance(e, SessionError):
                raise
            raise SessionError(f"セッションの作成に失敗しました: {str(e)}")
    
    def get_session(self, session_id: str) -> QuizSession:
        """セッションを取得"""
        if session_id not in self._active_sessions:
            raise SessionError(f"セッションが見つかりません: {session_id}")
        
        return self._active_sessions[session_id]
    
    def get_current_question(self, session_id: str) -> Optional[Question]:
        """現在の問題を取得"""
        session = self.get_session(session_id)
        return session.get_current_question()
    
    def answer_question(self, session_id: str, selected_option: int) -> Dict[str, Any]:
        """
        問題に回答
        
        Args:
            session_id: セッションID
            selected_option: 選択した選択肢（0-3）
            
        Returns:
            回答結果の詳細情報
        """
        try:
            session = self.get_session(session_id)
            
            # 現在の問題を取得
            current_question = session.get_current_question()
            if not current_question:
                raise SessionError("これ以上問題がありません")
            
            # 選択肢の妥当性チェック
            if not 0 <= selected_option <= 3:
                raise InvalidAnswerError(selected_option)
            
            # 回答を追加
            answer = session.add_answer(selected_option)
            
            # 結果情報を作成
            result = {
                'session_id': session_id,
                'question': current_question,
                'selected_option': selected_option,
                'correct_answer': current_question.correct_answer,
                'is_correct': answer.is_correct,
                'explanation': current_question.explanation,
                'current_score': session.score,
                'total_questions': session.total_questions,
                'current_index': session.current_index,
                'accuracy': session.accuracy,
                'is_session_completed': session.is_completed
            }
            
            # セッション完了時の処理
            if session.is_completed:
                self._handle_session_completion(session)
            
            self.logger.info(f"回答処理完了: {session_id} - {'正解' if answer.is_correct else '不正解'}")
            
            return result
            
        except (SessionError, InvalidAnswerError):
            raise
        except Exception as e:
            self.logger.error(f"回答処理エラー: {e}")
            raise SessionError(f"回答の処理に失敗しました: {str(e)}")
    
    def _handle_session_completion(self, session: QuizSession) -> None:
        """セッション完了時の処理"""
        try:
            # データベースに保存
            self.db.save_session(session)
            
            # アクティブセッションから削除
            if session.id in self._active_sessions:
                del self._active_sessions[session.id]
            
            self.logger.info(f"セッション完了: {session.id} - スコア: {session.score}/{session.total_questions}")
            
        except Exception as e:
            self.logger.error(f"セッション完了処理エラー: {e}")
    
    def get_session_results(self, session_id: str) -> Dict[str, Any]:
        """セッション結果を取得"""
        try:
            session = self.get_session(session_id)
            
            if not session.is_completed:
                raise SessionError("セッションがまだ完了していません")
            
            # 基本結果
            results = session.get_results_summary()
            
            # 間違えた問題の詳細
            wrong_answers = session.get_wrong_answers()
            results['wrong_questions'] = wrong_answers
            
            # カテゴリ別・難易度別の統計
            results['category_stats'] = self._calculate_category_stats(session)
            results['difficulty_stats'] = self._calculate_difficulty_stats(session)
            
            return results
            
        except SessionError:
            raise
        except Exception as e:
            self.logger.error(f"結果取得エラー: {e}")
            raise SessionError(f"結果の取得に失敗しました: {str(e)}")
    
    def _calculate_category_stats(self, session: QuizSession) -> Dict[str, Dict[str, int]]:
        """カテゴリ別統計を計算"""
        stats = {}
        
        for i, question in enumerate(session.questions):
            category = question.category or "未分類"
            
            if category not in stats:
                stats[category] = {'total': 0, 'correct': 0}
            
            stats[category]['total'] += 1
            
            # 対応する回答が正解かチェック
            if i < len(session.answers) and session.answers[i].is_correct:
                stats[category]['correct'] += 1
        
        return stats
    
    def _calculate_difficulty_stats(self, session: QuizSession) -> Dict[str, Dict[str, int]]:
        """難易度別統計を計算"""
        stats = {}
        
        for i, question in enumerate(session.questions):
            difficulty = question.difficulty or "未設定"
            
            if difficulty not in stats:
                stats[difficulty] = {'total': 0, 'correct': 0}
            
            stats[difficulty]['total'] += 1
            
            # 対応する回答が正解かチェック
            if i < len(session.answers) and session.answers[i].is_correct:
                stats[difficulty]['correct'] += 1
        
        return stats
    
    def get_session_progress(self, session_id: str) -> Dict[str, Any]:
        """セッションの進行状況を取得"""
        try:
            session = self.get_session(session_id)
            
            return {
                'session_id': session_id,
                'current_index': session.current_index,
                'total_questions': session.total_questions,
                'score': session.score,
                'accuracy': session.accuracy,
                'progress_percentage': session.progress_percentage,
                'is_completed': session.is_completed,
                'remaining_questions': session.total_questions - session.current_index
            }
            
        except SessionError:
            raise
        except Exception as e:
            self.logger.error(f"進行状況取得エラー: {e}")
            raise SessionError(f"進行状況の取得に失敗しました: {str(e)}")
    
    def abandon_session(self, session_id: str) -> None:
        """セッションを中断"""
        try:
            if session_id in self._active_sessions:
                session = self._active_sessions[session_id]
                
                # 途中終了として記録（オプション）
                if session.current_index > 0:
                    self.db.save_session(session)
                
                del self._active_sessions[session_id]
                self.logger.info(f"セッション中断: {session_id}")
            
        except Exception as e:
            self.logger.error(f"セッション中断エラー: {e}")
    
    def get_available_categories(self) -> List[str]:
        """利用可能なカテゴリ一覧を取得"""
        return self.db.get_categories()
    
    def get_available_difficulties(self) -> List[str]:
        """利用可能な難易度一覧を取得"""
        return self.db.get_difficulties()
    
    def get_statistics(self) -> QuizStatistics:
        """統計情報を取得"""
        return self.db.get_statistics()
    
    def get_question_count(self, 
                          category: Optional[str] = None,
                          difficulty: Optional[str] = None) -> int:
        """条件に合う問題数を取得"""
        try:
            return self.db.get_question_count(category, difficulty)
        except Exception as e:
            self.logger.error(f"問題数取得エラー: {e}")
            return 0
    
    def create_retry_session(self, original_session_id: str) -> QuizSession:
        """
        間違えた問題のみで再挑戦セッションを作成
        
        Args:
            original_session_id: 元のセッションID
            
        Returns:
            間違えた問題のみのセッション
        """
        try:
            # 元のセッションから間違えた問題を取得
            original_session = self.get_session(original_session_id)
            
            if not original_session.is_completed:
                raise SessionError("セッションが完了していません")
            
            wrong_answers = original_session.get_wrong_answers()
            
            if not wrong_answers:
                raise SessionError("間違えた問題がありません")
            
            # 間違えた問題のみでセッション作成
            wrong_questions = [wa['question'] for wa in wrong_answers]
            
            retry_session = QuizSession(
                id="",  # 新しいIDで作成
                questions=wrong_questions
            )
            
            self._active_sessions[retry_session.id] = retry_session
            
            self.logger.info(f"再挑戦セッション作成: {retry_session.id} ({len(wrong_questions)}問)")
            
            return retry_session
            
        except SessionError:
            raise
        except Exception as e:
            self.logger.error(f"再挑戦セッション作成エラー: {e}")
            raise SessionError(f"再挑戦セッションの作成に失敗しました: {str(e)}")
    
    def shuffle_options(self, question: Question) -> Question:
        """
        問題の選択肢をシャッフル
        
        Args:
            question: 元の問題
            
        Returns:
            選択肢がシャッフルされた新しい問題
        """
        try:
            # 既存のシャッフル関数を使用
            from app.core.models import shuffle_question_options
            return shuffle_question_options(question)
            
        except Exception as e:
            self.logger.error(f"選択肢シャッフルエラー: {e}")
            # エラー時は元の問題をそのまま返す
            return question