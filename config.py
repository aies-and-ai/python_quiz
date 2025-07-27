# config.py (移行版 + SQLite対応)
"""
クイズアプリの設定値
Week 3: 新しい設定管理システムとの互換性を保ちつつ移行
Week 4: SQLite データベース対応
"""

# 新しい設定管理システムをインポート
from settings import get_settings, get_setting
from logger import get_logger

# データベース統合用（オプション）
try:
    from database import get_database_connection, get_database_status
    DATABASE_AVAILABLE = True
except ImportError:
    DATABASE_AVAILABLE = False

# 移行通知のログ
logger = get_logger()
logger.info("Loading config.py - migrating to new settings system with database support")

# 設定インスタンスを取得
_settings = get_settings()

# === 後方互換性のための変数定義 ===
# 既存コードが引き続き動作するように、従来の定数を新設定システムから取得

# データ保存設定
DATA_FILE = _settings.data_file
AUTO_SAVE = _settings.auto_save

# データベース設定（新規追加）
USE_DATABASE = _settings.use_database
DATABASE_URL = _settings.database_url
DATABASE_TIMEOUT = _settings.database_timeout
AUTO_OPTIMIZE_DB = _settings.auto_optimize_db

# ゲーム設定  
SHUFFLE_QUESTIONS = _settings.shuffle_questions
SHUFFLE_OPTIONS = _settings.shuffle_options

# ファイル設定
DEFAULT_CSV_FILE = _settings.default_csv_file

# UI設定
WINDOW_WIDTH = _settings.window_width
WINDOW_HEIGHT = _settings.window_height
WINDOW_TITLE = _settings.window_title

# フォント設定（新設定システムのfont_sizeを基準に計算）
base_font_size = _settings.font_size
QUESTION_FONT = ("Arial", base_font_size + 4, "bold")
OPTION_FONT = ("Arial", base_font_size)
SCORE_FONT = ("Arial", base_font_size + 2, "bold")
BUTTON_FONT = ("Arial", base_font_size)

# 色設定（テーマに応じて動的に変更可能）
def _get_theme_colors():
    """テーマに応じた色設定を取得"""
    theme = _settings.theme
    
    if theme == "dark":
        return {
            "BG_COLOR": "#2b2b2b",
            "QUESTION_BG": "#3c3c3c",
            "CORRECT_COLOR": "#4CAF50",
            "INCORRECT_COLOR": "#f44336",
            "BUTTON_COLOR": "#555555"
        }
    elif theme == "blue":
        return {
            "BG_COLOR": "#e3f2fd",
            "QUESTION_BG": "#ffffff",
            "CORRECT_COLOR": "#4CAF50",
            "INCORRECT_COLOR": "#f44336",
            "BUTTON_COLOR": "#2196F3"
        }
    else:  # default theme
        return {
            "BG_COLOR": "#f0f0f0",
            "QUESTION_BG": "#ffffff",
            "CORRECT_COLOR": "#90EE90",
            "INCORRECT_COLOR": "#FFB6C1",
            "BUTTON_COLOR": "#e0e0e0"
        }

# テーマ色を適用
_theme_colors = _get_theme_colors()
BG_COLOR = _theme_colors["BG_COLOR"]
QUESTION_BG = _theme_colors["QUESTION_BG"] 
CORRECT_COLOR = _theme_colors["CORRECT_COLOR"]
INCORRECT_COLOR = _theme_colors["INCORRECT_COLOR"]
BUTTON_COLOR = _theme_colors["BUTTON_COLOR"]

# レイアウト設定
PADDING = 20
BUTTON_WIDTH = 50
BUTTON_HEIGHT = 3

# === 新機能への移行支援関数 ===

def get_current_settings_summary():
    """現在の設定のサマリーを取得"""
    summary = {
        "data_file": DATA_FILE,
        "auto_save": AUTO_SAVE,
        "use_database": USE_DATABASE,
        "database_url": DATABASE_URL.split('/')[-1] if DATABASE_URL else "N/A",  # ファイル名のみ
        "shuffle_questions": SHUFFLE_QUESTIONS,
        "shuffle_options": SHUFFLE_OPTIONS,
        "window_size": f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}",
        "theme": _settings.theme,
        "font_size": _settings.font_size,
        "log_level": _settings.log_level
    }
    
    # データベース状況を追加
    if DATABASE_AVAILABLE and USE_DATABASE:
        try:
            db_status = get_database_status()
            summary["database_status"] = db_status.get("connection_status", "unknown")
        except Exception:
            summary["database_status"] = "error"
    else:
        summary["database_status"] = "disabled"
    
    return summary

def reload_config():
    """設定を再読み込み（新機能 + DB対応）"""
    global _settings, DATA_FILE, AUTO_SAVE, USE_DATABASE, DATABASE_URL, DATABASE_TIMEOUT
    global SHUFFLE_QUESTIONS, SHUFFLE_OPTIONS, DEFAULT_CSV_FILE, WINDOW_WIDTH, WINDOW_HEIGHT, WINDOW_TITLE
    global QUESTION_FONT, OPTION_FONT, SCORE_FONT, BUTTON_FONT
    global BG_COLOR, QUESTION_BG, CORRECT_COLOR, INCORRECT_COLOR, BUTTON_COLOR
    
    from settings import reload_settings
    reload_settings()
    
    # 設定を再取得
    _settings = get_settings()
    
    # 変数を更新
    DATA_FILE = _settings.data_file
    AUTO_SAVE = _settings.auto_save
    USE_DATABASE = _settings.use_database
    DATABASE_URL = _settings.database_url
    DATABASE_TIMEOUT = _settings.database_timeout
    SHUFFLE_QUESTIONS = _settings.shuffle_questions
    SHUFFLE_OPTIONS = _settings.shuffle_options
    DEFAULT_CSV_FILE = _settings.default_csv_file
    WINDOW_WIDTH = _settings.window_width
    WINDOW_HEIGHT = _settings.window_height
    WINDOW_TITLE = _settings.window_title
    
    # フォント設定更新
    base_font_size = _settings.font_size
    QUESTION_FONT = ("Arial", base_font_size + 4, "bold")
    OPTION_FONT = ("Arial", base_font_size)
    SCORE_FONT = ("Arial", base_font_size + 2, "bold")
    BUTTON_FONT = ("Arial", base_font_size)
    
    # 色設定更新
    _theme_colors = _get_theme_colors()
    BG_COLOR = _theme_colors["BG_COLOR"]
    QUESTION_BG = _theme_colors["QUESTION_BG"]
    CORRECT_COLOR = _theme_colors["CORRECT_COLOR"]
    INCORRECT_COLOR = _theme_colors["INCORRECT_COLOR"]
    BUTTON_COLOR = _theme_colors["BUTTON_COLOR"]
    
    logger.info("Configuration reloaded from new settings system with database support")

def is_debug_mode():
    """デバッグモードかどうかを確認"""
    return _settings.debug_mode

def get_max_questions():
    """1回のクイズの最大問題数を取得"""
    return _settings.max_questions_per_quiz

def get_csv_encoding():
    """CSVファイルのエンコーディングを取得"""
    return _settings.csv_encoding

# === データベース関連の新機能 ===

def is_database_enabled():
    """データベースが有効かどうかを確認"""
    return DATABASE_AVAILABLE and USE_DATABASE

def get_database_url():
    """データベースURLを取得"""
    return DATABASE_URL if is_database_enabled() else None

def get_database_status_summary():
    """データベース状態のサマリーを取得"""
    if not DATABASE_AVAILABLE:
        return {
            "status": "unavailable",
            "message": "Database module not available"
        }
    
    if not USE_DATABASE:
        return {
            "status": "disabled",
            "message": "Database disabled in settings"
        }
    
    try:
        return get_database_status()
    except Exception as e:
        return {
            "status": "error",
            "message": str(e)
        }

def initialize_database():
    """データベースを初期化"""
    if not is_database_enabled():
        logger.warning("Database initialization skipped - not enabled")
        return False
    
    try:
        db_connection = get_database_connection(DATABASE_URL)
        logger.info("Database initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        return False

def get_data_storage_mode():
    """現在のデータ保存モードを取得"""
    if is_database_enabled():
        return "database"
    else:
        return "json_file"

def should_use_csv_import():
    """CSVファイルを自動インポートするかどうか"""
    return is_database_enabled() and _settings.preload_questions

def get_quiz_data_options():
    """QuizDataクラス用のオプションを取得"""
    return {
        "use_database": is_database_enabled(),
        "database_url": get_database_url(),
        "shuffle": SHUFFLE_QUESTIONS,
        "shuffle_options": SHUFFLE_OPTIONS
    }

def get_data_manager_options():
    """QuizDataManagerクラス用のオプションを取得"""
    return {
        "data_file": DATA_FILE,
        "use_database": is_database_enabled(),
        "database_url": get_database_url()
    }

# === 設定切り替え機能 ===

def switch_to_database_mode():
    """データベースモードに切り替え"""
    global USE_DATABASE
    
    if not DATABASE_AVAILABLE:
        logger.warning("Cannot switch to database mode - module not available")
        return False
    
    try:
        USE_DATABASE = True
        _settings.use_database = True
        logger.info("Switched to database mode")
        return True
    except Exception as e:
        logger.error(f"Failed to switch to database mode: {e}")
        return False

def switch_to_json_mode():
    """JSONファイルモードに切り替え"""
    global USE_DATABASE
    
    USE_DATABASE = False
    _settings.use_database = False
    logger.info("Switched to JSON file mode")

def toggle_database_mode():
    """データベースモードを切り替え"""
    if USE_DATABASE:
        switch_to_json_mode()
        return "json_file"
    else:
        success = switch_to_database_mode()
        return "database" if success else "json_file"

# === 互換性チェック ===

def check_compatibility():
    """設定の互換性をチェック"""
    issues = []
    
    # データベース関連のチェック
    if USE_DATABASE and not DATABASE_AVAILABLE:
        issues.append("Database is enabled in settings but database module is not available")
    
    if USE_DATABASE and DATABASE_AVAILABLE:
        try:
            db_status = get_database_status()
            if db_status.get("status") == "unhealthy":
                issues.append(f"Database connection issue: {db_status.get('error', 'Unknown error')}")
        except Exception as e:
            issues.append(f"Database status check failed: {e}")
    
    # ファイル関連のチェック
    if not USE_DATABASE and not DATA_FILE:
        issues.append("Neither database nor JSON file is properly configured")
    
    # CSVファイルのチェック
    import os
    if DEFAULT_CSV_FILE and not os.path.exists(DEFAULT_CSV_FILE):
        issues.append(f"Default CSV file not found: {DEFAULT_CSV_FILE}")
    
    return issues

def validate_current_config():
    """現在の設定を検証"""
    issues = check_compatibility()
    
    if issues:
        logger.warning(f"Configuration issues found: {len(issues)} issues")
        for issue in issues:
            logger.warning(f"  - {issue}")
        return False, issues
    else:
        logger.info("Configuration validation passed")
        return True, []

# === アプリケーション起動時の初期化 ===

def initialize_app_config():
    """アプリケーション起動時の設定初期化"""
    logger.info("Initializing application configuration...")
    
    # 設定の検証
    is_valid, issues = validate_current_config()
    
    if not is_valid:
        logger.warning(f"Configuration validation failed with {len(issues)} issues")
        # 自動修復を試行
        if _attempt_auto_fix():
            logger.info("Configuration auto-fix completed")
        else:
            logger.warning("Configuration auto-fix failed")
    
    # データベースの初期化（有効な場合）
    if is_database_enabled():
        if initialize_database():
            logger.info("Database initialization completed")
        else:
            logger.warning("Database initialization failed, falling back to JSON mode")
            switch_to_json_mode()
    
    # 設定サマリーをログ出力
    summary = get_current_settings_summary()
    logger.info(f"Configuration summary: {summary}")
    
    return is_valid

def _attempt_auto_fix():
    """設定の自動修復を試行"""
    try:
        # データベースが利用できない場合はJSONモードに切り替え
        if USE_DATABASE and not DATABASE_AVAILABLE:
            switch_to_json_mode()
            logger.info("Auto-fix: Switched to JSON mode due to unavailable database")
            return True
        
        return False
    except Exception as e:
        logger.error(f"Auto-fix failed: {e}")
        return False

# 移行完了のログ
logger.info("Config migration completed - all settings loaded from new system with database support")

# 循環インポートを避けるため、QuizControllerのインポートは削除
# 必要に応じて各ファイルで直接インポートすること

# ===================================================================
# requirements.txt への追加
"""
Week 3で新たに必要になるパッケージ:

pydantic==2.5.0
pydantic-settings==2.1.0
python-dotenv==1.0.0

Week 4で新たに必要になるパッケージ:

sqlalchemy==2.0.23

既存パッケージは引き続き使用:
- tkinter (標準ライブラリ)
- json (標準ライブラリ)  
- csv (標準ライブラリ)
- logging (標準ライブラリ)
- sqlite3 (標準ライブラリ)
"""

# === 使用例 ===
"""
# データベースモードでの使用例
if is_database_enabled():
    quiz_options = get_quiz_data_options()
    quiz_data = QuizData(**quiz_options)
else:
    # 従来通りのCSVモード
    quiz_data = QuizData(csv_file=DEFAULT_CSV_FILE)

# データマネージャーの初期化
data_options = get_data_manager_options()
data_manager = QuizDataManager(**data_options)

# 設定の動的切り替え
current_mode = toggle_database_mode()
print(f"Current storage mode: {current_mode}")
"""