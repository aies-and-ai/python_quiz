# app/core/__init__.py
"""
コアビジネスロジック層
ドメインロジック、サービス、インターフェースを提供
"""

from .models import Question, QuizSession, Answer, QuizStatistics
from .interfaces import (
    QuizServiceInterface,
    QuestionRepositoryInterface, 
    SessionRepositoryInterface,
    CSVImportServiceInterface,
    DatabaseServiceInterface
)
from .exceptions import (
    QuizError,
    SessionError,
    QuestionNotFoundError,
    InvalidAnswerError,
    CSVImportError,
    DatabaseError
)

__all__ = [
    # モデル
    "Question",
    "QuizSession", 
    "Answer",
    "QuizStatistics",
    
    # インターフェース
    "QuizServiceInterface",
    "QuestionRepositoryInterface",
    "SessionRepositoryInterface", 
    "CSVImportServiceInterface",
    "DatabaseServiceInterface",
    
    # 例外
    "QuizError",
    "SessionError",
    "QuestionNotFoundError",
    "InvalidAnswerError",
    "CSVImportError",
    "DatabaseError"
]