# database/manager.py
"""
データベース操作の統合管理クラス
既存のクイズ機能とSQLiteデータベースを橋渡し
"""

import random
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from sqlalchemy import func, desc, and_, or_
from sqlalchemy.orm import Session

from database import (
    get_db_session,
    DatabaseQuestion,
    DatabaseQuizSession,
    DatabaseQuizAnswer,
    DatabaseUserHistory,
    DatabaseStatistics
)
from models import QuestionModel, QuizSessionModel
from enhanced_exceptions import QuizDataError, wrap_exception
from logger import get_logger


class QuizDatabaseManager:
    """クイズデータベース操作の統合管理クラス"""
    
    def __init__(self, database_url: Optional[str] = None):
        """
        初期化
        
        Args:
            database_url: データベースURL（Noneの場合デフォルト使用）
        """
        self.logger = get_logger()
        self.database_url = database_url
        
    # === 問題データ操作 ===
    
    def get_questions(self, 
                     genre: Optional[str] = None,
                     difficulty: Optional[str] = None,
                     tags: Optional[List[str]] = None,
                     csv_source: Optional[str] = None,
                     limit: Optional[int] = None,
                     shuffle: bool = False) -> List[Dict[str, Any]]:
        """
        条件に基づいて問題を取得
        
        Args:
            genre: ジャンル絞り込み
            difficulty: 難易度絞り込み
            tags: タグ絞り込み（リスト内のいずれかにマッチ）
            csv_source: CSVファイル名絞り込み
            limit: 取得件数制限
            shuffle: ランダム順序で取得するかどうか
            
        Returns:
            List[Dict]: 既存形式の問題データリスト
        """
        try:
            with get_db_session(self.database_url) as session:
                query = session.query(DatabaseQuestion).filter(
                    DatabaseQuestion.is_active == True
                )
                
                # 絞り込み条件の適用
                if genre:
                    query = query.filter(DatabaseQuestion.genre == genre)
                
                if difficulty:
                    query = query.filter(DatabaseQuestion.difficulty == difficulty)
                
                if tags:
                    # タグは文字列内検索（カンマ区切りのタグに対して）
                    tag_conditions = []
                    for tag in tags:
                        tag_conditions.append(DatabaseQuestion.tags.contains(tag))
                    query = query.filter(or_(*tag_conditions))
                
                if csv_source:
                    query = query.filter(DatabaseQuestion.csv_source_file == csv_source)
                
                # ランダム順序またはID順
                if shuffle:
                    query = query.order_by(func.random())
                else:
                    query = query.order_by(DatabaseQuestion.id)
                
                if limit:
                    query = query.limit(limit)
                
                questions = query.all()
                
                # 既存形式に変換
                result = [q.to_legacy_dict() for q in questions]
                
                self.logger.debug(f"Retrieved {len(result)} questions with filters: genre={genre}, difficulty={difficulty}")
                
                return result
                
        except Exception as e:
            self.logger.error(f"Failed to get questions: {e}")
            raise QuizDataError(
                message=f"Failed to retrieve questions: {str(e)}",
                operation="get_questions"
            )
    
    def get_question_by_id(self, question_id: int) -> Optional[Dict[str, Any]]:
        """
        IDで問題を取得
        
        Args:
            question_id: 問題ID
            
        Returns:
            Dict: 問題データ（既存形式）またはNone
        """
        try:
            with get_db_session(self.database_url) as session:
                question = session.query(DatabaseQuestion).filter(
                    DatabaseQuestion.id == question_id,
                    DatabaseQuestion.is_active == True
                ).first()
                
                return question.to_legacy_dict() if question else None
                
        except Exception as e:
            self.logger.error(f"Failed to get question by ID {question_id}: {e}")
            return None
    
    def search_questions(self, keyword: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        キーワードで問題を検索
        
        Args:
            keyword: 検索キーワード
            limit: 最大取得件数
            
        Returns:
            List[Dict]: 検索結果の問題データリスト
        """
        try:
            with get_db_session(self.database_url) as session:
                # 問題文、選択肢、解説から検索
                search_pattern = f"%{keyword}%"
                
                query = session.query(DatabaseQuestion).filter(
                    DatabaseQuestion.is_active == True,
                    or_(
                        DatabaseQuestion.question.ilike(search_pattern),
                        DatabaseQuestion.explanation.ilike(search_pattern),
                        # JSON配列内の検索（SQLiteではシンプルに）
                        func.json_extract(DatabaseQuestion.options, '$').like(search_pattern)
                    )
                ).limit(limit)
                
                questions = query.all()
                
                self.logger.debug(f"Found {len(questions)} questions for keyword: {keyword}")
                
                return [q.to_legacy_dict() for q in questions]
                
        except Exception as e:
            self.logger.error(f"Failed to search questions: {e}")
            return []
    
    def get_available_genres(self) -> List[str]:
        """利用可能なジャンル一覧を取得"""
        try:
            with get_db_session(self.database_url) as session:
                genres = session.query(DatabaseQuestion.genre).filter(
                    DatabaseQuestion.is_active == True,
                    DatabaseQuestion.genre.isnot(None),
                    DatabaseQuestion.genre != ""
                ).distinct().all()
                
                return [genre[0] for genre in genres]
                
        except Exception as e:
            self.logger.error(f"Failed to get genres: {e}")
            return []
    
    def get_available_difficulties(self) -> List[str]:
        """利用可能な難易度一覧を取得"""
        try:
            with get_db_session(self.database_url) as session:
                difficulties = session.query(DatabaseQuestion.difficulty).filter(
                    DatabaseQuestion.is_active == True,
                    DatabaseQuestion.difficulty.isnot(None),
                    DatabaseQuestion.difficulty != ""
                ).distinct().all()
                
                return [diff[0] for diff in difficulties]
                
        except Exception as e:
            self.logger.error(f"Failed to get difficulties: {e}")
            return []
    
    def get_csv_sources(self) -> List[str]:
        """利用可能なCSVソース一覧を取得"""
        try:
            with get_db_session(self.database_url) as session:
                sources = session.query(DatabaseQuestion.csv_source_file).filter(
                    DatabaseQuestion.is_active == True,
                    DatabaseQuestion.csv_source_file.isnot(None)
                ).distinct().all()
                
                return [source[0] for source in sources]
                
        except Exception as e:
            self.logger.error(f"Failed to get CSV sources: {e}")
            return []
    
    # === クイズセッション管理 ===
    
    def create_quiz_session(self, 
                           question_ids: List[int],
                           csv_source: Optional[str] = None,
                           shuffle_questions: bool = True,
                           shuffle_options: bool = True) -> str:
        """
        新しいクイズセッションを作成
        
        Args:
            question_ids: 出題する問題IDのリスト
            csv_source: CSVファイル名
            shuffle_questions: 問題順をシャッフルするか
            shuffle_options: 選択肢順をシャッフルするか
            
        Returns:
            str: セッションID
        """
        try:
            session_id = str(uuid.uuid4())
            
            # 問題順をシャッフル
            if shuffle_questions:
                random.shuffle(question_ids)
            
            with get_db_session(self.database_url) as session:
                quiz_session = DatabaseQuizSession.create_new_session(
                    total_questions=len(question_ids),
                    csv_filename=csv_source,
                    shuffle_questions=shuffle_questions,
                    shuffle_options=shuffle_options
                )
                quiz_session.session_id = session_id
                quiz_session.question_sequence = question_ids
                
                session.add(quiz_session)
                session.commit()
                
                self.logger.info(f"Created quiz session {session_id} with {len(question_ids)} questions")
                
                return session_id
                
        except Exception as e:
            self.logger.error(f"Failed to create quiz session: {e}")
            raise QuizDataError(
                message=f"Failed to create quiz session: {str(e)}",
                operation="create_session"
            )
    
    def get_quiz_session(self, session_id: str) -> Optional[DatabaseQuizSession]:
        """クイズセッション情報を取得"""
        try:
            with get_db_session(self.database_url) as session:
                quiz_session = session.query(DatabaseQuizSession).filter(
                    DatabaseQuizSession.session_id == session_id
                ).first()
                
                return quiz_session
                
        except Exception as e:
            self.logger.error(f"Failed to get quiz session {session_id}: {e}")
            return None
    
    def update_session_progress(self, session_id: str, current_index: int, score: int) -> bool:
        """セッションの進行状況を更新"""
        try:
            with get_db_session(self.database_url) as session:
                quiz_session = session.query(DatabaseQuizSession).filter(
                    DatabaseQuizSession.session_id == session_id
                ).first()
                
                if not quiz_session:
                    return False
                
                quiz_session.current_index = current_index
                quiz_session.score = score
                
                # 完了チェック
                if current_index >= quiz_session.total_questions:
                    quiz_session.status = 'completed'
                    quiz_session.completed_at = datetime.utcnow()
                    quiz_session.final_accuracy = (score / quiz_session.total_questions) * 100
                    quiz_session.wrong_count = quiz_session.total_questions - score
                
                session.commit()
                
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to update session progress: {e}")
            return False
    
    def save_quiz_answer(self, 
                        session_id: str,
                        question_id: int,
                        question_index: int,
                        selected_option: int,
                        is_correct: bool,
                        question_snapshot: Dict[str, Any]) -> bool:
        """
        クイズの回答を保存
        
        Args:
            session_id: セッションID
            question_id: 問題ID
            question_index: セッション内の問題番号
            selected_option: 選択した選択肢
            is_correct: 正解かどうか
            question_snapshot: 回答時の問題データ（シャッフル後）
            
        Returns:
            bool: 保存成功かどうか
        """
        try:
            with get_db_session(self.database_url) as session:
                quiz_answer = DatabaseQuizAnswer(
                    session_id=session_id,
                    question_id=question_id,
                    question_index=question_index,
                    selected_option=selected_option,
                    is_correct=is_correct,
                    question_snapshot=question_snapshot
                )
                
                session.add(quiz_answer)
                session.commit()
                
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to save quiz answer: {e}")
            return False
    
    # === 履歴・統計管理 ===
    
    def save_quiz_result(self, results: Dict[str, Any], session_id: str) -> bool:
        """
        クイズ結果を履歴として保存（既存のdata_manager.pyとの互換性維持）
        
        Args:
            results: クイズ結果データ
            session_id: セッションID
            
        Returns:
            bool: 保存成功かどうか
        """
        try:
            with get_db_session(self.database_url) as session:
                user_history = DatabaseUserHistory.from_legacy_result(results, session_id)
                session.add(user_history)
                session.commit()
                
                self.logger.info(f"Saved quiz result for session {session_id}")
                
                return True
                
        except Exception as e:
            self.logger.error(f"Failed to save quiz result: {e}")
            return False
    
    def get_quiz_history(self, limit: int = 10, csv_file: str = None) -> List[Dict[str, Any]]:
        """
        クイズ履歴を取得（既存形式で返す）
        
        Args:
            limit: 取得件数制限
            csv_file: CSVファイル絞り込み
            
        Returns:
            List[Dict]: 履歴データリスト
        """
        try:
            with get_db_session(self.database_url) as session:
                query = session.query(DatabaseUserHistory).order_by(
                    desc(DatabaseUserHistory.timestamp)
                )
                
                if csv_file:
                    query = query.filter(DatabaseUserHistory.csv_file == csv_file)
                
                if limit:
                    query = query.limit(limit)
                
                histories = query.all()
                
                # 既存形式に変換
                result = []
                for history in histories:
                    result.append({
                        'timestamp': history.timestamp.isoformat(),
                        'csv_file': history.csv_file,
                        'total_questions': history.total_questions,
                        'score': history.score,
                        'accuracy': history.accuracy,
                        'wrong_count': history.wrong_count,
                        'wrong_questions': history.wrong_questions_data or []
                    })
                
                return result
                
        except Exception as e:
            self.logger.error(f"Failed to get quiz history: {e}")
            return []
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        統計情報を取得（既存のdata_manager.pyと同じ形式）
        
        Returns:
            Dict: 統計情報
        """
        try:
            with get_db_session(self.database_url) as session:
                # 基本統計
                total_quizzes = session.query(DatabaseUserHistory).count()
                total_questions = session.query(func.sum(DatabaseUserHistory.total_questions)).scalar() or 0
                total_correct = session.query(func.sum(DatabaseUserHistory.score)).scalar() or 0
                
                overall_accuracy = (total_correct / total_questions * 100) if total_questions > 0 else 0.0
                
                return {
                    'total_quizzes': total_quizzes,
                    'total_questions': total_questions,
                    'total_correct': total_correct,
                    'overall_accuracy': overall_accuracy
                }
                
        except Exception as e:
            self.logger.error(f"Failed to get statistics: {e}")
            return {
                'total_quizzes': 0,
                'total_questions': 0,
                'total_correct': 0,
                'overall_accuracy': 0.0
            }
    
    def get_best_scores(self) -> Dict[str, Any]:
        """
        ベストスコア情報を取得
        
        Returns:
            Dict: CSVファイル別のベストスコア
        """
        try:
            with get_db_session(self.database_url) as session:
                # CSVファイル別の最高スコア
                best_scores = {}
                
                csv_files = session.query(DatabaseUserHistory.csv_file).distinct().all()
                
                for (csv_file,) in csv_files:
                    # 該当CSVファイルの最高スコア
                    best_record = session.query(DatabaseUserHistory).filter(
                        DatabaseUserHistory.csv_file == csv_file
                    ).order_by(
                        desc(DatabaseUserHistory.score),
                        desc(DatabaseUserHistory.accuracy)
                    ).first()
                    
                    if best_record:
                        # プレイ回数
                        play_count = session.query(DatabaseUserHistory).filter(
                            DatabaseUserHistory.csv_file == csv_file
                        ).count()
                        
                        best_scores[csv_file] = {
                            'best_score': best_record.score,
                            'best_accuracy': best_record.accuracy,
                            'total_questions': best_record.total_questions,
                            'achieved_date': best_record.timestamp.isoformat(),
                            'play_count': play_count
                        }
                
                return best_scores
                
        except Exception as e:
            self.logger.error(f"Failed to get best scores: {e}")
            return {}
    
    def get_wrong_questions_summary(self, csv_file: str = None) -> Dict[str, Any]:
        """
        間違えた問題のサマリーを取得
        
        Args:
            csv_file: CSVファイル絞り込み
            
        Returns:
            Dict: 間違えた問題の集計データ
        """
        try:
            with get_db_session(self.database_url) as session:
                query = session.query(DatabaseUserHistory)
                
                if csv_file:
                    query = query.filter(DatabaseUserHistory.csv_file == csv_file)
                
                histories = query.all()
                
                # 間違えた問題を集計
                wrong_summary = {}
                
                for history in histories:
                    if history.wrong_questions_data:
                        for wrong in history.wrong_questions_data:
                            question_text = wrong.get('question', {}).get('question', '')
                            
                            if question_text:
                                if question_text not in wrong_summary:
                                    wrong_summary[question_text] = {
                                        'count': 0,
                                        'correct_answer': wrong.get('question', {}).get('options', [''])[
                                            wrong.get('correct_answer', 0)
                                        ] if wrong.get('correct_answer', 0) < len(wrong.get('question', {}).get('options', [])) else '',
                                        'common_mistakes': {}
                                    }
                                
                                wrong_summary[question_text]['count'] += 1
                                
                                # よくある間違い
                                selected = wrong.get('question', {}).get('options', [''])[
                                    wrong.get('selected_option', 0)
                                ] if wrong.get('selected_option', 0) < len(wrong.get('question', {}).get('options', [])) else ''
                                
                                if selected:
                                    mistakes = wrong_summary[question_text]['common_mistakes']
                                    mistakes[selected] = mistakes.get(selected, 0) + 1
                
                # 間違い回数でソート
                sorted_wrong = dict(sorted(wrong_summary.items(), key=lambda x: x[1]['count'], reverse=True))
                
                return sorted_wrong
                
        except Exception as e:
            self.logger.error(f"Failed to get wrong questions summary: {e}")
            return {}
    
    # === データベース管理 ===
    
    def get_database_info(self) -> Dict[str, Any]:
        """データベース情報を取得"""
        try:
            with get_db_session(self.database_url) as session:
                # テーブル別レコード数
                question_count = session.query(DatabaseQuestion).filter(DatabaseQuestion.is_active == True).count()
                session_count = session.query(DatabaseQuizSession).count()
                history_count = session.query(DatabaseUserHistory).count()
                answer_count = session.query(DatabaseQuizAnswer).count()
                
                # CSVファイル別の問題数
                csv_counts = session.query(
                    DatabaseQuestion.csv_source_file,
                    func.count(DatabaseQuestion.id)
                ).filter(
                    DatabaseQuestion.is_active == True
                ).group_by(DatabaseQuestion.csv_source_file).all()
                
                return {
                    'total_questions': question_count,
                    'total_sessions': session_count,
                    'total_history_records': history_count,
                    'total_answers': answer_count,
                    'csv_file_counts': {csv_file: count for csv_file, count in csv_counts},
                    'available_genres': self.get_available_genres(),
                    'available_difficulties': self.get_available_difficulties()
                }
                
        except Exception as e:
            self.logger.error(f"Failed to get database info: {e}")
            return {}


# 便利関数：既存コードとの互換性
def get_quiz_manager(database_url: str = None) -> QuizDatabaseManager:
    """QuizDatabaseManagerインスタンスを取得"""
    return QuizDatabaseManager(database_url)