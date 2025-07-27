# database/models.py
"""
SQLAlchemyモデル定義
既存のpydanticモデルと連携するDBテーブル構造
"""

from sqlalchemy import Column, Integer, String, Text, JSON, DateTime, Boolean, Float, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
from typing import List, Dict, Any, Optional
import json
import uuid

Base = declarative_base()


class DatabaseQuestion(Base):
    """問題テーブル - csv_reader.pyの問題データを格納"""
    __tablename__ = 'questions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # 基本問題データ
    question = Column(Text, nullable=False, comment="問題文")
    options = Column(JSON, nullable=False, comment="選択肢リスト[選択肢1,選択肢2,選択肢3,選択肢4]")
    correct_answer = Column(Integer, nullable=False, comment="正解番号(0-3)")
    explanation = Column(Text, comment="全体解説")
    option_explanations = Column(JSON, comment="選択肢別解説リスト")
    
    # メタデータ（既存のextra_dataフィールドに対応）
    title = Column(String(200), comment="問題タイトル")
    genre = Column(String(50), comment="ジャンル（数学、歴史等）")
    difficulty = Column(String(20), comment="難易度（初級、中級、上級等）")
    tags = Column(String(200), comment="タグ（カンマ区切り）")
    source = Column(String(100), comment="出典")
    
    # 追加メタデータ（将来拡張用）
    custom_metadata = Column(JSON, comment="その他のカスタムメタデータ")
    
    # 問題管理用
    is_active = Column(Boolean, default=True, nullable=False, comment="アクティブ状態")
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # CSV由来情報
    csv_source_file = Column(String(255), comment="元のCSVファイル名")
    csv_import_date = Column(DateTime, comment="CSVインポート日時")
    
    def to_legacy_dict(self) -> Dict[str, Any]:
        """既存のクイズデータ形式（辞書）に変換"""
        # extra_dataの構築
        extra_data = {}
        if self.title: extra_data['title'] = self.title
        if self.genre: extra_data['genre'] = self.genre
        if self.difficulty: extra_data['difficulty'] = self.difficulty
        if self.tags: extra_data['tags'] = self.tags
        if self.source: extra_data['source'] = self.source
        if self.custom_metadata: extra_data.update(self.custom_metadata)
        
        return {
            'question': self.question,
            'options': self.options,
            'correct_answer': self.correct_answer,
            'explanation': self.explanation or '',
            'option_explanations': self.option_explanations or ['', '', '', ''],
            'extra_data': extra_data
        }
    
    @classmethod
    def from_legacy_dict(cls, question_dict: Dict[str, Any], csv_filename: str = None) -> 'DatabaseQuestion':
        """既存のクイズデータ形式から作成"""
        extra_data = question_dict.get('extra_data', {})
        
        # custom_metadataの抽出（既知フィールド以外）
        known_fields = {'title', 'genre', 'difficulty', 'tags', 'source'}
        custom_metadata = {k: v for k, v in extra_data.items() if k not in known_fields}
        
        return cls(
            question=question_dict['question'],
            options=question_dict['options'],
            correct_answer=question_dict['correct_answer'],
            explanation=question_dict.get('explanation'),
            option_explanations=question_dict.get('option_explanations', ['', '', '', '']),
            title=extra_data.get('title'),
            genre=extra_data.get('genre'),
            difficulty=extra_data.get('difficulty'),
            tags=extra_data.get('tags'),
            source=extra_data.get('source'),
            custom_metadata=custom_metadata if custom_metadata else None,
            csv_source_file=csv_filename,
            csv_import_date=datetime.utcnow() if csv_filename else None
        )


class DatabaseQuizSession(Base):
    """クイズセッションテーブル - 1回のクイズプレイを管理"""
    __tablename__ = 'quiz_sessions'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    session_id = Column(String(36), unique=True, nullable=False, comment="セッションUUID")
    
    # セッション設定
    total_questions = Column(Integer, nullable=False, comment="総問題数")
    shuffle_questions = Column(Boolean, default=True, comment="問題順シャッフル")
    shuffle_options = Column(Boolean, default=True, comment="選択肢順シャッフル")
    
    # 進行状況
    current_index = Column(Integer, default=0, comment="現在の問題インデックス")
    score = Column(Integer, default=0, comment="現在のスコア")
    
    # セッション状態
    status = Column(String(20), default='active', comment="状態：active/completed/abandoned")
    started_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at = Column(DateTime, comment="完了日時")
    
    # データ（JSON形式）
    question_sequence = Column(JSON, comment="出題順序[question_id1, question_id2, ...]")
    settings_snapshot = Column(JSON, comment="セッション開始時の設定スナップショット")
    
    # 結果サマリー（完了時に計算）
    final_accuracy = Column(Float, comment="最終正答率")
    wrong_count = Column(Integer, comment="間違えた問題数")
    
    # CSV由来情報（従来のファイル指定に対応）
    csv_source_file = Column(String(255), comment="使用したCSVファイル名")
    
    # リレーション
    answers = relationship("DatabaseQuizAnswer", back_populates="session", cascade="all, delete-orphan")
    
    @classmethod
    def create_new_session(cls, total_questions: int, csv_filename: str = None, **settings) -> 'DatabaseQuizSession':
        """新しいセッションを作成"""
        return cls(
            session_id=str(uuid.uuid4()),
            total_questions=total_questions,
            shuffle_questions=settings.get('shuffle_questions', True),
            shuffle_options=settings.get('shuffle_options', True),
            csv_source_file=csv_filename,
            settings_snapshot=settings
        )


class DatabaseQuizAnswer(Base):
    """個別回答テーブル - セッション内の各問題への回答を記録"""
    __tablename__ = 'quiz_answers'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # 外部キー
    session_id = Column(String(36), ForeignKey('quiz_sessions.session_id'), nullable=False)
    question_id = Column(Integer, ForeignKey('questions.id'), nullable=False)
    
    # 回答データ
    question_index = Column(Integer, nullable=False, comment="セッション内の問題番号")
    selected_option = Column(Integer, nullable=False, comment="選択した選択肢(0-3)")
    is_correct = Column(Boolean, nullable=False, comment="正解かどうか")
    answered_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # 問題スナップショット（シャッフル後の状態を保存）
    question_snapshot = Column(JSON, comment="回答時の問題データ（シャッフル後）")
    
    # リレーション
    session = relationship("DatabaseQuizSession", back_populates="answers")
    question = relationship("DatabaseQuestion")


class DatabaseUserHistory(Base):
    """ユーザー履歴テーブル - data_manager.pyの履歴データを格納"""
    __tablename__ = 'user_history'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # セッション参照
    session_id = Column(String(36), ForeignKey('quiz_sessions.session_id'), nullable=False)
    
    # 既存のdata_manager.pyと互換性を保つためのフィールド
    csv_file = Column(String(255), nullable=False, comment="使用したCSVファイル名")
    total_questions = Column(Integer, nullable=False)
    score = Column(Integer, nullable=False)
    accuracy = Column(Float, nullable=False, comment="正答率")
    wrong_count = Column(Integer, nullable=False)
    
    # 時間情報
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    duration_seconds = Column(Integer, comment="所要時間（秒）")
    
    # 詳細データ（JSON）
    wrong_questions_data = Column(JSON, comment="間違えた問題の詳細")
    performance_data = Column(JSON, comment="パフォーマンス詳細データ")
    
    # リレーション
    session = relationship("DatabaseQuizSession")
    
    @classmethod
    def from_legacy_result(cls, results: Dict[str, Any], session_id: str) -> 'DatabaseUserHistory':
        """既存のクイズ結果形式から作成"""
        return cls(
            session_id=session_id,
            csv_file=results.get('csv_file', ''),
            total_questions=results['total_questions'],
            score=results['score'],
            accuracy=results['accuracy'],
            wrong_count=len(results.get('wrong_questions', [])),
            wrong_questions_data=results.get('wrong_questions', []),
            performance_data=results.get('statistics', {})
        )


class DatabaseStatistics(Base):
    """統計情報テーブル - 集計済み統計データを保存"""
    __tablename__ = 'statistics'
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # 統計期間
    stat_date = Column(String(10), nullable=False, comment="統計日付(YYYY-MM-DD)")
    stat_type = Column(String(20), nullable=False, comment="統計種別（daily/weekly/monthly）")
    
    # 集計データ（JSON）
    total_quizzes = Column(Integer, default=0)
    total_questions = Column(Integer, default=0)
    total_correct = Column(Integer, default=0)
    overall_accuracy = Column(Float, default=0.0)
    
    # 詳細統計（JSON）
    genre_stats = Column(JSON, comment="ジャンル別統計")
    difficulty_stats = Column(JSON, comment="難易度別統計")
    popular_questions = Column(JSON, comment="人気問題ランキング")
    
    # 更新情報
    calculated_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    
    # ユニーク制約用のインデックス
    __table_args__ = (
        {'comment': '集計済み統計データ。日次/週次/月次で事前計算'}
    )


# インデックス定義（パフォーマンス最適化）
from sqlalchemy import Index

# 問題テーブルのインデックス
Index('idx_questions_genre', DatabaseQuestion.genre)
Index('idx_questions_difficulty', DatabaseQuestion.difficulty)
Index('idx_questions_active', DatabaseQuestion.is_active)
Index('idx_questions_csv_source', DatabaseQuestion.csv_source_file)

# セッションテーブルのインデックス
Index('idx_sessions_status', DatabaseQuizSession.status)
Index('idx_sessions_started_at', DatabaseQuizSession.started_at)
Index('idx_sessions_csv_source', DatabaseQuizSession.csv_source_file)

# 回答テーブルのインデックス
Index('idx_answers_session_id', DatabaseQuizAnswer.session_id)
Index('idx_answers_question_id', DatabaseQuizAnswer.question_id)

# 履歴テーブルのインデックス
Index('idx_history_timestamp', DatabaseUserHistory.timestamp)
Index('idx_history_csv_file', DatabaseUserHistory.csv_file)

# 統計テーブルのインデックス
Index('idx_stats_date_type', DatabaseStatistics.stat_date, DatabaseStatistics.stat_type)