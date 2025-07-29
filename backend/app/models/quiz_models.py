# app/models/quiz_models.py
"""
クイズ関連のPydanticモデル
FastAPI用のリクエスト/レスポンスモデル
"""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime


class QuestionResponse(BaseModel):
    """問題レスポンスモデル"""
    id: int
    text: str
    options: List[str] = Field(..., min_items=4, max_items=4)
    category: Optional[str] = None
    difficulty: Optional[str] = None
    
    class Config:
        from_attributes = True


class QuizSessionRequest(BaseModel):
    """クイズセッション作成リクエストモデル"""
    question_count: int = Field(default=10, ge=1, le=100)
    category: Optional[str] = None
    difficulty: Optional[str] = None
    shuffle: bool = True


class QuizSessionResponse(BaseModel):
    """クイズセッションレスポンスモデル"""
    session_id: str
    total_questions: int
    current_index: int
    score: int
    accuracy: float
    progress_percentage: float
    is_completed: bool
    
    class Config:
        from_attributes = True


class AnswerRequest(BaseModel):
    """回答リクエストモデル"""
    session_id: str
    selected_option: int = Field(..., ge=0, le=3)


class AnswerResponse(BaseModel):
    """回答レスポンスモデル"""
    session_id: str
    question_id: int
    selected_option: int
    correct_answer: int
    is_correct: bool
    explanation: Optional[str] = None
    current_score: int
    current_accuracy: float
    is_session_completed: bool
    
    class Config:
        from_attributes = True


class WrongQuestionDetail(BaseModel):
    """間違えた問題の詳細"""
    question: QuestionResponse
    selected_option: int
    correct_answer: int
    answered_at: datetime


class ResultsResponse(BaseModel):
    """クイズ結果レスポンスモデル"""
    session_id: str
    total_questions: int
    score: int
    accuracy: float
    wrong_count: int
    wrong_questions: List[WrongQuestionDetail]
    started_at: datetime
    completed_at: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    
    class Config:
        from_attributes = True


class CategoryStats(BaseModel):
    """カテゴリ別統計"""
    total: int
    correct: int
    accuracy: float


class StatisticsResponse(BaseModel):
    """統計情報レスポンスモデル"""
    total_sessions: int
    total_questions_answered: int
    total_correct_answers: int
    overall_accuracy: float
    best_score: int
    best_accuracy: float
    category_stats: Optional[Dict[str, CategoryStats]] = None
    difficulty_stats: Optional[Dict[str, CategoryStats]] = None
    
    class Config:
        from_attributes = True


class ProgressResponse(BaseModel):
    """進行状況レスポンスモデル"""
    session_id: str
    current_index: int
    total_questions: int
    score: int
    accuracy: float
    progress_percentage: float
    is_completed: bool
    remaining_questions: int
    
    class Config:
        from_attributes = True


class QuestionListResponse(BaseModel):
    """問題一覧レスポンスモデル"""
    questions: List[QuestionResponse]
    total_count: int
    categories: List[str]
    difficulties: List[str]
    
    class Config:
        from_attributes = True