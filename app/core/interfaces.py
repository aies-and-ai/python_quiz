# app/core/interfaces.py
"""
インターフェース定義
責任分離とテスタビリティ向上のためのインターフェース層
"""

from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from app.core.models import Question, QuizSession, QuizStatistics


class QuestionRepositoryInterface(ABC):
    """問題データリポジトリインターフェース"""
    
    @abstractmethod
    def get_questions(self, 
                     category: Optional[str] = None,
                     difficulty: Optional[str] = None,
                     limit: Optional[int] = None,
                     shuffle: bool = False) -> List[Question]:
        """問題を取得"""
        pass
    
    @abstractmethod
    def get_question_by_id(self, question_id: int) -> Optional[Question]:
        """IDで問題を取得"""
        pass
    
    @abstractmethod
    def save_question(self, question: Question, csv_filename: str = None) -> Optional[Question]:
        """問題を保存"""
        pass
    
    @abstractmethod
    def find_question_by_text(self, question_text: str, csv_filename: str = None) -> Optional[Question]:
        """問題文で問題を検索"""
        pass
    
    @abstractmethod
    def get_categories(self) -> List[str]:
        """利用可能なカテゴリ一覧を取得"""
        pass
    
    @abstractmethod
    def get_difficulties(self) -> List[str]:
        """利用可能な難易度一覧を取得"""
        pass
    
    @abstractmethod
    def get_question_count(self, 
                          category: Optional[str] = None,
                          difficulty: Optional[str] = None) -> int:
        """条件に合う問題数を取得"""
        pass


class SessionRepositoryInterface(ABC):
    """セッションリポジトリインターフェース"""
    
    @abstractmethod
    def save_session(self, session: QuizSession) -> bool:
        """セッションを保存"""
        pass
    
    @abstractmethod
    def get_statistics(self) -> QuizStatistics:
        """統計情報を取得"""
        pass


class QuizServiceInterface(ABC):
    """クイズサービスインターフェース"""
    
    @abstractmethod
    def create_session(self, 
                      question_count: int = 10,
                      category: Optional[str] = None,
                      difficulty: Optional[str] = None,
                      shuffle: bool = True) -> QuizSession:
        """新しいクイズセッションを作成"""
        pass
    
    @abstractmethod
    def get_session(self, session_id: str) -> QuizSession:
        """セッションを取得"""
        pass
    
    @abstractmethod
    def get_current_question(self, session_id: str) -> Optional[Question]:
        """現在の問題を取得"""
        pass
    
    @abstractmethod
    def answer_question(self, session_id: str, selected_option: int) -> Dict[str, Any]:
        """問題に回答"""
        pass
    
    @abstractmethod
    def get_session_results(self, session_id: str) -> Dict[str, Any]:
        """セッション結果を取得"""
        pass
    
    @abstractmethod
    def get_available_categories(self) -> List[str]:
        """利用可能なカテゴリ一覧を取得"""
        pass
    
    @abstractmethod
    def get_available_difficulties(self) -> List[str]:
        """利用可能な難易度一覧を取得"""
        pass
    
    @abstractmethod
    def get_statistics(self) -> QuizStatistics:
        """統計情報を取得"""
        pass


class CSVImportServiceInterface(ABC):
    """CSVインポートサービスインターフェース"""
    
    @abstractmethod
    def import_from_csv(self, csv_file_path: str, overwrite: bool = False) -> Dict[str, Any]:
        """CSVファイルからインポート"""
        pass
    
    @abstractmethod
    def validate_csv_file(self, csv_file_path: str) -> Dict[str, Any]:
        """CSVファイルの妥当性をチェック"""
        pass
    
    @abstractmethod
    def import_multiple_csv_files(self, csv_directory: str, 
                                 pattern: str = "*.csv") -> Dict[str, Any]:
        """複数のCSVファイルを一括インポート"""
        pass


class DatabaseServiceInterface(ABC):
    """データベースサービスインターフェース"""
    
    @abstractmethod
    def get_database_info(self) -> Dict[str, Any]:
        """データベース情報を取得"""
        pass
    
    @abstractmethod
    def health_check(self) -> Dict[str, Any]:
        """ヘルスチェック"""
        pass


class LoggerInterface(ABC):
    """ロガーインターフェース"""
    
    @abstractmethod
    def info(self, message: str) -> None:
        """INFOレベルでログ出力"""
        pass
    
    @abstractmethod
    def error(self, message: str) -> None:
        """ERRORレベルでログ出力"""
        pass
    
    @abstractmethod
    def warning(self, message: str) -> None:
        """WARNINGレベルでログ出力"""
        pass
    
    @abstractmethod
    def debug(self, message: str) -> None:
        """DEBUGレベルでログ出力"""
        pass