# app/core/models.py
"""
データクラスモデル
基本的なデータクラスのみ使用
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any
import uuid


@dataclass
class Question:
    """問題データクラス"""
    id: int
    text: str
    options: List[str]
    correct_answer: int
    explanation: Optional[str] = None
    category: Optional[str] = None
    difficulty: Optional[str] = None
    
    def __post_init__(self):
        """バリデーション"""
        if len(self.options) != 4:
            raise ValueError("選択肢は4つ必要です")
        if not 0 <= self.correct_answer <= 3:
            raise ValueError("正解番号は0-3の範囲である必要があります")
        if not self.text.strip():
            raise ValueError("問題文は空にできません")
        for i, option in enumerate(self.options):
            if not option.strip():
                raise ValueError(f"選択肢{i+1}は空にできません")
    
    @classmethod
    def from_database(cls, db_question) -> 'Question':
        """データベースQuestionから作成"""
        return cls(
            id=db_question.id,
            text=db_question.question,
            options=db_question.options,
            correct_answer=db_question.correct_answer,
            explanation=db_question.explanation,
            category=db_question.genre,
            difficulty=db_question.difficulty
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            'id': self.id,
            'text': self.text,
            'options': self.options,
            'correct_answer': self.correct_answer,
            'explanation': self.explanation,
            'category': self.category,
            'difficulty': self.difficulty
        }


@dataclass
class Answer:
    """回答データクラス"""
    question_id: int
    selected_option: int
    is_correct: bool
    answered_at: datetime = field(default_factory=datetime.now)
    
    def __post_init__(self):
        """バリデーション"""
        if not 0 <= self.selected_option <= 3:
            raise ValueError("選択肢は0-3の範囲である必要があります")


@dataclass
class QuizSession:
    """クイズセッションデータクラス"""
    id: str
    questions: List[Question]
    answers: List[Answer] = field(default_factory=list)
    started_at: datetime = field(default_factory=datetime.now)
    completed_at: Optional[datetime] = None
    
    def __post_init__(self):
        """初期化後の処理"""
        if not self.id:
            self.id = str(uuid.uuid4())
        if not self.questions:
            raise ValueError("問題リストが空です")
    
    @property
    def total_questions(self) -> int:
        """総問題数"""
        return len(self.questions)
    
    @property
    def current_index(self) -> int:
        """現在の問題インデックス"""
        return len(self.answers)
    
    @property
    def score(self) -> int:
        """現在のスコア"""
        return sum(1 for answer in self.answers if answer.is_correct)
    
    @property
    def accuracy(self) -> float:
        """現在の正答率"""
        if not self.answers:
            return 0.0
        return (self.score / len(self.answers)) * 100
    
    @property
    def progress_percentage(self) -> float:
        """進行状況（パーセンテージ）"""
        return (self.current_index / self.total_questions) * 100
    
    @property
    def is_completed(self) -> bool:
        """セッション完了判定"""
        return self.current_index >= self.total_questions
    
    def get_current_question(self) -> Optional[Question]:
        """現在の問題を取得"""
        if self.current_index < self.total_questions:
            return self.questions[self.current_index]
        return None
    
    def add_answer(self, selected_option: int) -> Answer:
        """回答を追加"""
        if self.is_completed:
            raise ValueError("セッションは既に完了しています")
        
        current_question = self.get_current_question()
        if not current_question:
            raise ValueError("現在の問題が見つかりません")
        
        is_correct = selected_option == current_question.correct_answer
        
        answer = Answer(
            question_id=current_question.id,
            selected_option=selected_option,
            is_correct=is_correct
        )
        
        self.answers.append(answer)
        
        if self.is_completed:
            self.completed_at = datetime.now()
        
        return answer
    
    def get_wrong_answers(self) -> List[Dict[str, Any]]:
        """間違えた問題の詳細を取得"""
        wrong_answers = []
        
        for answer in self.answers:
            if not answer.is_correct:
                question = None
                for q in self.questions:
                    if q.id == answer.question_id:
                        question = q
                        break
                
                if question:
                    wrong_answers.append({
                        'question': question,
                        'selected_option': answer.selected_option,
                        'correct_answer': question.correct_answer,
                        'answered_at': answer.answered_at
                    })
        
        return wrong_answers
    
    def get_results_summary(self) -> Dict[str, Any]:
        """結果サマリーを取得"""
        if not self.is_completed:
            raise ValueError("セッションが完了していません")
        
        wrong_answers = self.get_wrong_answers()
        
        return {
            'session_id': self.id,
            'total_questions': self.total_questions,
            'score': self.score,
            'accuracy': self.accuracy,
            'wrong_count': len(wrong_answers),
            'wrong_questions': wrong_answers,
            'started_at': self.started_at,
            'completed_at': self.completed_at,
            'duration_seconds': (self.completed_at - self.started_at).total_seconds() if self.completed_at else None
        }


@dataclass
class QuizStatistics:
    """統計情報データクラス"""
    total_sessions: int = 0
    total_questions_answered: int = 0
    total_correct_answers: int = 0
    best_score: int = 0
    best_accuracy: float = 0.0
    
    @property
    def overall_accuracy(self) -> float:
        """全体正答率"""
        if self.total_questions_answered == 0:
            return 0.0
        return (self.total_correct_answers / self.total_questions_answered) * 100
    
    def update_with_session(self, session: QuizSession) -> None:
        """セッション結果で統計を更新"""
        if not session.is_completed:
            return
        
        self.total_sessions += 1
        self.total_questions_answered += session.total_questions
        self.total_correct_answers += session.score
        
        if session.score > self.best_score:
            self.best_score = session.score
        
        if session.accuracy > self.best_accuracy:
            self.best_accuracy = session.accuracy
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            'total_sessions': self.total_sessions,
            'total_questions_answered': self.total_questions_answered,
            'total_correct_answers': self.total_correct_answers,
            'overall_accuracy': self.overall_accuracy,
            'best_score': self.best_score,
            'best_accuracy': self.best_accuracy
        }


@dataclass
class ImportResult:
    """インポート結果データクラス"""
    success: bool
    imported_count: int = 0
    skipped_count: int = 0
    error_count: int = 0
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    def add_error(self, error: str) -> None:
        """エラーを追加"""
        self.errors.append(error)
        self.error_count += 1
    
    def add_warning(self, warning: str) -> None:
        """警告を追加"""
        self.warnings.append(warning)
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return {
            'success': self.success,
            'imported_count': self.imported_count,
            'skipped_count': self.skipped_count,
            'error_count': self.error_count,
            'errors': self.errors,
            'warnings': self.warnings
        }


# ユーティリティ関数

def create_question_from_csv_row(row: Dict[str, str], question_id: int) -> Question:
    """CSV行から問題を作成"""
    try:
        text = row.get('question', '').strip()
        if not text:
            raise ValueError("問題文が空です")
        
        options = []
        for i in range(1, 5):
            option = row.get(f'option{i}', '').strip()
            if not option:
                raise ValueError(f"選択肢{i}が空です")
            options.append(option)
        
        correct_str = row.get('correct_answer', '').strip()
        if not correct_str:
            raise ValueError("正解番号が設定されていません")
        
        try:
            correct_answer = int(correct_str) - 1
            if not 0 <= correct_answer <= 3:
                raise ValueError(f"正解番号が範囲外です: {correct_str}")
        except ValueError:
            raise ValueError(f"正解番号が無効です: {correct_str}")
        
        explanation = row.get('explanation', '').strip() or None
        category = row.get('genre', '').strip() or row.get('category', '').strip() or None
        difficulty = row.get('difficulty', '').strip() or None
        
        return Question(
            id=question_id,
            text=text,
            options=options,
            correct_answer=correct_answer,
            explanation=explanation,
            category=category,
            difficulty=difficulty
        )
        
    except Exception as e:
        raise ValueError(f"CSV行の解析エラー: {str(e)}")


def validate_csv_headers(headers: List[str]) -> tuple[bool, List[str]]:
    """CSVヘッダーの妥当性をチェック"""
    required_headers = ['question', 'option1', 'option2', 'option3', 'option4', 'correct_answer']
    missing_headers = []
    
    for header in required_headers:
        if header not in headers:
            missing_headers.append(header)
    
    return len(missing_headers) == 0, missing_headers


def shuffle_question_options(question: Question) -> Question:
    """問題の選択肢をシャッフル"""
    import random
    
    options_with_indices = list(enumerate(question.options))
    random.shuffle(options_with_indices)
    
    new_options = [option for _, option in options_with_indices]
    
    new_correct_answer = 0
    for new_idx, (old_idx, _) in enumerate(options_with_indices):
        if old_idx == question.correct_answer:
            new_correct_answer = new_idx
            break
    
    return Question(
        id=question.id,
        text=question.text,
        options=new_options,
        correct_answer=new_correct_answer,
        explanation=question.explanation,
        category=question.category,
        difficulty=question.difficulty
    )