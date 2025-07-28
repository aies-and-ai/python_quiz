# utils/logger.py
"""
ログシステム - 責任明確化版
Web API対応とシンプルなログ機能
"""

import logging
import logging.handlers
import sys
import os
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime


class QuizAppLogger:
    """クイズアプリケーション専用ロガー"""
    
    def __init__(self, name: str = "quiz_app"):
        self.name = name
        self.logger = logging.getLogger(name)
        self._configured = False
        self._handlers_added = False
    
    def configure(self, 
                  level: str = "INFO",
                  to_file: bool = False,
                  file_path: str = "quiz_app.log",
                  format_string: str = None) -> None:
        """ロガーを設定"""
        if self._configured:
            return
        
        # ログレベル設定
        log_level = getattr(logging, level.upper(), logging.INFO)
        self.logger.setLevel(log_level)
        
        # 既存ハンドラーをクリア（重複防止）
        if self._handlers_added:
            self.logger.handlers.clear()
        
        # フォーマッター
        if format_string is None:
            format_string = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        
        formatter = logging.Formatter(
            format_string,
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # コンソールハンドラー
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(log_level)
        console_handler.setFormatter(formatter)
        self.logger.addHandler(console_handler)
        
        # ファイルハンドラー（必要な場合）
        if to_file:
            self._add_file_handler(file_path, formatter, log_level)
        
        # 親ロガーへの伝播を無効化（重複ログ防止）
        self.logger.propagate = False
        
        self._configured = True
        self._handlers_added = True
    
    def _add_file_handler(self, file_path: str, formatter: logging.Formatter, level: int):
        """ファイルハンドラーを追加"""
        try:
            # ログディレクトリを作成
            log_file = Path(file_path)
            log_file.parent.mkdir(parents=True, exist_ok=True)
            
            # ローテーティングファイルハンドラー（10MB, 5ファイル保持）
            file_handler = logging.handlers.RotatingFileHandler(
                file_path,
                maxBytes=10*1024*1024,  # 10MB
                backupCount=5,
                encoding='utf-8'
            )
            file_handler.setLevel(level)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
            
        except Exception as e:
            # ファイルハンドラーの追加に失敗してもコンソール出力は継続
            print(f"警告: ファイルログの設定に失敗しました: {e}")
    
    def get_logger(self) -> logging.Logger:
        """設定済みロガーを取得"""
        if not self._configured:
            self.configure()
        return self.logger
    
    def set_level(self, level: str) -> None:
        """ログレベルを動的に変更"""
        log_level = getattr(logging, level.upper(), logging.INFO)
        self.logger.setLevel(log_level)
        
        # 全ハンドラーのレベルも更新
        for handler in self.logger.handlers:
            handler.setLevel(log_level)
    
    def add_context(self, **context) -> 'ContextLogger':
        """コンテキスト付きロガーを作成"""
        return ContextLogger(self.logger, context)


class ContextLogger:
    """コンテキスト情報付きロガー"""
    
    def __init__(self, logger: logging.Logger, context: Dict[str, Any]):
        self.logger = logger
        self.context = context
    
    def _format_message(self, message: str) -> str:
        """コンテキスト情報を含むメッセージを作成"""
        if self.context:
            context_str = " | ".join([f"{k}={v}" for k, v in self.context.items()])
            return f"[{context_str}] {message}"
        return message
    
    def info(self, message: str) -> None:
        self.logger.info(self._format_message(message))
    
    def error(self, message: str) -> None:
        self.logger.error(self._format_message(message))
    
    def warning(self, message: str) -> None:
        self.logger.warning(self._format_message(message))
    
    def debug(self, message: str) -> None:
        self.logger.debug(self._format_message(message))


# グローバルロガーインスタンス
_global_logger: Optional[QuizAppLogger] = None


def get_logger(name: str = "quiz_app") -> logging.Logger:
    """グローバルロガーを取得"""
    global _global_logger
    
    if _global_logger is None:
        _global_logger = QuizAppLogger(name)
        
        # 設定ファイルから設定を読み込み（可能な場合）
        try:
            from app.config import get_settings
            settings = get_settings()
            log_config = settings.get_log_config()
            
            _global_logger.configure(
                level=log_config['level'],
                to_file=log_config['to_file'],
                file_path=log_config['file_path'],
                format_string=log_config['format']
            )
        except ImportError:
            # 設定ファイルが利用できない場合はデフォルト設定
            _global_logger.configure()
    
    return _global_logger.get_logger()


def get_context_logger(**context) -> ContextLogger:
    """コンテキスト付きロガーを取得"""
    base_logger = get_logger()
    return ContextLogger(base_logger, context)


def set_log_level(level: str) -> None:
    """グローバルログレベルを設定"""
    global _global_logger
    if _global_logger:
        _global_logger.set_level(level)
    else:
        # ロガーが未初期化の場合は作成して設定
        logger = get_logger()
        _global_logger.set_level(level)


def configure_logging(
    level: str = "INFO",
    to_file: bool = False,
    file_path: str = "quiz_app.log",
    format_string: str = None
) -> None:
    """ログシステムを設定"""
    global _global_logger
    
    if _global_logger is None:
        _global_logger = QuizAppLogger()
    
    _global_logger.configure(level, to_file, file_path, format_string)


def reset_logging() -> None:
    """ログシステムをリセット（テスト用）"""
    global _global_logger
    if _global_logger:
        _global_logger.logger.handlers.clear()
        _global_logger._configured = False
        _global_logger._handlers_added = False
    _global_logger = None


# 便利関数

def log_info(message: str, **context) -> None:
    """INFO レベルでログ出力"""
    if context:
        logger = get_context_logger(**context)
        logger.info(message)
    else:
        get_logger().info(message)


def log_error(message: str, **context) -> None:
    """ERROR レベルでログ出力"""
    if context:
        logger = get_context_logger(**context)
        logger.error(message)
    else:
        get_logger().error(message)


def log_warning(message: str, **context) -> None:
    """WARNING レベルでログ出力"""
    if context:
        logger = get_context_logger(**context)
        logger.warning(message)
    else:
        get_logger().warning(message)


def log_debug(message: str, **context) -> None:
    """DEBUG レベルでログ出力"""
    if context:
        logger = get_context_logger(**context)
        logger.debug(message)
    else:
        get_logger().debug(message)


# FastAPI用のログ設定

def setup_fastapi_logging() -> None:
    """FastAPI用のログ設定"""
    # FastAPI関連のロガー設定
    uvicorn_logger = logging.getLogger("uvicorn")
    uvicorn_access_logger = logging.getLogger("uvicorn.access")
    fastapi_logger = logging.getLogger("fastapi")
    
    # アプリケーションログと統一
    app_logger = get_logger()
    handler = app_logger.handlers[0] if app_logger.handlers else None
    
    if handler:
        uvicorn_logger.handlers = [handler]
        uvicorn_access_logger.handlers = [handler]
        fastapi_logger.handlers = [handler]
        
        uvicorn_logger.propagate = False
        uvicorn_access_logger.propagate = False
        fastapi_logger.propagate = False


# パフォーマンス測定用のログ

class PerformanceLogger:
    """パフォーマンス測定用ロガー"""
    
    def __init__(self, operation: str, logger: logging.Logger = None):
        self.operation = operation
        self.logger = logger or get_logger()
        self.start_time = None
    
    def __enter__(self):
        self.start_time = datetime.now()
        self.logger.debug(f"開始: {self.operation}")
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration = (datetime.now() - self.start_time).total_seconds()
            
            if exc_type is None:
                self.logger.debug(f"完了: {self.operation} ({duration:.3f}秒)")
            else:
                self.logger.error(f"エラー: {self.operation} ({duration:.3f}秒) - {exc_val}")


def performance_log(operation: str):
    """パフォーマンス測定デコレータ"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            with PerformanceLogger(f"{func.__name__}:{operation}"):
                return func(*args, **kwargs)
        return wrapper
    return decorator


# ログ情報の取得

def get_log_status() -> Dict[str, Any]:
    """ログシステムの状態を取得"""
    global _global_logger
    
    if _global_logger is None:
        return {
            'configured': False,
            'level': 'UNKNOWN',
            'handlers': []
        }
    
    logger = _global_logger.logger
    
    return {
        'configured': _global_logger._configured,
        'level': logging.getLevelName(logger.level),
        'handlers': [
            {
                'type': type(handler).__name__,
                'level': logging.getLevelName(handler.level)
            }
            for handler in logger.handlers
        ],
        'name': logger.name
    }