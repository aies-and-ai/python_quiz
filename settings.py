# settings.py
"""
強化された設定管理システム
.env ファイル対応 + 型安全な設定管理
"""

import os
from pathlib import Path
from typing import Dict, Any, Optional, Union
from pydantic import field_validator, Field
from pydantic_settings import BaseSettings
from logger import get_logger
from enhanced_exceptions import ConfigurationError


class QuizAppSettings(BaseSettings):
    """
    クイズアプリの設定クラス（pydantic BaseSettings使用）
    環境変数と.envファイルから自動読み込み
    """
    
    # === データ保存設定 ===
    data_file: str = Field(default="quiz_history.json", description="履歴保存ファイル")
    auto_save: bool = Field(default=True, description="自動保存するかどうか")
    backup_enabled: bool = Field(default=True, description="バックアップを作成するかどうか")
    max_backup_files: int = Field(default=5, ge=1, le=20, description="保持するバックアップファイル数")
    
    # === ゲーム設定 ===
    shuffle_questions: bool = Field(default=True, description="問題の順序をシャッフルするかどうか")
    shuffle_options: bool = Field(default=True, description="選択肢の順序をシャッフルするかどうか")
    show_progress: bool = Field(default=True, description="進行状況を表示するかどうか")
    enable_hints: bool = Field(default=False, description="ヒント機能を有効にするかどうか")
    
    # === ファイル設定 ===
    default_csv_file: str = Field(default="sample_quiz.csv", description="デフォルトCSVファイル")
    csv_encoding: str = Field(default="utf-8", description="CSVファイルのエンコーディング")
    max_file_size_mb: int = Field(default=50, ge=1, le=500, description="最大ファイルサイズ(MB)")
    
    # === UI設定 ===
    window_width: int = Field(default=800, ge=600, le=1600, description="ウィンドウ幅")
    window_height: int = Field(default=800, ge=600, le=1200, description="ウィンドウ高さ")
    window_title: str = Field(default="4択クイズアプリ", description="ウィンドウタイトル")
    theme: str = Field(default="default", description="UIテーマ")
    font_size: int = Field(default=12, ge=8, le=20, description="フォントサイズ")
    
    # === ログ設定 ===
    log_level: str = Field(default="INFO", description="ログレベル")
    log_max_size_mb: int = Field(default=10, ge=1, le=100, description="ログファイル最大サイズ(MB)")
    log_backup_count: int = Field(default=5, ge=1, le=20, description="ログファイルバックアップ数")
    console_log_enabled: bool = Field(default=True, description="コンソールログを有効にするかどうか")
    
    # === パフォーマンス設定 ===
    max_questions_per_quiz: int = Field(default=100, ge=1, le=1000, description="1回のクイズの最大問題数")
    cache_enabled: bool = Field(default=True, description="キャッシュを有効にするかどうか")
    preload_questions: bool = Field(default=True, description="問題を事前読み込みするかどうか")
    
    # === 開発・デバッグ設定 ===
    debug_mode: bool = Field(default=False, description="デバッグモード")
    performance_monitoring: bool = Field(default=False, description="パフォーマンス監視")
    error_reporting: bool = Field(default=True, description="エラーレポート送信")
    
    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "env_prefix": "QUIZ_APP_"
    }
    
    @field_validator('log_level')
    @classmethod
    def validate_log_level(cls, v):
        """ログレベルの妥当性をチェック"""
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if v.upper() not in valid_levels:
            raise ValueError(f"log_level must be one of {valid_levels}")
        return v.upper()
    
    @field_validator('theme')
    @classmethod
    def validate_theme(cls, v):
        """テーマの妥当性をチェック"""
        valid_themes = ['default', 'dark', 'light', 'blue', 'green']
        if v not in valid_themes:
            raise ValueError(f"theme must be one of {valid_themes}")
        return v
    
    @field_validator('csv_encoding')
    @classmethod
    def validate_encoding(cls, v):
        """エンコーディングの妥当性をチェック"""
        try:
            # エンコーディングが有効かテスト
            "test".encode(v)
            return v
        except LookupError:
            raise ValueError(f"Invalid encoding: {v}")
    
    @field_validator('data_file', 'default_csv_file')
    @classmethod
    def validate_file_paths(cls, v):
        """ファイルパスの妥当性をチェック"""
        if not v or len(v.strip()) == 0:
            raise ValueError("File path cannot be empty")
        
        # 不正な文字をチェック
        invalid_chars = ['<', '>', ':', '"', '|', '?', '*']
        if any(char in v for char in invalid_chars):
            raise ValueError(f"File path contains invalid characters: {v}")
        
        return v.strip()


class SettingsManager:
    """設定管理クラス"""
    
    def __init__(self, settings_file: Optional[str] = None):
        """
        初期化
        
        Args:
            settings_file: カスタム設定ファイルパス（オプション）
        """
        self.logger = get_logger()
        self.settings_file = settings_file
        self._settings: Optional[QuizAppSettings] = None
        self._load_settings()
    
    def _load_settings(self) -> None:
        """設定を読み込み"""
        try:
            # .envファイルの存在確認
            env_file = Path(".env")
            if env_file.exists():
                self.logger.info(f"Loading settings from .env file: {env_file.absolute()}")
            else:
                self.logger.info("No .env file found, using default settings and environment variables")
            
            # 設定の読み込み
            self._settings = QuizAppSettings()
            
            self.logger.info("Settings loaded successfully")
            self._log_current_settings()
            
        except Exception as e:
            error_msg = f"Failed to load settings: {str(e)}"
            self.logger.error(error_msg)
            raise ConfigurationError(
                message=error_msg,
                original_error=e,
                user_message="設定の読み込みに失敗しました。設定ファイルをご確認ください。"
            )
    
    def _log_current_settings(self) -> None:
        """現在の設定をログに記録（機密情報は除外）"""
        settings_dict = self._settings.dict()
        
        # ログに記録する設定（機密情報を除外）
        log_settings = {
            key: value for key, value in settings_dict.items()
            if not any(sensitive in key.lower() for sensitive in ['password', 'secret', 'token', 'key'])
        }
        
        self.logger.debug(f"Current settings: {log_settings}")
    
    def get_settings(self) -> QuizAppSettings:
        """現在の設定を取得"""
        if self._settings is None:
            self._load_settings()
        return self._settings
    
    def reload_settings(self) -> None:
        """設定を再読み込み"""
        self.logger.info("Reloading settings...")
        self._load_settings()
    
    def get_value(self, key: str, default: Any = None) -> Any:
        """設定値を取得"""
        settings = self.get_settings()
        return getattr(settings, key, default)
    
    def update_setting(self, key: str, value: Any) -> None:
        """設定値を更新（メモリ内のみ）"""
        if self._settings is None:
            self._load_settings()
        
        if hasattr(self._settings, key):
            setattr(self._settings, key, value)
            self.logger.info(f"Setting updated: {key} = {value}")
        else:
            raise ConfigurationError(
                message=f"Unknown setting key: {key}",
                user_message=f"不明な設定項目です: {key}"
            )
    
    def save_to_env_file(self, file_path: str = ".env") -> None:
        """現在の設定を.envファイルに保存"""
        try:
            settings = self.get_settings()
            settings_dict = settings.dict()
            
            env_content = []
            env_content.append("# クイズアプリ設定ファイル")
            env_content.append("# このファイルを編集して設定をカスタマイズできます")
            env_content.append("")
            
            # カテゴリ別に設定を整理
            categories = {
                "データ保存設定": ["data_file", "auto_save", "backup_enabled", "max_backup_files"],
                "ゲーム設定": ["shuffle_questions", "shuffle_options", "show_progress", "enable_hints"],
                "ファイル設定": ["default_csv_file", "csv_encoding", "max_file_size_mb"],
                "UI設定": ["window_width", "window_height", "window_title", "theme", "font_size"],
                "ログ設定": ["log_level", "log_max_size_mb", "log_backup_count", "console_log_enabled"],
                "パフォーマンス設定": ["max_questions_per_quiz", "cache_enabled", "preload_questions"],
                "開発設定": ["debug_mode", "performance_monitoring", "error_reporting"]
            }
            
            for category, keys in categories.items():
                env_content.append(f"# {category}")
                for key in keys:
                    if key in settings_dict:
                        env_key = f"QUIZ_APP_{key.upper()}"
                        value = settings_dict[key]
                        # ブール値の変換
                        if isinstance(value, bool):
                            value = "true" if value else "false"
                        env_content.append(f"{env_key}={value}")
                env_content.append("")
            
            # ファイルに書き込み
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write('\n'.join(env_content))
            
            self.logger.info(f"Settings saved to {file_path}")
            
        except Exception as e:
            error_msg = f"Failed to save settings to {file_path}: {str(e)}"
            self.logger.error(error_msg)
            raise ConfigurationError(
                message=error_msg,
                original_error=e,
                user_message="設定ファイルの保存に失敗しました。"
            )
    
    def validate_settings(self) -> Dict[str, Any]:
        """設定の妥当性を検証"""
        validation_result = {
            "is_valid": True,
            "errors": [],
            "warnings": []
        }
        
        try:
            settings = self.get_settings()
            
            # データファイルのパス確認
            data_file_path = Path(settings.data_file)
            if data_file_path.is_absolute() and not data_file_path.parent.exists():
                validation_result["warnings"].append(f"Data file directory does not exist: {data_file_path.parent}")
            
            # CSVファイルの確認
            csv_file_path = Path(settings.default_csv_file)
            if not csv_file_path.exists():
                validation_result["warnings"].append(f"Default CSV file not found: {csv_file_path}")
            
            # ウィンドウサイズの妥当性
            if settings.window_width > settings.window_height * 3:
                validation_result["warnings"].append("Window width seems unusually large compared to height")
            
            # ログ設定の確認
            log_dir = Path("logs")
            if not log_dir.exists():
                validation_result["warnings"].append("Log directory does not exist (will be created automatically)")
            
        except Exception as e:
            validation_result["is_valid"] = False
            validation_result["errors"].append(str(e))
        
        return validation_result
    
    def get_config_summary(self) -> Dict[str, Any]:
        """設定サマリーを取得（デバッグ・サポート用）"""
        settings = self.get_settings()
        validation = self.validate_settings()
        
        return {
            "settings_loaded": self._settings is not None,
            "env_file_exists": Path(".env").exists(),
            "validation": validation,
            "key_settings": {
                "auto_save": settings.auto_save,
                "shuffle_questions": settings.shuffle_questions,
                "log_level": settings.log_level,
                "debug_mode": settings.debug_mode,
                "window_size": f"{settings.window_width}x{settings.window_height}"
            }
        }


# グローバルな設定管理インスタンス
_settings_manager: Optional[SettingsManager] = None


def get_settings_manager() -> SettingsManager:
    """グローバルな設定管理インスタンスを取得"""
    global _settings_manager
    if _settings_manager is None:
        _settings_manager = SettingsManager()
    return _settings_manager


def reset_settings_manager() -> None:
    """グローバルな設定管理インスタンスをリセット（テスト用）"""
    global _settings_manager
    _settings_manager = None


def get_settings() -> QuizAppSettings:
    """現在の設定を取得（便利関数）"""
    return get_settings_manager().get_settings()


def get_setting(key: str, default: Any = None) -> Any:
    """設定値を取得（便利関数）"""
    return get_settings_manager().get_value(key, default)


def reload_settings() -> None:
    """設定を再読み込み（便利関数）"""
    global _settings_manager
    if _settings_manager is not None:
        _settings_manager.reload_settings()
    else:
        _settings_manager = SettingsManager()


def create_default_env_file() -> None:
    """デフォルト.envファイルを作成"""
    if not Path(".env").exists():
        get_settings_manager().save_to_env_file()
        print("✅ .envファイルを作成しました。設定をカスタマイズできます。")
    else:
        print("ℹ️  .envファイルは既に存在します。")