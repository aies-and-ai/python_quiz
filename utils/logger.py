"""
シンプルなログシステム
最小限の機能のみ実装
"""

import logging
import sys
from typing import Optional


def get_logger(name: str = "quiz_app") -> logging.Logger:
    """ロガーを取得（設定は一度だけ実行）"""
    logger = logging.getLogger(name)
    
    # 既に設定済みの場合はそのまま返す
    if logger.handlers:
        return logger
    
    # ログレベル設定
    logger.setLevel(logging.INFO)
    
    # コンソールハンドラー
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    
    # フォーマッター
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)
    
    # ハンドラーを追加
    logger.addHandler(console_handler)
    
    return logger


def set_log_level(level: str) -> None:
    """ログレベルを設定"""
    logger = get_logger()
    
    level_map = {
        'DEBUG': logging.DEBUG,
        'INFO': logging.INFO,
        'WARNING': logging.WARNING,
        'ERROR': logging.ERROR,
        'CRITICAL': logging.CRITICAL
    }
    
    if level.upper() in level_map:
        logger.setLevel(level_map[level.upper()])
        for handler in logger.handlers:
            handler.setLevel(level_map[level.upper()])
    else:
        logger.warning(f"Unknown log level: {level}")


# 便利関数
def log_info(message: str) -> None:
    """INFO レベルでログ出力"""
    get_logger().info(message)


def log_error(message: str) -> None:
    """ERROR レベルでログ出力"""
    get_logger().error(message)


def log_debug(message: str) -> None:
    """DEBUG レベルでログ出力"""
    get_logger().debug(message)