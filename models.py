# models.py
"""
Week 4: データバリデーション強化
pydanticを使用した型安全なデータモデル
"""

from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, field_validator, Field, ConfigDict
from enum import Enum
from logger import get_logger


class DifficultyLevel(str, Enum):
    """難易度レベルの定義"""
    BEGINNER = "初級"
    INTERMEDIATE = "中級" 
    ADVANCED = "上級"
    EXPERT = "エキスパート"


class QuestionType(str, Enum):
    """問題タイプの定義"""
    MULTIPLE_CHOICE = "4択"
    TRUE_FALSE = "○×"
    FILL_BLANK = "記述"


class QuestionModel(BaseModel):
    """
    クイズ問題のデータモデル
    CSVから読み込まれたデータを型安全に管理
    """
    model_config = ConfigDict(
        str_strip_whitespace=True,  # 文字列の前後空白を自動削除
        validate_assignment=True,   # 代入時にもバリデーション実行
        extra='allow'              # 追加フィールドを許可
    )
    
    # === 必須フィールド ===
    question: str = Field(
        min_length=1,
        max_length=1000,
        description="問題文"
    )
    
    options: List[str] = Field(
        min_length=4,
        max_length=4,
        description="選択肢（4つ）"
    )
    
    correct_answer: int = Field(
        ge=0,
        le=3,
        description="正解のインデックス（0-3）"
    )
    
    # === オプションフィールド ===
    title: Optional[str] = Field(
        default=None,
        max_length=200,
        description="問題タイトル"
    )
    
    explanation: Optional[str] = Field(
        default=None,
        max_length=2000,
        description="解説"
    )
    
    option_explanations: List[str] = Field(
        default_factory=lambda: ["", "", "", ""],
        min_length=4,
        max_length=4,
        description="各選択肢の解説"
    )
    
    # === メタデータフィールド ===
    genre: Optional[str] = Field(
        default=None,
        max_length=50,
        description="ジャンル"
    )
    
    difficulty: Optional[str] = Field(
        default=None,
        max_length=20,
        description="難易度"
    )
    
    tags: Optional[str] = Field(
        default=None,
        max_length=200,
        description="タグ（カンマ区切り）"
    )
    
    source: Optional[str] = Field(
        default=None,
        max_length=100,
        description="出典"
    )
    
    # === 動的フィールド ===
    extra_data: Dict[str, Any] = Field(
        default_factory=dict,
        description="その他の追加データ"
    )
    
    @field_validator('question')
    @classmethod
    def validate_question(cls, v: str) -> str:
        """問題文のバリデーション"""
        if not v or v.isspace():
            raise ValueError("問題文は空にできません")
        
        # 問題文として不適切なパターンをチェック
        invalid_patterns = ['test', 'テスト', 'dummy', 'sample']
        if any(pattern in v.lower() for pattern in invalid_patterns):
            logger = get_logger()
            logger.warning(f"問題文に仮データらしき文言が含まれています: {v[:50]}...")
        
        return v
    
    @field_validator('options')
    @classmethod
    def validate_options(cls, v: List[str]) -> List[str]:
        """選択肢のバリデーション"""
        if len(v) != 4:
            raise ValueError("選択肢は必ず4つ必要です")
        
        # 空の選択肢をチェック
        for i, option in enumerate(v):
            if not option or option.isspace():
                raise ValueError(f"選択肢{i+1}は空にできません")
        
        # 重複する選択肢をチェック
        unique_options = set(option.lower().strip() for option in v)
        if len(unique_options) != 4:
            raise ValueError("選択肢に重複があります")
        
        # 選択肢が極端に短い場合の警告
        for i, option in enumerate(v):
            if len(option.strip()) < 2:
                logger = get_logger()
                logger.warning(f"選択肢{i+1}が極端に短いです: '{option}'")
        
        return v
    
    @field_validator('correct_answer')
    @classmethod
    def validate_correct_answer(cls, v: int) -> int:
        """正解のバリデーション"""
        if not isinstance(v, int):
            raise ValueError("正解番号は整数である必要があります")
        
        if v < 0 or v > 3:
            raise ValueError("正解番号は0-3の範囲である必要があります")
        
        return v
    
    @field_validator('difficulty')
    @classmethod
    def validate_difficulty(cls, v: Optional[str]) -> Optional[str]:
        """難易度のバリデーション"""
        if v is None:
            return v
        
        # 一般的な難易度表現を正規化
        difficulty_mapping = {
            '1': '初級', 'easy': '初級', '簡単': '初級', '初心者': '初級',
            '2': '中級', 'medium': '中級', '普通': '中級', '中間': '中級',
            '3': '上級', 'hard': '上級', '難しい': '上級', '高級': '上級',
            '4': 'エキスパート', 'expert': 'エキスパート', '専門': 'エキスパート'
        }
        
        normalized = difficulty_mapping.get(v.lower(), v)
        return normalized
    
    @field_validator('tags')
    @classmethod
    def validate_tags(cls, v: Optional[str]) -> Optional[str]:
        """タグのバリデーション"""
        if v is None:
            return v
        
        # タグの形式をチェック
        tags = [tag.strip() for tag in v.split(',')]
        
        # 空のタグを除去
        valid_tags = [tag for tag in tags if tag]
        
        if not valid_tags:
            return None
        
        # タグの重複を除去
        unique_tags = list(dict.fromkeys(valid_tags))  # 順序を保持して重複除去
        
        return ', '.join(unique_tags)
    
    def get_display_title(self) -> str:
        """表示用タイトルを取得"""
        if self.title:
            return self.title
        
        # タイトルがない場合は問題文の最初の部分を使用
        question_preview = self.question[:50]
        if len(self.question) > 50:
            question_preview += "..."
        
        return question_preview
    
    def get_tags_list(self) -> List[str]:
        """タグをリストとして取得"""
        if not self.tags:
            return []
        
        return [tag.strip() for tag in self.tags.split(',')]
    
    def has_explanations(self) -> bool:
        """解説があるかどうかを確認"""
        if self.explanation:
            return True
        
        return any(exp.strip() for exp in self.option_explanations)
    
    def get_difficulty_level(self) -> Optional[DifficultyLevel]:
        """難易度をEnumとして取得"""
        if not self.difficulty:
            return None
        
        try:
            return DifficultyLevel(self.difficulty)
        except ValueError:
            return None
    
    def to_legacy_dict(self) -> Dict[str, Any]:
        """既存のコードとの互換性のため、従来の辞書形式に変換"""
        result = {
            'question': self.question,
            'options': self.options,
            'correct_answer': self.correct_answer,
            'explanation': self.explanation or '',
            'option_explanations': self.option_explanations
        }
        
        # 追加データがある場合は extra_data として設定
        if self.extra_data or self.title or self.genre or self.difficulty:
            extra = self.extra_data.copy()
            
            if self.title:
                extra['title'] = self.title
            if self.genre:
                extra['genre'] = self.genre
            if self.difficulty:
                extra['difficulty'] = self.difficulty
            if self.tags:
                extra['tags'] = self.tags
            if self.source:
                extra['source'] = self.source
            
            if extra:
                result['extra_data'] = extra
        
        return result
    
    @classmethod
    def from_csv_dict(cls, data: Dict[str, str], row_number: int = 0) -> 'QuestionModel':
        """
        CSVの辞書データからQuestionModelを作成
        
        Args:
            data: CSVの1行分のデータ
            row_number: 行番号（エラー表示用）
        
        Returns:
            QuestionModel: バリデーション済みの問題データ
        """
        from enhanced_exceptions import CSVFormatError
        
        try:
            # 基本フィールドの抽出
            question = data.get('question', '').strip()
            
            # 選択肢の抽出
            options = []
            for i in range(1, 5):
                option = data.get(f'option{i}', '').strip()
                options.append(option)
            
            # 正解番号の変換（1-4 → 0-3）
            correct_answer_str = data.get('correct_answer', '').strip()
            if correct_answer_str:
                try:
                    correct_answer = int(correct_answer_str) - 1
                except ValueError:
                    raise ValueError(f"正解番号が不正です: {correct_answer_str}")
            else:
                raise ValueError("正解番号が設定されていません")
            
            # 選択肢ごとの解説
            option_explanations = []
            for i in range(1, 5):
                explanation = data.get(f'option{i}_explanation', '').strip()
                option_explanations.append(explanation)
            
            # その他のフィールド
            title = data.get('title', '').strip() or None
            explanation = data.get('explanation', '').strip() or None
            genre = data.get('genre', '').strip() or None
            difficulty = data.get('difficulty', '').strip() or None
            tags = data.get('tags', '').strip() or None
            source = data.get('source', '').strip() or None
            
            # 追加データ（予約フィールド以外）
            reserved_fields = {
                'question', 'correct_answer', 'explanation', 'title', 'genre',
                'difficulty', 'tags', 'source',
                'option1', 'option2', 'option3', 'option4',
                'option1_explanation', 'option2_explanation', 
                'option3_explanation', 'option4_explanation'
            }
            
            extra_data = {}
            for key, value in data.items():
                if key not in reserved_fields and value.strip():
                    extra_data[key] = value.strip()
            
            # モデルを作成
            return cls(
                question=question,
                options=options,
                correct_answer=correct_answer,
                title=title,
                explanation=explanation,
                option_explanations=option_explanations,
                genre=genre,
                difficulty=difficulty,
                tags=tags,
                source=source,
                extra_data=extra_data
            )
            
        except Exception as e:
            # CSVFormatErrorでラップして行番号情報を追加
            if isinstance(e, ValueError):
                raise CSVFormatError(
                    message=str(e),
                    line_number=row_number,
                    user_message=f"{row_number}行目: {str(e)}"
                )
            else:
                raise CSVFormatError(
                    message=f"Row {row_number} parsing error: {str(e)}",
                    line_number=row_number,
                    original_error=e,
                    user_message=f"{row_number}行目のデータ処理中にエラーが発生しました"
                )


class QuizSessionModel(BaseModel):
    """
    クイズセッションのデータモデル
    1回のクイズ実行の状態を管理
    """
    model_config = ConfigDict(
        validate_assignment=True,
        extra='forbid'  # 予期しないフィールドは拒否
    )
    
    # === セッション情報 ===
    session_id: str = Field(description="セッションID")
    csv_file: str = Field(description="使用したCSVファイル")
    total_questions: int = Field(ge=1, le=1000, description="総問題数")
    current_index: int = Field(ge=0, description="現在の問題インデックス")
    
    # === 設定 ===
    shuffle_questions: bool = Field(default=True, description="問題をシャッフルするか")
    shuffle_options: bool = Field(default=True, description="選択肢をシャッフルするか")
    
    # === 結果 ===
    score: int = Field(ge=0, description="現在のスコア")
    answered_questions: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="回答済み問題のリスト"
    )
    wrong_questions: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="間違えた問題のリスト"
    )
    
    @field_validator('current_index')
    @classmethod
    def validate_current_index(cls, v: int, info) -> int:
        """現在のインデックスが総問題数を超えないかチェック"""
        if 'total_questions' in info.data and v > info.data['total_questions']:
            raise ValueError("現在のインデックスが総問題数を超えています")
        return v
    
    def get_progress_percentage(self) -> float:
        """進行状況をパーセンテージで取得"""
        if self.total_questions == 0:
            return 0.0
        return (self.current_index / self.total_questions) * 100
    
    def get_accuracy(self) -> float:
        """現在の正答率を取得"""
        if self.current_index == 0:
            return 0.0
        return (self.score / self.current_index) * 100
    
    def is_completed(self) -> bool:
        """クイズが完了したかどうか"""
        return self.current_index >= self.total_questions


class DataQualityReport(BaseModel):
    """
    データ品質レポートのモデル
    CSVファイルの品質をチェックした結果
    """
    model_config = ConfigDict(extra='forbid')
    
    # === 基本情報 ===
    file_path: str = Field(description="チェックしたファイルのパス")
    total_questions: int = Field(ge=0, description="総問題数")
    valid_questions: int = Field(ge=0, description="有効な問題数")
    
    # === 品質指標 ===
    has_explanations_count: int = Field(ge=0, description="解説がある問題数")
    has_option_explanations_count: int = Field(ge=0, description="選択肢解説がある問題数")
    has_metadata_count: int = Field(ge=0, description="メタデータがある問題数")
    
    # === 問題リスト ===
    validation_errors: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="バリデーションエラーのリスト"
    )
    warnings: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="警告のリスト"
    )
    
    # === 品質スコア ===
    quality_score: float = Field(ge=0.0, le=100.0, description="品質スコア（0-100）")
    
    def get_success_rate(self) -> float:
        """成功率を取得"""
        if self.total_questions == 0:
            return 0.0
        return (self.valid_questions / self.total_questions) * 100
    
    def get_explanation_coverage(self) -> float:
        """解説のカバー率を取得"""
        if self.valid_questions == 0:
            return 0.0
        return (self.has_explanations_count / self.valid_questions) * 100
    
    def get_metadata_coverage(self) -> float:
        """メタデータのカバー率を取得"""
        if self.valid_questions == 0:
            return 0.0
        return (self.has_metadata_count / self.valid_questions) * 100
    
    def is_high_quality(self) -> bool:
        """高品質なデータかどうか判定"""
        return (
            self.quality_score >= 80.0 and
            self.get_success_rate() >= 95.0 and
            len(self.validation_errors) == 0
        )