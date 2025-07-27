# logger.py
"""
クイズアプリ用のログシステム
Web化準備も兼ねた包括的なログ設定
"""

import logging
import logging.handlers
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional


class QuizLogger:
    """クイズアプリ専用のログ管理クラス"""
    
    def __init__(self):
        self.logger = None
        self.log_dir = Path("logs")
        self.setup_logger()
    
    def setup_logger(self) -> None:
        """ログシステムのセットアップ"""
        # ログディレクトリの作成
        self.log_dir.mkdir(exist_ok=True)
        
        # メインロガーの設定
        self.logger = logging.getLogger("quiz_app")
        self.logger.setLevel(logging.DEBUG)
        
        # 既存のハンドラーをクリア（重複防止）
        if self.logger.handlers:
            self.logger.handlers.clear()
        
        # フォーマッター
        detailed_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(name)s:%(lineno)d | %(message)s'
        )
        simple_formatter = logging.Formatter(
            '%(asctime)s | %(levelname)-8s | %(message)s'
        )
        
        # 1. コンソールハンドラー（開発時用）
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(simple_formatter)
        self.logger.addHandler(console_handler)
        
        # 2. ファイルハンドラー（全ログ・ローテーション付き）
        file_handler = logging.handlers.RotatingFileHandler(
            filename=self.log_dir / "quiz_app.log",
            maxBytes=10*1024*1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(detailed_formatter)
        self.logger.addHandler(file_handler)
        
        # 3. エラー専用ファイルハンドラー
        error_handler = logging.handlers.RotatingFileHandler(
            filename=self.log_dir / "quiz_errors.log",
            maxBytes=5*1024*1024,  # 5MB
            backupCount=3,
            encoding='utf-8'
        )
        error_handler.setLevel(logging.ERROR)
        error_handler.setFormatter(detailed_formatter)
        self.logger.addHandler(error_handler)
        
        # 初期化完了ログ
        self.logger.info("=== Quiz App Logger Initialized ===")
    
    def get_logger(self) -> logging.Logger:
        """ロガーインスタンスを取得"""
        return self.logger
    
    def log_app_start(self, csv_file: str) -> None:
        """アプリ開始時のログ"""
        self.logger.info(f"Quiz App Started - CSV: {csv_file}")
    
    def log_app_end(self) -> None:
        """アプリ終了時のログ"""
        self.logger.info("Quiz App Ended")
        self.logger.info("=" * 50)
    
    def log_quiz_start(self, total_questions: int, csv_file: str) -> None:
        """クイズ開始時のログ"""
        self.logger.info(f"Quiz Started - {total_questions} questions from {csv_file}")
    
    def log_quiz_result(self, score: int, total: int, accuracy: float, csv_file: str) -> None:
        """クイズ結果のログ"""
        self.logger.info(f"Quiz Completed - Score: {score}/{total} ({accuracy:.1f}%) - {csv_file}")
    
    def log_answer(self, question_num: int, is_correct: bool, question_text: str = None) -> None:
        """回答時のログ"""
        result = "CORRECT" if is_correct else "WRONG"
        if question_text:
            # 問題文が長い場合は省略
            short_question = question_text[:50] + "..." if len(question_text) > 50 else question_text
            self.logger.debug(f"Q{question_num}: {result} - {short_question}")
        else:
            self.logger.debug(f"Q{question_num}: {result}")
    
    def log_csv_load(self, csv_file: str, question_count: int) -> None:
        """CSV読み込み時のログ"""
        self.logger.info(f"CSV Loaded - {question_count} questions from {csv_file}")
    
    def log_error(self, error: Exception, context: str = None) -> None:
        """エラーログ（詳細情報付き）"""
        if context:
            self.logger.error(f"Error in {context}: {type(error).__name__}: {str(error)}", exc_info=True)
        else:
            self.logger.error(f"Error: {type(error).__name__}: {str(error)}", exc_info=True)
    
    def log_user_action(self, action: str, details: str = None) -> None:
        """ユーザーアクション（将来のユーザビリティ分析用）"""
        if details:
            self.logger.info(f"User Action: {action} - {details}")
        else:
            self.logger.info(f"User Action: {action}")
    
    def log_performance(self, operation: str, duration_ms: float) -> None:
        """パフォーマンス測定ログ"""
        self.logger.debug(f"Performance: {operation} took {duration_ms:.2f}ms")


# グローバルロガーインスタンス
_quiz_logger = None

def get_logger() -> logging.Logger:
    """
    アプリ全体で使用するロガーを取得
    
    Returns:
        logging.Logger: 設定済みのロガー
    """
    global _quiz_logger
    if _quiz_logger is None:
        _quiz_logger = QuizLogger()
    return _quiz_logger.get_logger()

def setup_app_logging() -> QuizLogger:
    """
    アプリ起動時にログシステムを初期化
    
    Returns:
        QuizLogger: ロガー管理インスタンス
    """
    global _quiz_logger
    if _quiz_logger is None:
        _quiz_logger = QuizLogger()
    return _quiz_logger

def log_app_start(csv_file: str) -> None:
    """アプリ開始ログ（便利関数）"""
    if _quiz_logger:
        _quiz_logger.log_app_start(csv_file)

def log_app_end() -> None:
    """アプリ終了ログ（便利関数）"""
    if _quiz_logger:
        _quiz_logger.log_app_end()

def log_quiz_start(total_questions: int, csv_file: str) -> None:
    """クイズ開始ログ（便利関数）"""
    if _quiz_logger:
        _quiz_logger.log_quiz_start(total_questions, csv_file)

def log_quiz_result(score: int, total: int, accuracy: float, csv_file: str) -> None:
    """クイズ結果ログ（便利関数）"""
    if _quiz_logger:
        _quiz_logger.log_quiz_result(score, total, accuracy, csv_file)

def log_error(error: Exception, context: str = None) -> None:
    """エラーログ（便利関数）"""
    if _quiz_logger:
        _quiz_logger.log_error(error, context)
    else:
        # ロガーが初期化されていない場合の緊急処理
        print(f"EMERGENCY LOG - Error in {context}: {error}")

def log_user_action(action: str, details: str = None) -> None:
    """ユーザーアクションログ（便利関数）"""
    if _quiz_logger:
        _quiz_logger.log_user_action(action, details)