# app/core/exceptions.py
"""
クイズアプリケーション例外クラス - 責任明確化版
Web API対応とビジネス例外の整理
"""

from typing import Optional, Dict, Any


class QuizError(Exception):
    """クイズアプリケーション基底例外"""
    
    def __init__(self, message: str, user_message: str = None, error_code: str = None):
        super().__init__(message)
        self.user_message = user_message or message
        self.error_code = error_code or self.__class__.__name__.upper()
    
    def to_dict(self) -> Dict[str, Any]:
        """辞書形式で例外情報を返す（API用）"""
        return {
            'error_code': self.error_code,
            'message': self.user_message,
            'technical_message': str(self)
        }


class BusinessLogicError(QuizError):
    """ビジネスロジック例外（400番台のHTTPエラー）"""
    
    def __init__(self, message: str, user_message: str = None, error_code: str = None):
        super().__init__(message, user_message, error_code)
        self.http_status_code = 400


class TechnicalError(QuizError):
    """技術的例外（500番台のHTTPエラー）"""
    
    def __init__(self, message: str, user_message: str = None, error_code: str = None, original_error: Exception = None):
        super().__init__(message, user_message, error_code)
        self.http_status_code = 500
        self.original_error = original_error


# データ関連例外

class DataError(BusinessLogicError):
    """データ関連エラー"""
    
    def __init__(self, message: str, user_message: str = None):
        super().__init__(
            message,
            user_message or "データの処理中にエラーが発生しました",
            "DATA_ERROR"
        )


class QuestionNotFoundError(DataError):
    """問題が見つからない"""
    
    def __init__(self, question_id: int = None):
        if question_id:
            message = f"問題が見つかりません: ID {question_id}"
            user_message = f"問題ID {question_id} が見つかりませんでした"
        else:
            message = "問題が見つかりません"
            user_message = "指定された問題が存在しません"
        
        super().__init__(message, user_message)
        self.error_code = "QUESTION_NOT_FOUND"
        self.http_status_code = 404


class QuestionDataInvalidError(DataError):
    """問題データが無効"""
    
    def __init__(self, field: str = None, value: Any = None):
        if field:
            message = f"問題データが無効です: フィールド '{field}'"
            user_message = f"問題の{field}が正しくありません"
        else:
            message = "問題データが無効です"
            user_message = "問題データの形式が正しくありません"
        
        super().__init__(message, user_message)
        self.error_code = "QUESTION_DATA_INVALID"
        self.field = field
        self.value = value


# セッション関連例外

class SessionError(BusinessLogicError):
    """セッション関連エラー"""
    
    def __init__(self, message: str, user_message: str = None):
        super().__init__(
            message,
            user_message or "クイズセッションでエラーが発生しました",
            "SESSION_ERROR"
        )


class SessionNotFoundError(SessionError):
    """セッションが見つからない"""
    
    def __init__(self, session_id: str = None):
        if session_id:
            message = f"セッションが見つかりません: {session_id}"
            user_message = "指定されたクイズセッションが見つかりません"
        else:
            message = "セッションが見つかりません"
            user_message = "クイズセッションが存在しません"
        
        super().__init__(message, user_message)
        self.error_code = "SESSION_NOT_FOUND"
        self.http_status_code = 404
        self.session_id = session_id


class SessionExpiredError(SessionError):
    """セッションが期限切れ"""
    
    def __init__(self, session_id: str = None):
        message = f"セッションが期限切れです: {session_id}" if session_id else "セッションが期限切れです"
        user_message = "クイズセッションの有効期限が切れています。新しいクイズを開始してください"
        
        super().__init__(message, user_message)
        self.error_code = "SESSION_EXPIRED"
        self.http_status_code = 410
        self.session_id = session_id


class SessionAlreadyCompletedError(SessionError):
    """セッションが既に完了している"""
    
    def __init__(self, session_id: str = None):
        message = f"セッションは既に完了しています: {session_id}" if session_id else "セッションは既に完了しています"
        user_message = "このクイズは既に完了しています"
        
        super().__init__(message, user_message)
        self.error_code = "SESSION_ALREADY_COMPLETED"
        self.http_status_code = 409
        self.session_id = session_id


# 回答関連例外

class AnswerError(BusinessLogicError):
    """回答関連エラー"""
    
    def __init__(self, message: str, user_message: str = None):
        super().__init__(
            message,
            user_message or "回答の処理中にエラーが発生しました",
            "ANSWER_ERROR"
        )


class InvalidAnswerError(AnswerError):
    """無効な回答"""
    
    def __init__(self, option: int = None):
        if option is not None:
            message = f"無効な選択肢: {option}"
            user_message = f"選択肢 {option + 1} は存在しません。1-4の範囲で選択してください"
        else:
            message = "無効な回答です"
            user_message = "正しい選択肢を選んでください（1-4）"
        
        super().__init__(message, user_message)
        self.error_code = "INVALID_ANSWER"
        self.option = option


class AnswerAlreadySubmittedError(AnswerError):
    """回答が既に送信済み"""
    
    def __init__(self, question_index: int = None):
        if question_index is not None:
            message = f"問題{question_index + 1}は既に回答済みです"
            user_message = f"問題{question_index + 1}には既に回答しています"
        else:
            message = "この問題は既に回答済みです"
            user_message = "既に回答済みの問題です"
        
        super().__init__(message, user_message)
        self.error_code = "ANSWER_ALREADY_SUBMITTED"
        self.http_status_code = 409
        self.question_index = question_index


# CSVインポート関連例外

class CSVImportError(DataError):
    """CSV インポートエラー"""
    
    def __init__(self, message: str, line_number: int = None, filename: str = None):
        if line_number:
            full_message = f"CSV インポートエラー (行 {line_number}): {message}"
            user_message = f"{line_number}行目でエラーが発生しました: {message}"
        else:
            full_message = f"CSV インポートエラー: {message}"
            user_message = f"CSVファイルの読み込みに失敗しました: {message}"
        
        super().__init__(full_message, user_message)
        self.error_code = "CSV_IMPORT_ERROR"
        self.line_number = line_number
        self.filename = filename


class CSVValidationError(CSVImportError):
    """CSV バリデーションエラー"""
    
    def __init__(self, message: str, field: str = None, line_number: int = None):
        super().__init__(message, line_number)
        self.error_code = "CSV_VALIDATION_ERROR"
        self.field = field


class CSVFileNotFoundError(CSVImportError):
    """CSVファイルが見つからない"""
    
    def __init__(self, filepath: str):
        message = f"CSVファイルが見つかりません: {filepath}"
        user_message = f"指定されたCSVファイルが存在しません: {filepath}"
        
        super().__init__(message)
        self.error_code = "CSV_FILE_NOT_FOUND"
        self.http_status_code = 404
        self.filepath = filepath


# データベース関連例外

class DatabaseError(TechnicalError):
    """データベース関連エラー"""
    
    def __init__(self, message: str, original_error: Exception = None):
        user_message = "データベースエラーが発生しました。しばらく時間をおいて再試行してください"
        super().__init__(message, user_message, "DATABASE_ERROR", original_error)


class DatabaseConnectionError(DatabaseError):
    """データベース接続エラー"""
    
    def __init__(self, message: str, original_error: Exception = None):
        user_message = "データベースに接続できません。システム管理者にお問い合わせください"
        super().__init__(message, user_message, original_error)
        self.error_code = "DATABASE_CONNECTION_ERROR"


class DatabaseIntegrityError(DatabaseError):
    """データベース整合性エラー"""
    
    def __init__(self, message: str, original_error: Exception = None):
        user_message = "データの整合性エラーが発生しました"
        super().__init__(message, user_message, original_error)
        self.error_code = "DATABASE_INTEGRITY_ERROR"
        self.http_status_code = 409


# 設定・システム関連例外

class ConfigurationError(TechnicalError):
    """設定エラー"""
    
    def __init__(self, message: str, config_key: str = None):
        user_message = "システム設定にエラーがあります。管理者にお問い合わせください"
        super().__init__(message, user_message, "CONFIGURATION_ERROR")
        self.config_key = config_key


class ServiceUnavailableError(TechnicalError):
    """サービス利用不可"""
    
    def __init__(self, service_name: str = None):
        if service_name:
            message = f"サービスが利用できません: {service_name}"
            user_message = f"{service_name}サービスが一時的に利用できません"
        else:
            message = "サービスが利用できません"
            user_message = "サービスが一時的に利用できません。しばらく時間をおいて再試行してください"
        
        super().__init__(message, user_message, "SERVICE_UNAVAILABLE")
        self.http_status_code = 503
        self.service_name = service_name


# バリデーション関連例外

class ValidationError(BusinessLogicError):
    """バリデーションエラー"""
    
    def __init__(self, message: str, field: str = None, value: Any = None):
        user_message = f"入力値が正しくありません: {message}"
        super().__init__(message, user_message, "VALIDATION_ERROR")
        self.field = field
        self.value = value


class RequiredFieldError(ValidationError):
    """必須フィールドエラー"""
    
    def __init__(self, field: str):
        message = f"必須フィールドが設定されていません: {field}"
        user_message = f"{field}は必須項目です"
        super().__init__(message, field)
        self.error_code = "REQUIRED_FIELD_ERROR"


class InvalidFieldValueError(ValidationError):
    """無効なフィールド値エラー"""
    
    def __init__(self, field: str, value: Any, expected: str = None):
        if expected:
            message = f"フィールド '{field}' の値が無効です: {value} (期待値: {expected})"
            user_message = f"{field}の値が正しくありません。{expected}を入力してください"
        else:
            message = f"フィールド '{field}' の値が無効です: {value}"
            user_message = f"{field}の値が正しくありません"
        
        super().__init__(message, field, value)
        self.error_code = "INVALID_FIELD_VALUE"
        self.expected = expected


# Web API用のヘルパー関数

def get_http_status_code(error: Exception) -> int:
    """例外からHTTPステータスコードを取得"""
    if hasattr(error, 'http_status_code'):
        return error.http_status_code
    elif isinstance(error, BusinessLogicError):
        return 400
    elif isinstance(error, TechnicalError):
        return 500
    else:
        return 500


def exception_to_api_response(error: Exception) -> Dict[str, Any]:
    """例外をAPI レスポンス形式に変換"""
    if isinstance(error, QuizError):
        return {
            'success': False,
            'error': error.to_dict(),
            'status_code': get_http_status_code(error)
        }
    else:
        return {
            'success': False,
            'error': {
                'error_code': 'UNKNOWN_ERROR',
                'message': '予期しないエラーが発生しました',
                'technical_message': str(error)
            },
            'status_code': 500
        }