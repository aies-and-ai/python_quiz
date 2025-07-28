"""
クイズアプリケーション例外クラス
シンプルな例外階層
"""


class QuizError(Exception):
    """クイズアプリケーション基底例外"""
    
    def __init__(self, message: str, user_message: str = None):
        super().__init__(message)
        self.user_message = user_message or message


class DataError(QuizError):
    """データ関連エラー"""
    pass


class SessionError(QuizError):
    """セッション関連エラー"""
    pass


class QuestionNotFoundError(DataError):
    """問題が見つからない"""
    
    def __init__(self, question_id: int = None):
        if question_id:
            message = f"問題が見つかりません: ID {question_id}"
            user_message = "指定された問題が見つかりませんでした"
        else:
            message = "問題が見つかりません"
            user_message = "問題データが存在しません"
        
        super().__init__(message, user_message)


class InvalidAnswerError(QuizError):
    """無効な回答"""
    
    def __init__(self, option: int = None):
        if option is not None:
            message = f"無効な選択肢: {option}"
            user_message = f"選択肢 {option + 1} は存在しません"
        else:
            message = "無効な回答です"
            user_message = "正しい選択肢を選んでください"
        
        super().__init__(message, user_message)


class SessionNotFoundError(SessionError):
    """セッションが見つからない"""
    
    def __init__(self, session_id: str = None):
        if session_id:
            message = f"セッションが見つかりません: {session_id}"
        else:
            message = "セッションが見つかりません"
        
        user_message = "クイズセッションが存在しません"
        super().__init__(message, user_message)


class DatabaseError(DataError):
    """データベース関連エラー"""
    
    def __init__(self, message: str, original_error: Exception = None):
        user_message = "データベースエラーが発生しました"
        super().__init__(message, user_message)
        self.original_error = original_error


class CSVImportError(DataError):
    """CSV インポートエラー"""
    
    def __init__(self, message: str, line_number: int = None):
        if line_number:
            full_message = f"CSV インポートエラー (行 {line_number}): {message}"
            user_message = f"{line_number}行目でエラーが発生しました: {message}"
        else:
            full_message = f"CSV インポートエラー: {message}"
            user_message = f"CSVファイルの読み込みに失敗しました: {message}"
        
        super().__init__(full_message, user_message)