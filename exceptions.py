"""
クイズアプリ用のカスタム例外クラス
"""

class QuizAppError(Exception):
    """クイズアプリの基底例外クラス"""
    pass

class CSVFormatError(QuizAppError):
    """CSV形式に関するエラー"""
    pass

class QuizDataError(QuizAppError):
    """クイズデータに関するエラー"""
    pass

class FileNotFoundError(QuizAppError):
    """ファイルが見つからない場合のエラー"""
    pass