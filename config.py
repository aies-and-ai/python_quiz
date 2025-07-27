# config.py (移行版)
"""
クイズアプリの設定値
Week 3: 新しい設定管理システムとの互換性を保ちつつ移行
"""

# 新しい設定管理システムをインポート
from settings import get_settings, get_setting
from logger import get_logger

# 移行通知のログ
logger = get_logger()
logger.info("Loading config.py - migrating to new settings system")

# 設定インスタンスを取得
_settings = get_settings()

# === 後方互換性のための変数定義 ===
# 既存コードが引き続き動作するように、従来の定数を新設定システムから取得

# データ保存設定
DATA_FILE = _settings.data_file
AUTO_SAVE = _settings.auto_save

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
    return {
        "data_file": DATA_FILE,
        "auto_save": AUTO_SAVE,
        "shuffle_questions": SHUFFLE_QUESTIONS,
        "shuffle_options": SHUFFLE_OPTIONS,
        "window_size": f"{WINDOW_WIDTH}x{WINDOW_HEIGHT}",
        "theme": _settings.theme,
        "font_size": _settings.font_size,
        "log_level": _settings.log_level
    }

def reload_config():
    """設定を再読み込み（新機能）"""
    global _settings, DATA_FILE, AUTO_SAVE, SHUFFLE_QUESTIONS, SHUFFLE_OPTIONS
    global DEFAULT_CSV_FILE, WINDOW_WIDTH, WINDOW_HEIGHT, WINDOW_TITLE
    global QUESTION_FONT, OPTION_FONT, SCORE_FONT, BUTTON_FONT
    global BG_COLOR, QUESTION_BG, CORRECT_COLOR, INCORRECT_COLOR, BUTTON_COLOR
    
    from settings import reload_settings
    reload_settings()
    
    # 設定を再取得
    _settings = get_settings()
    
    # 変数を更新
    DATA_FILE = _settings.data_file
    AUTO_SAVE = _settings.auto_save
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
    
    logger.info("Configuration reloaded from new settings system")

def is_debug_mode():
    """デバッグモードかどうかを確認"""
    return _settings.debug_mode

def get_max_questions():
    """1回のクイズの最大問題数を取得"""
    return _settings.max_questions_per_quiz

def get_csv_encoding():
    """CSVファイルのエンコーディングを取得"""
    return _settings.csv_encoding

# 移行完了のログ
logger.info("Config migration completed - all settings loaded from new system")

# 循環インポートを避けるため、QuizControllerのインポートは削除
# 必要に応じて各ファイルで直接インポートすること


# ===================================================================
# requirements.txt への追加
"""
Week 3で新たに必要になるパッケージ:

pydantic==2.5.0
pydantic-settings==2.1.0
python-dotenv==1.0.0

既存パッケージは引き続き使用:
- tkinter (標準ライブラリ)
- json (標準ライブラリ)  
- csv (標準ライブラリ)
- logging (標準ライブラリ)
"""