# app/config.py
"""
アプリケーション設定管理 - 責任明確化版
Web API対応とシンプルな設定システム
"""

import json
import os
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Optional, Dict, Any


@dataclass
class Settings:
    """アプリケーション設定 - Web API対応版"""
    
    # データベース設定
    database_url: str = "sqlite:///quiz.db"
    database_pool_size: int = 5
    database_timeout: int = 30
    
    # Web API設定（Phase 3で使用）
    api_host: str = "0.0.0.0"
    api_port: int = 8000
    api_debug: bool = False
    api_reload: bool = False
    api_cors_origins: list = None
    
    # セキュリティ設定（将来拡張用）
    secret_key: str = "quiz-app-secret-key-change-in-production"
    session_timeout_minutes: int = 30
    
    # ゲーム設定
    shuffle_questions: bool = True
    shuffle_options: bool = True
    default_question_count: int = 10
    max_question_count: int = 100
    
    # ログ設定
    log_level: str = "INFO"
    log_to_file: bool = False
    log_file_path: str = "quiz_app.log"
    
    # パフォーマンス設定
    question_cache_size: int = 1000
    session_cleanup_interval_minutes: int = 60
    
    def __post_init__(self):
        """初期化後の処理"""
        # CORS設定のデフォルト値
        if self.api_cors_origins is None:
            self.api_cors_origins = [
                "http://localhost:3000",  # React開発サーバー
                "http://127.0.0.1:3000",
                "http://localhost:8080",  # 代替ポート
                "http://127.0.0.1:8080"
            ]
        
        # 環境変数からの上書き
        self._load_from_environment()
    
    def _load_from_environment(self):
        """環境変数から設定を読み込み"""
        env_mappings = {
            'DATABASE_URL': 'database_url',
            'API_HOST': 'api_host',
            'API_PORT': 'api_port',
            'API_DEBUG': 'api_debug',
            'LOG_LEVEL': 'log_level',
            'SECRET_KEY': 'secret_key'
        }
        
        for env_key, attr_name in env_mappings.items():
            env_value = os.getenv(env_key)
            if env_value is not None:
                # 型変換
                if attr_name in ['api_port', 'database_pool_size', 'database_timeout']:
                    try:
                        env_value = int(env_value)
                    except ValueError:
                        continue
                elif attr_name in ['api_debug', 'log_to_file', 'shuffle_questions', 'shuffle_options']:
                    env_value = env_value.lower() in ('true', '1', 'yes', 'on')
                
                setattr(self, attr_name, env_value)
    
    @classmethod
    def load(cls, config_path: str = "config.json") -> 'Settings':
        """設定ファイルから読み込み"""
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
            # 環境変数由来の設定は保存しない
            save_data = self._get_saveable_data()
            
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(save_data, f, indent=2, ensure_ascii=False)
            print(f"設定を保存しました: {config_path}")
        except Exception as e:
            print(f"設定保存エラー: {e}")
    
    def _get_saveable_data(self) -> Dict[str, Any]:
        """保存可能なデータのみを抽出"""
        data = asdict(self)
        
        # 機密情報や環境依存の設定を除外
        exclude_keys = ['secret_key']
        for key in exclude_keys:
            if key in data:
                data.pop(key)
        
        return data
    
    def get_database_path(self) -> Optional[str]:
        """SQLiteファイルパスを取得"""
        if self.database_url.startswith("sqlite:///"):
            return self.database_url.replace("sqlite:///", "")
        return None
    
    def get_api_url(self) -> str:
        """API URLを取得"""
        return f"http://{self.api_host}:{self.api_port}"
    
    def is_development(self) -> bool:
        """開発環境かどうかを判定"""
        return self.api_debug or self.log_level == "DEBUG"
    
    def is_production(self) -> bool:
        """本番環境かどうかを判定"""
        return not self.is_development()
    
    def get_log_config(self) -> Dict[str, Any]:
        """ログ設定を取得"""
        return {
            'level': self.log_level,
            'to_file': self.log_to_file,
            'file_path': self.log_file_path,
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        }
    
    def get_database_config(self) -> Dict[str, Any]:
        """データベース設定を取得"""
        return {
            'url': self.database_url,
            'pool_size': self.database_pool_size,
            'timeout': self.database_timeout
        }
    
    def get_api_config(self) -> Dict[str, Any]:
        """API設定を取得"""
        return {
            'host': self.api_host,
            'port': self.api_port,
            'debug': self.api_debug,
            'reload': self.api_reload,
            'cors_origins': self.api_cors_origins
        }
    
    def validate(self) -> list:
        """設定の妥当性をチェック"""
        errors = []
        
        # ポート番号チェック
        if not 1 <= self.api_port <= 65535:
            errors.append(f"無効なAPIポート番号: {self.api_port}")
        
        # ログレベルチェック
        valid_log_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if self.log_level.upper() not in valid_log_levels:
            errors.append(f"無効なログレベル: {self.log_level}")
        
        # 問題数チェック
        if self.default_question_count < 1:
            errors.append(f"無効なデフォルト問題数: {self.default_question_count}")
        
        if self.max_question_count < self.default_question_count:
            errors.append("最大問題数がデフォルト問題数より小さいです")
        
        # データベースURLチェック
        if not self.database_url:
            errors.append("データベースURLが設定されていません")
        
        return errors
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式に変換"""
        return asdict(self)


# グローバル設定インスタンス
_settings: Optional[Settings] = None


def get_settings() -> Settings:
    """グローバル設定インスタンスを取得"""
    global _settings
    if _settings is None:
        _settings = Settings.load()
        
        # 設定の妥当性チェック
        validation_errors = _settings.validate()
        if validation_errors:
            print("設定エラーが検出されました:")
            for error in validation_errors:
                print(f"  - {error}")
            print("一部機能が正常に動作しない可能性があります")
    
    return _settings


def reload_settings() -> None:
    """設定を再読み込み"""
    global _settings
    _settings = Settings.load()


def update_settings(**kwargs) -> None:
    """設定を動的に更新"""
    settings = get_settings()
    for key, value in kwargs.items():
        if hasattr(settings, key):
            setattr(settings, key, value)
        else:
            print(f"警告: 未知の設定キー '{key}' をスキップしました")


# 便利関数

def get_setting(key: str, default=None):
    """個別設定値を取得"""
    settings = get_settings()
    return getattr(settings, key, default)


def is_debug_mode() -> bool:
    """デバッグモードかどうかを判定"""
    return get_settings().is_development()


def get_database_url() -> str:
    """データベースURLを取得"""
    return get_settings().database_url


def get_api_config() -> Dict[str, Any]:
    """API設定を取得"""
    return get_settings().get_api_config()


def get_cors_origins() -> list:
    """CORS許可オリジンを取得"""
    return get_settings().api_cors_origins


# 設定ファイルの初期化（初回実行時）

def initialize_config_file(config_path: str = "config.json") -> None:
    """設定ファイルを初期化（存在しない場合のみ）"""
    if not Path(config_path).exists():
        settings = Settings()
        settings.save(config_path)
        print(f"設定ファイルを作成しました: {config_path}")


# 環境別設定の便利関数

def get_development_settings() -> Settings:
    """開発環境用設定を取得"""
    settings = Settings()
    settings.api_debug = True
    settings.api_reload = True
    settings.log_level = "DEBUG"
    settings.log_to_file = False
    return settings


def get_production_settings() -> Settings:
    """本番環境用設定を取得"""
    settings = Settings()
    settings.api_debug = False
    settings.api_reload = False
    settings.log_level = "INFO"
    settings.log_to_file = True
    settings.api_host = "0.0.0.0"
    return settings


# 設定の書き出し用ヘルパー

def export_config_template(output_path: str = "config.template.json") -> None:
    """設定テンプレートを出力"""
    template_settings = Settings()
    
    # コメント付きの設定例
    template_data = {
        "database_url": "sqlite:///quiz.db",
        "api_host": "0.0.0.0",
        "api_port": 8000,
        "api_debug": False,
        "log_level": "INFO",
        "shuffle_questions": True,
        "shuffle_options": True,
        "default_question_count": 10,
        "max_question_count": 100,
        "_comments": {
            "database_url": "データベース接続URL",
            "api_host": "APIサーバーのホスト (0.0.0.0 = 全てのインターフェース)",
            "api_port": "APIサーバーのポート番号",
            "api_debug": "デバッグモード (開発時のみtrue)",
            "log_level": "ログレベル (DEBUG, INFO, WARNING, ERROR, CRITICAL)",
            "shuffle_questions": "問題順をシャッフルするか",
            "shuffle_options": "選択肢順をシャッフルするか",
            "default_question_count": "デフォルトの問題数",
            "max_question_count": "最大問題数"
        }
    }
    
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(template_data, f, indent=2, ensure_ascii=False)
        print(f"設定テンプレートを出力しました: {output_path}")
    except Exception as e:
        print(f"テンプレート出力エラー: {e}")