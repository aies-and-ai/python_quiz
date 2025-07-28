"""
アプリケーション設定管理
シンプルなJSON設定システム
"""

import json
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional


@dataclass
class Settings:
    """アプリケーション設定"""
    
    # データベース設定
    database_url: str = "sqlite:///quiz.db"
    
    # UI設定
    window_width: int = 800
    window_height: int = 600
    window_title: str = "4択クイズアプリ"
    
    # ゲーム設定
    shuffle_questions: bool = True
    shuffle_options: bool = True
    default_question_count: int = 10
    
    # デバッグ設定
    debug: bool = False
    log_level: str = "INFO"
    
    @classmethod
    def load(cls, config_path: str = "config.json") -> 'Settings':
        """設定ファイルから読み込み（なければデフォルト値を使用）"""
        config_file = Path(config_path)
        
        if config_file.exists():
            try:
                with open(config_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return cls(**data)
            except (json.JSONDecodeError, TypeError) as e:
                print(f"設定ファイル読み込みエラー: {e}")
                print("デフォルト設定を使用します")
        
        return cls()
    
    def save(self, config_path: str = "config.json") -> None:
        """設定ファイルに保存"""
        try:
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(asdict(self), f, indent=2, ensure_ascii=False)
            print(f"設定を保存しました: {config_path}")
        except Exception as e:
            print(f"設定保存エラー: {e}")
    
    def get_database_path(self) -> Optional[str]:
        """SQLiteファイルパスを取得"""
        if self.database_url.startswith("sqlite:///"):
            return self.database_url.replace("sqlite:///", "")
        return None


# グローバル設定インスタンス
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """グローバル設定インスタンスを取得"""
    global _settings
    if _settings is None:
        _settings = Settings.load()
    return _settings


def reload_settings() -> None:
    """設定を再読み込み"""
    global _settings
    _settings = Settings.load()


# 便利関数
def get_setting(key: str, default=None):
    """個別設定値を取得"""
    settings = get_settings()
    return getattr(settings, key, default)