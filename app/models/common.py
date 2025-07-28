# app/models/common.py
"""
共通モデル・バリデーター
全APIで共通して使用されるPydanticモデル
"""

from typing import Any, Optional, List, Generic, TypeVar
from pydantic import BaseModel, Field
from datetime import datetime

T = TypeVar('T')


class BaseResponse(BaseModel):
    """基本レスポンスモデル"""
    success: bool = True
    message: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.now)
    
    class Config:
        from_attributes = True


class ErrorResponse(BaseResponse):
    """エラーレスポンスモデル"""
    success: bool = False
    error_code: Optional[str] = None
    error_details: Optional[dict] = None


class SuccessResponse(BaseResponse, Generic[T]):
    """成功レスポンスモデル（データ付き）"""
    data: T
    
    class Config:
        from_attributes = True


class PaginationRequest(BaseModel):
    """ページネーションリクエストモデル"""
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
    sort_by: Optional[str] = None
    sort_order: Optional[str] = Field(default="asc", regex="^(asc|desc)$")


class PaginationResponse(BaseModel):
    """ページネーションレスポンスモデル"""
    page: int
    page_size: int
    total_items: int
    total_pages: int
    has_next: bool
    has_previous: bool
    
    class Config:
        from_attributes = True


class PaginatedResponse(BaseModel, Generic[T]):
    """ページネーション付きレスポンスモデル"""
    items: List[T]
    pagination: PaginationResponse
    
    class Config:
        from_attributes = True


class HealthResponse(BaseModel):
    """ヘルスチェックレスポンスモデル"""
    status: str = "healthy"
    version: str = "1.0.0"
    database_status: str = "connected"
    timestamp: datetime = Field(default_factory=datetime.now)
    
    class Config:
        from_attributes = True


class ValidationErrorDetail(BaseModel):
    """バリデーションエラー詳細"""
    field: str
    message: str
    value: Any


class ValidationErrorResponse(ErrorResponse):
    """バリデーションエラーレスポンス"""
    error_code: str = "VALIDATION_ERROR"
    validation_errors: List[ValidationErrorDetail]


class ImportRequest(BaseModel):
    """インポートリクエストモデル"""
    overwrite: bool = False
    validate_only: bool = False


class ImportResponse(BaseModel):
    """インポートレスポンスモデル"""
    success: bool
    imported_count: int = 0
    skipped_count: int = 0
    error_count: int = 0
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    
    class Config:
        from_attributes = True