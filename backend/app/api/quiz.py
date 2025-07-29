# backend/app/api/quiz.py
"""
クイズAPI エンドポイント
FastAPI用のクイズ機能API
"""

from typing import List, Optional
from fastapi import APIRouter, HTTPException, Depends, Query
from fastapi.responses import JSONResponse

from app.models.quiz_models import (
    QuizSessionRequest,
    QuizSessionResponse,
    QuestionResponse,
    AnswerRequest,
    AnswerResponse,
    ResultsResponse,
    StatisticsResponse,
    ProgressResponse,
    QuestionListResponse
)
from app.models.common import BaseResponse, ErrorResponse, SuccessResponse
from app.core.dependencies import QuizServiceDep, DatabaseServiceDep
from app.core.exceptions import (
    QuizError,
    SessionNotFoundError,
    QuestionNotFoundError,
    InvalidAnswerError,
    exception_to_api_response,
    get_http_status_code
)
from utils.logger import get_logger

router = APIRouter()
logger = get_logger()


@router.post("/sessions", response_model=SuccessResponse[QuizSessionResponse])
async def create_quiz_session(
    request: QuizSessionRequest,
    quiz_service: QuizServiceDep
):
    """新しいクイズセッションを作成"""
    try:
        session = quiz_service.create_session(
            question_count=request.question_count,
            category=request.category,
            difficulty=request.difficulty,
            shuffle=request.shuffle
        )
        
        response_data = QuizSessionResponse(
            session_id=session.id,
            total_questions=session.total_questions,
            current_index=session.current_index,
            score=session.score,
            accuracy=session.accuracy,
            progress_percentage=session.progress_percentage,
            is_completed=session.is_completed
        )
        
        logger.info(f"クイズセッション作成: {session.id}")
        
        return SuccessResponse(
            data=response_data,
            message="クイズセッションを作成しました"
        )
        
    except QuizError as e:
        logger.error(f"セッション作成エラー: {e}")
        error_response = exception_to_api_response(e)
        raise HTTPException(
            status_code=get_http_status_code(e),
            detail=error_response['error']
        )
    except Exception as e:
        logger.error(f"予期しないエラー: {e}")
        raise HTTPException(
            status_code=500,
            detail={"error_code": "INTERNAL_ERROR", "message": "サーバーエラーが発生しました"}
        )


@router.get("/sessions/{session_id}/current", response_model=SuccessResponse[QuestionResponse])
async def get_current_question(
    session_id: str,
    quiz_service: QuizServiceDep
):
    """現在の問題を取得"""
    try:
        question = quiz_service.get_current_question(session_id)
        
        if not question:
            # セッション確認
            try:
                session = quiz_service.get_session(session_id)
                if session.is_completed:
                    raise HTTPException(
                        status_code=409,
                        detail={"error_code": "SESSION_COMPLETED", "message": "クイズは既に完了しています"}
                    )
                else:
                    raise HTTPException(
                        status_code=404,
                        detail={"error_code": "NO_MORE_QUESTIONS", "message": "これ以上問題がありません"}
                    )
            except SessionNotFoundError:
                raise HTTPException(
                    status_code=404,
                    detail={"error_code": "SESSION_NOT_FOUND", "message": "セッションが見つかりません"}
                )
        
        response_data = QuestionResponse(
            id=question.id,
            text=question.text,
            options=question.options,
            category=question.category,
            difficulty=question.difficulty
        )
        
        return SuccessResponse(
            data=response_data,
            message="問題を取得しました"
        )
        
    except HTTPException:
        raise
    except QuizError as e:
        error_response = exception_to_api_response(e)
        raise HTTPException(
            status_code=get_http_status_code(e),
            detail=error_response['error']
        )
    except Exception as e:
        logger.error(f"問題取得エラー: {e}")
        raise HTTPException(
            status_code=500,
            detail={"error_code": "INTERNAL_ERROR", "message": "サーバーエラーが発生しました"}
        )


@router.post("/sessions/{session_id}/answer", response_model=SuccessResponse[AnswerResponse])
async def submit_answer(
    session_id: str,
    request: AnswerRequest,
    quiz_service: QuizServiceDep
):
    """問題に回答を送信"""
    try:
        # セッションIDの整合性チェック
        if request.session_id != session_id:
            raise HTTPException(
                status_code=400,
                detail={"error_code": "SESSION_ID_MISMATCH", "message": "セッションIDが一致しません"}
            )
        
        result = quiz_service.answer_question(session_id, request.selected_option)
        
        response_data = AnswerResponse(
            session_id=result['session_id'],
            question_id=result['question'].id,
            selected_option=result['selected_option'],
            correct_answer=result['correct_answer'],
            is_correct=result['is_correct'],
            explanation=result['explanation'],
            current_score=result['current_score'],
            current_accuracy=result['accuracy'],
            is_session_completed=result['is_session_completed']
        )
        
        message = "正解です！" if result['is_correct'] else "不正解です"
        if result['is_session_completed']:
            message += " クイズが完了しました。"
        
        logger.info(f"回答処理: {session_id} - {'正解' if result['is_correct'] else '不正解'}")
        
        return SuccessResponse(
            data=response_data,
            message=message
        )
        
    except QuizError as e:
        error_response = exception_to_api_response(e)
        raise HTTPException(
            status_code=get_http_status_code(e),
            detail=error_response['error']
        )
    except Exception as e:
        logger.error(f"回答処理エラー: {e}")
        raise HTTPException(
            status_code=500,
            detail={"error_code": "INTERNAL_ERROR", "message": "サーバーエラーが発生しました"}
        )


@router.get("/sessions/{session_id}/progress", response_model=SuccessResponse[ProgressResponse])
async def get_session_progress(
    session_id: str,
    quiz_service: QuizServiceDep
):
    """セッションの進行状況を取得"""
    try:
        progress = quiz_service.get_session_progress(session_id)
        
        response_data = ProgressResponse(
            session_id=progress['session_id'],
            current_index=progress['current_index'],
            total_questions=progress['total_questions'],
            score=progress['score'],
            accuracy=progress['accuracy'],
            progress_percentage=progress['progress_percentage'],
            is_completed=progress['is_completed'],
            remaining_questions=progress['remaining_questions']
        )
        
        return SuccessResponse(
            data=response_data,
            message="進行状況を取得しました"
        )
        
    except QuizError as e:
        error_response = exception_to_api_response(e)
        raise HTTPException(
            status_code=get_http_status_code(e),
            detail=error_response['error']
        )
    except Exception as e:
        logger.error(f"進行状況取得エラー: {e}")
        raise HTTPException(
            status_code=500,
            detail={"error_code": "INTERNAL_ERROR", "message": "サーバーエラーが発生しました"}
        )


@router.get("/sessions/{session_id}/results", response_model=SuccessResponse[ResultsResponse])
async def get_session_results(
    session_id: str,
    quiz_service: QuizServiceDep
):
    """セッション結果を取得"""
    try:
        results = quiz_service.get_session_results(session_id)
        
        # 間違えた問題の詳細を変換
        from app.models.quiz_models import WrongQuestionDetail
        wrong_questions = []
        for wrong in results['wrong_questions']:
            question_data = QuestionResponse(
                id=wrong['question'].id,
                text=wrong['question'].text,
                options=wrong['question'].options,
                category=wrong['question'].category,
                difficulty=wrong['question'].difficulty
            )
            wrong_detail = WrongQuestionDetail(
                question=question_data,
                selected_option=wrong['selected_option'],
                correct_answer=wrong['correct_answer'],
                answered_at=wrong['answered_at']
            )
            wrong_questions.append(wrong_detail)
        
        response_data = ResultsResponse(
            session_id=results['session_id'],
            total_questions=results['total_questions'],
            score=results['score'],
            accuracy=results['accuracy'],
            wrong_count=results['wrong_count'],
            wrong_questions=wrong_questions,
            started_at=results['started_at'],
            completed_at=results['completed_at'],
            duration_seconds=results['duration_seconds']
        )
        
        return SuccessResponse(
            data=response_data,
            message="結果を取得しました"
        )
        
    except QuizError as e:
        error_response = exception_to_api_response(e)
        raise HTTPException(
            status_code=get_http_status_code(e),
            detail=error_response['error']
        )
    except Exception as e:
        logger.error(f"結果取得エラー: {e}")
        raise HTTPException(
            status_code=500,
            detail={"error_code": "INTERNAL_ERROR", "message": "サーバーエラーが発生しました"}
        )


@router.get("/questions")
async def get_questions(
    quiz_service: QuizServiceDep,
    category: Optional[str] = Query(None, description="カテゴリフィルター"),
    difficulty: Optional[str] = Query(None, description="難易度フィルター"),
    limit: Optional[int] = Query(50, ge=1, le=100, description="取得件数")
) -> SuccessResponse[QuestionListResponse]:
    """問題一覧を取得"""
    try:
        # 問題取得
        from app.core.service_factory import get_question_repository
        question_repo = get_question_repository()
        
        questions = question_repo.get_questions(
            category=category,
            difficulty=difficulty,
            limit=limit,
            shuffle=False
        )
        
        # レスポンス形式に変換
        question_responses = [
            QuestionResponse(
                id=q.id,
                text=q.text,
                options=q.options,
                category=q.category,
                difficulty=q.difficulty
            )
            for q in questions
        ]
        
        # メタデータ取得
        categories = quiz_service.get_available_categories()
        difficulties = quiz_service.get_available_difficulties()
        total_count = quiz_service.get_question_count(category, difficulty)
        
        response_data = QuestionListResponse(
            questions=question_responses,
            total_count=total_count,
            categories=categories,
            difficulties=difficulties
        )
        
        return SuccessResponse(
            data=response_data,
            message=f"{len(questions)}件の問題を取得しました"
        )
        
    except Exception as e:
        logger.error(f"問題一覧取得エラー: {e}")
        raise HTTPException(
            status_code=500,
            detail={"error_code": "INTERNAL_ERROR", "message": "サーバーエラーが発生しました"}
        )


@router.get("/statistics", response_model=SuccessResponse[StatisticsResponse])
async def get_statistics(quiz_service: QuizServiceDep):
    """統計情報を取得"""
    try:
        stats = quiz_service.get_statistics()
        
        response_data = StatisticsResponse(
            total_sessions=stats.total_sessions,
            total_questions_answered=stats.total_questions_answered,
            total_correct_answers=stats.total_correct_answers,
            overall_accuracy=stats.overall_accuracy,
            best_score=stats.best_score,
            best_accuracy=stats.best_accuracy
        )
        
        return SuccessResponse(
            data=response_data,
            message="統計情報を取得しました"
        )
        
    except Exception as e:
        logger.error(f"統計情報取得エラー: {e}")
        raise HTTPException(
            status_code=500,
            detail={"error_code": "INTERNAL_ERROR", "message": "サーバーエラーが発生しました"}
        )


@router.get("/categories", response_model=SuccessResponse[List[str]])
async def get_categories(quiz_service: QuizServiceDep):
    """利用可能なカテゴリ一覧を取得"""
    try:
        categories = quiz_service.get_available_categories()
        
        return SuccessResponse(
            data=categories,
            message=f"{len(categories)}件のカテゴリを取得しました"
        )
        
    except Exception as e:
        logger.error(f"カテゴリ取得エラー: {e}")
        raise HTTPException(
            status_code=500,
            detail={"error_code": "INTERNAL_ERROR", "message": "サーバーエラーが発生しました"}
        )


@router.get("/difficulties", response_model=SuccessResponse[List[str]])
async def get_difficulties(quiz_service: QuizServiceDep):
    """利用可能な難易度一覧を取得"""
    try:
        difficulties = quiz_service.get_available_difficulties()
        
        return SuccessResponse(
            data=difficulties,
            message=f"{len(difficulties)}件の難易度を取得しました"
        )
        
    except Exception as e:
        logger.error(f"難易度取得エラー: {e}")
        raise HTTPException(
            status_code=500,
            detail={"error_code": "INTERNAL_ERROR", "message": "サーバーエラーが発生しました"}
        )