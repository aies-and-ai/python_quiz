# app/models/__init__.py
"""
APIモデル層
FastAPI用のPydanticモデルを定義
"""

from .quiz_models import (
    QuestionResponse,
    QuizSessionRequest,
    QuizSessionResponse,
    AnswerRequest,
    AnswerResponse,
    ResultsResponse,
    StatisticsResponse
)

from .common import (
    BaseResponse,
    ErrorResponse,
    PaginationRequest,
    PaginationResponse
)

__all__ = [
    # クイズ関連
    "QuestionResponse",
    "QuizSessionRequest", 
    "QuizSessionResponse",
    "AnswerRequest",
    "AnswerResponse",
    "ResultsResponse",
    "StatisticsResponse",
    
    # 共通
    "BaseResponse",
    "ErrorResponse",
    "PaginationRequest",
    "PaginationResponse"
]