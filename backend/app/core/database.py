# app/core/database.py
"""
データベースサービス - 責任明確化版
データアクセス層に特化し、複数のインターフェースを実装
"""

import random
import sys
import os
from pathlib import Path
from typing import List, Optional, Dict, Any
from sqlalchemy import func, desc
from sqlalchemy.exc import IntegrityError, OperationalError

project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from app.core.models import Question, QuizSession, QuizStatistics
from app.core.interfaces import (
    QuestionRepositoryInterface,
    SessionRepositoryInterface,
    DatabaseServiceInterface
)
from app.core.exceptions import DatabaseError, QuestionNotFoundError
from utils.logger import get_logger


class DatabaseService(QuestionRepositoryInterface, SessionRepositoryInterface, DatabaseServiceInterface):
    """
    データベース操作サービス - 責任明確化版
    複数のリポジトリインターフェースを実装
    """
    
    def __init__(self, database_url: str):
        """初期化"""
        self.database_url = database_url
        self.logger = get_logger()
        self._db_connection = None
        self._ensure_connection()
    
    def _ensure_connection(self):
        """データベース接続を確保"""
        if self._db_connection is None:
            try:
                from database import get_database_connection
                self._db_connection = get_database_connection(self.database_url)
            except Exception as e:
                self.logger.error(f"Database connection failed: {e}")
                raise DatabaseError(f"データベース接続に失敗しました: {str(e)}")
    
    def _get_session(self):
        """データベースセッションを取得"""
        self._ensure_connection()
        return self._db_connection.get_session()
    
    # QuestionRepositoryInterface の実装
    
    def get_questions(self, 
                     category: Optional[str] = None,
                     difficulty: Optional[str] = None,
                     limit: Optional[int] = None,
                     shuffle: bool = False) -> List[Question]:
        """問題を取得"""
        try:
            from database import DatabaseQuestion
            
            with self._get_session() as session:
                query = session.query(DatabaseQuestion).filter(
                    DatabaseQuestion.is_active == True
                )
                
                if category:
                    query = query.filter(DatabaseQuestion.genre == category)
                
                if difficulty:
                    query = query.filter(DatabaseQuestion.difficulty == difficulty)
                
                if shuffle:
                    query = query.order_by(func.random())
                else:
                    query = query.order_by(DatabaseQuestion.id)
                
                if limit:
                    query = query.limit(limit)
                
                db_questions = query.all()
                
                questions = []
                for db_q in db_questions:
                    question = Question.from_database(db_q)
                    questions.append(question)
                
                return questions
                
        except Exception as e:
            self.logger.error(f"問題取得エラー: {e}")
            raise DatabaseError(f"問題の取得に失敗しました: {str(e)}")
    
    def get_question_by_id(self, question_id: int) -> Optional[Question]:
        """IDで問題を取得"""
        try:
            from database import DatabaseQuestion
            
            with self._get_session() as session:
                db_question = session.query(DatabaseQuestion).filter(
                    DatabaseQuestion.id == question_id,
                    DatabaseQuestion.is_active == True
                ).first()
                
                if db_question:
                    return Question.from_database(db_question)
                
                return None
                
        except Exception as e:
            self.logger.error(f"問題取得エラー (ID: {question_id}): {e}")
            return None
    
    def save_question(self, question: Question, csv_filename: str = None) -> Optional[Question]:
        """問題を保存"""
        try:
            from database import DatabaseQuestion
            
            with self._get_session() as session:
                db_question = DatabaseQuestion(
                    question=question.text,
                    options=question.options,
                    correct_answer=question.correct_answer,
                    explanation=question.explanation,
                    genre=question.category,
                    difficulty=question.difficulty,
                    csv_source_file=csv_filename
                )
                
                session.add(db_question)
                session.flush()
                
                question.id = db_question.id
                
                return question
                
        except IntegrityError as e:
            self.logger.warning(f"問題保存時の整合性エラー: {e}")
            raise DatabaseError("データの整合性エラーが発生しました")
        except Exception as e:
            self.logger.error(f"問題保存エラー: {e}")
            raise DatabaseError(f"問題の保存に失敗しました: {str(e)}")
    
    def find_question_by_text(self, question_text: str, csv_filename: str = None) -> Optional[Question]:
        """問題文で問題を検索"""
        try:
            from database import DatabaseQuestion
            
            with self._get_session() as session:
                query = session.query(DatabaseQuestion).filter(
                    DatabaseQuestion.question == question_text,
                    DatabaseQuestion.is_active == True
                )
                
                if csv_filename:
                    query = query.filter(DatabaseQuestion.csv_source_file == csv_filename)
                
                db_question = query.first()
                
                if db_question:
                    return Question.from_database(db_question)
                
                return None
                
        except Exception as e:
            self.logger.error(f"問題検索エラー: {e}")
            return None
    
    def get_categories(self) -> List[str]:
        """利用可能なカテゴリ一覧を取得"""
        try:
            from database import DatabaseQuestion
            
            with self._get_session() as session:
                categories = session.query(DatabaseQuestion.genre).filter(
                    DatabaseQuestion.is_active == True,
                    DatabaseQuestion.genre.isnot(None),
                    DatabaseQuestion.genre != ""
                ).distinct().all()
                
                return [cat[0] for cat in categories]
                
        except Exception as e:
            self.logger.error(f"カテゴリ取得エラー: {e}")
            return []
    
    def get_difficulties(self) -> List[str]:
        """利用可能な難易度一覧を取得"""
        try:
            from database import DatabaseQuestion
            
            with self._get_session() as session:
                difficulties = session.query(DatabaseQuestion.difficulty).filter(
                    DatabaseQuestion.is_active == True,
                    DatabaseQuestion.difficulty.isnot(None),
                    DatabaseQuestion.difficulty != ""
                ).distinct().all()
                
                return [diff[0] for diff in difficulties]
                
        except Exception as e:
            self.logger.error(f"難易度取得エラー: {e}")
            return []
    
    def get_question_count(self, 
                          category: Optional[str] = None,
                          difficulty: Optional[str] = None) -> int:
        """条件に合う問題数を取得"""
        try:
            from database import DatabaseQuestion
            
            with self._get_session() as session:
                query = session.query(DatabaseQuestion).filter(
                    DatabaseQuestion.is_active == True
                )
                
                if category:
                    query = query.filter(DatabaseQuestion.genre == category)
                
                if difficulty:
                    query = query.filter(DatabaseQuestion.difficulty == difficulty)
                
                return query.count()
                
        except Exception as e:
            self.logger.error(f"問題数取得エラー: {e}")
            return 0
    
    # SessionRepositoryInterface の実装
    
    def save_session(self, session: QuizSession) -> bool:
        """セッションを保存"""
        try:
            from database import DatabaseQuizSession, DatabaseUserHistory
            
            with self._get_session() as session_db:
                existing = session_db.query(DatabaseQuizSession).filter(
                    DatabaseQuizSession.session_id == session.id
                ).first()
                
                if existing:
                    existing.current_index = session.current_index
                    existing.score = session.score
                    
                    if session.is_completed:
                        existing.status = 'completed'
                        existing.completed_at = session.completed_at
                        existing.final_accuracy = session.accuracy
                        existing.wrong_count = len(session.get_wrong_answers())
                else:
                    db_session = DatabaseQuizSession(
                        session_id=session.id,
                        total_questions=session.total_questions,
                        current_index=session.current_index,
                        score=session.score,
                        started_at=session.started_at
                    )
                    
                    if session.is_completed:
                        db_session.status = 'completed'
                        db_session.completed_at = session.completed_at
                        db_session.final_accuracy = session.accuracy
                        db_session.wrong_count = len(session.get_wrong_answers())
                    
                    session_db.add(db_session)
                
                if session.is_completed:
                    self._save_session_history(session, session_db)
                
                return True
                
        except Exception as e:
            self.logger.error(f"セッション保存エラー: {e}")
            return False
    
    def _save_session_history(self, session: QuizSession, db_session) -> None:
        """セッション履歴を保存"""
        try:
            from database import DatabaseUserHistory
            
            wrong_questions_data = []
            for wrong in session.get_wrong_answers():
                wrong_data = {
                    'question': {
                        'question': wrong['question'].text,
                        'options': wrong['question'].options,
                        'correct_answer': wrong['question'].correct_answer,
                        'explanation': wrong['question'].explanation
                    },
                    'selected_option': wrong['selected_option'],
                    'correct_answer': wrong['correct_answer']
                }
                wrong_questions_data.append(wrong_data)
            
            history = DatabaseUserHistory(
                session_id=session.id,
                csv_file="database",
                total_questions=session.total_questions,
                score=session.score,
                accuracy=session.accuracy,
                wrong_count=len(wrong_questions_data),
                timestamp=session.completed_at or session.started_at,
                wrong_questions_data=wrong_questions_data
            )
            
            db_session.add(history)
            
        except Exception as e:
            self.logger.warning(f"履歴保存エラー: {e}")
    
    def get_statistics(self) -> QuizStatistics:
        """統計情報を取得"""
        try:
            from database import DatabaseQuizSession
            
            with self._get_session() as session:
                completed_sessions = session.query(DatabaseQuizSession).filter(
                    DatabaseQuizSession.status == 'completed'
                ).all()
                
                total_sessions = len(completed_sessions)
                total_questions = sum(s.total_questions for s in completed_sessions)
                total_correct = sum(s.score for s in completed_sessions)
                
                best_score = 0
                best_accuracy = 0.0
                
                if completed_sessions:
                    best_score = max(s.score for s in completed_sessions)
                    best_accuracy = max(s.final_accuracy or 0 for s in completed_sessions)
                
                stats = QuizStatistics(
                    total_sessions=total_sessions,
                    total_questions_answered=total_questions,
                    total_correct_answers=total_correct,
                    best_score=best_score,
                    best_accuracy=best_accuracy
                )
                
                return stats
                
        except Exception as e:
            self.logger.error(f"統計取得エラー: {e}")
            return QuizStatistics()
    
    # DatabaseServiceInterface の実装
    
    def get_database_info(self) -> Dict[str, Any]:
        """データベース情報を取得"""
        try:
            from database import DatabaseQuestion, DatabaseQuizSession, DatabaseUserHistory
            
            with self._get_session() as session:
                question_count = session.query(DatabaseQuestion).filter(
                    DatabaseQuestion.is_active == True
                ).count()
                
                session_count = session.query(DatabaseQuizSession).count()
                history_count = session.query(DatabaseUserHistory).count()
                
                return {
                    'question_count': question_count,
                    'session_count': session_count,
                    'history_count': history_count,
                    'categories': self.get_categories(),
                    'difficulties': self.get_difficulties()
                }
                
        except Exception as e:
            self.logger.error(f"データベース情報取得エラー: {e}")
            return {
                'question_count': 0,
                'session_count': 0,
                'history_count': 0,
                'error': str(e)
            }
    
    def health_check(self) -> Dict[str, Any]:
        """データベースヘルスチェック"""
        try:
            # 基本接続チェック
            with self._get_session() as session:
                session.execute("SELECT 1").scalar()
            
            # データベース接続情報取得
            if self._db_connection:
                connection_info = self._db_connection.health_check()
            else:
                connection_info = {'status': 'no_connection'}
            
            # 問題数チェック
            question_count = self.get_question_count()
            
            return {
                'status': 'healthy',
                'database_url': self.database_url,
                'question_count': question_count,
                'connection_info': connection_info
            }
            
        except Exception as e:
            self.logger.error(f"データベースヘルスチェック失敗: {e}")
            return {
                'status': 'unhealthy',
                'error': str(e),
                'database_url': self.database_url
            }
    
    # 追加機能（既存互換性維持）
    
    def search_questions(self, keyword: str, limit: int = 50) -> List[Question]:
        """キーワードで問題を検索"""
        try:
            from database import DatabaseQuestion
            
            with self._get_session() as session:
                search_pattern = f"%{keyword}%"
                
                db_questions = session.query(DatabaseQuestion).filter(
                    DatabaseQuestion.is_active == True,
                    DatabaseQuestion.question.ilike(search_pattern)
                ).limit(limit).all()
                
                questions = []
                for db_q in db_questions:
                    question = Question.from_database(db_q)
                    questions.append(question)
                
                return questions
                
        except Exception as e:
            self.logger.error(f"問題検索エラー: {e}")
            return []
    
    def get_random_questions(self, count: int, 
                           category: Optional[str] = None,
                           difficulty: Optional[str] = None) -> List[Question]:
        """ランダムに問題を取得"""
        return self.get_questions(
            category=category,
            difficulty=difficulty,
            limit=count,
            shuffle=True
        )
    
    def close(self) -> None:
        """データベース接続を閉じる"""
        try:
            if self._db_connection and hasattr(self._db_connection, 'close'):
                self._db_connection.close()
                self.logger.info("データベース接続を閉じました")
        except Exception as e:
            self.logger.warning(f"データベース接続クローズエラー: {e}")
        finally:
            self._db_connection = None