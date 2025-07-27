# enhanced_exceptions.py
"""
強化されたエラーハンドリングシステム
ユーザーフレンドリーなメッセージ + 詳細な技術情報
"""

import traceback
from typing import Optional, Dict, Any
from logger import log_error


class EnhancedQuizAppError(Exception):
    """
    強化されたクイズアプリエラー基底クラス
    ユーザー向けメッセージと技術的詳細を分離
    """
    
    def __init__(
        self, 
        message: str,
        user_message: Optional[str] = None,
        error_code: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
        original_error: Optional[Exception] = None
    ):
        """
        初期化
        
        Args:
            message (str): 技術的なエラーメッセージ
            user_message (str): ユーザー向けの分かりやすいメッセージ
            error_code (str): エラー識別コード
            details (Dict): 追加の詳細情報
            original_error (Exception): 元の例外（ある場合）
        """
        super().__init__(message)
        
        self.technical_message = message
        self.user_message = user_message or self._generate_user_message()
        self.error_code = error_code or self._generate_error_code()
        self.details = details or {}
        self.original_error = original_error
        
        # 自動ログ記録
        self._log_error()
    
    def _generate_user_message(self) -> str:
        """ユーザー向けメッセージを生成（サブクラスでオーバーライド）"""
        return "申し訳ございません。予期しないエラーが発生しました。"
    
    def _generate_error_code(self) -> str:
        """エラーコードを生成"""
        return f"{self.__class__.__name__}_{hash(self.technical_message) % 10000:04d}"
    
    def _log_error(self) -> None:
        """エラーを自動ログ記録"""
        context = f"{self.__class__.__name__}({self.error_code})"
        log_error(self, context)
    
    def get_user_message(self) -> str:
        """ユーザー向けメッセージを取得"""
        return self.user_message
    
    def get_technical_info(self) -> Dict[str, Any]:
        """技術的情報を取得"""
        return {
            "error_code": self.error_code,
            "technical_message": self.technical_message,
            "details": self.details,
            "original_error": str(self.original_error) if self.original_error else None,
            "traceback": traceback.format_exc()
        }
    
    def add_detail(self, key: str, value: Any) -> None:
        """詳細情報を追加"""
        self.details[key] = value


class CSVFormatError(EnhancedQuizAppError):
    """CSV形式に関するエラー"""
    
    def __init__(
        self, 
        message: str, 
        file_path: Optional[str] = None,
        line_number: Optional[int] = None,
        **kwargs
    ):
        # 詳細情報を追加
        details = kwargs.get('details', {})
        if file_path:
            details['file_path'] = file_path
        if line_number:
            details['line_number'] = line_number
        
        kwargs['details'] = details
        super().__init__(message, **kwargs)
    
    def _generate_user_message(self) -> str:
        """CSVエラー向けのユーザーメッセージ"""
        if 'line_number' in self.details:
            return f"CSVファイルの{self.details['line_number']}行目に問題があります。ファイルの内容をご確認ください。"
        elif 'file_path' in self.details:
            return f"CSVファイル「{self.details['file_path']}」の形式に問題があります。"
        else:
            return "CSVファイルの形式に問題があります。ファイルの内容をご確認ください。"
    
    def _generate_error_code(self) -> str:
        return f"CSV_{hash(self.technical_message) % 10000:04d}"


class FileNotFoundError(EnhancedQuizAppError):
    """ファイルが見つからない場合のエラー"""
    
    def __init__(self, message: str, file_path: Optional[str] = None, **kwargs):
        details = kwargs.get('details', {})
        if file_path:
            details['file_path'] = file_path
        kwargs['details'] = details
        super().__init__(message, **kwargs)
    
    def _generate_user_message(self) -> str:
        if 'file_path' in self.details:
            return f"ファイル「{self.details['file_path']}」が見つかりません。ファイルが存在するかご確認ください。"
        else:
            return "指定されたファイルが見つかりません。ファイルパスをご確認ください。"
    
    def _generate_error_code(self) -> str:
        return f"FILE_{hash(self.technical_message) % 10000:04d}"


class QuizDataError(EnhancedQuizAppError):
    """クイズデータに関するエラー"""
    
    def __init__(
        self, 
        message: str,
        question_number: Optional[int] = None,
        operation: Optional[str] = None,
        **kwargs
    ):
        details = kwargs.get('details', {})
        if question_number:
            details['question_number'] = question_number
        if operation:
            details['operation'] = operation
        kwargs['details'] = details
        super().__init__(message, **kwargs)
    
    def _generate_user_message(self) -> str:
        if 'question_number' in self.details:
            return f"問題{self.details['question_number']}の処理中にエラーが発生しました。"
        elif 'operation' in self.details:
            return f"クイズデータの{self.details['operation']}中にエラーが発生しました。"
        else:
            return "クイズデータの処理中にエラーが発生しました。"
    
    def _generate_error_code(self) -> str:
        return f"DATA_{hash(self.technical_message) % 10000:04d}"


class UIError(EnhancedQuizAppError):
    """UI関連のエラー"""
    
    def __init__(
        self, 
        message: str,
        ui_component: Optional[str] = None,
        **kwargs
    ):
        details = kwargs.get('details', {})
        if ui_component:
            details['ui_component'] = ui_component
        kwargs['details'] = details
        super().__init__(message, **kwargs)
    
    def _generate_user_message(self) -> str:
        if 'ui_component' in self.details:
            return f"画面表示の処理中にエラーが発生しました。アプリを再起動してお試しください。"
        else:
            return "画面の表示に問題が発生しました。アプリを再起動してお試しください。"
    
    def _generate_error_code(self) -> str:
        return f"UI_{hash(self.technical_message) % 10000:04d}"


class ConfigurationError(EnhancedQuizAppError):
    """設定関連のエラー"""
    
    def __init__(
        self, 
        message: str,
        config_key: Optional[str] = None,
        **kwargs
    ):
        details = kwargs.get('details', {})
        if config_key:
            details['config_key'] = config_key
        kwargs['details'] = details
        super().__init__(message, **kwargs)
    
    def _generate_user_message(self) -> str:
        return "設定に問題があります。設定を確認するか、アプリを再インストールしてください。"
    
    def _generate_error_code(self) -> str:
        return f"CONFIG_{hash(self.technical_message) % 10000:04d}"


# エラーハンドリング支援関数
def handle_error_safely(func, *args, **kwargs):
    """
    関数を安全に実行し、エラーを適切にハンドリング
    
    Args:
        func: 実行する関数
        *args: 関数の引数
        **kwargs: 関数のキーワード引数
    
    Returns:
        tuple: (success: bool, result: Any, error: Exception)
    """
    try:
        result = func(*args, **kwargs)
        return True, result, None
    except EnhancedQuizAppError as e:
        # 既に強化されたエラーはそのまま
        return False, None, e
    except Exception as e:
        # 予期しないエラーは強化エラーでラップ
        enhanced_error = EnhancedQuizAppError(
            message=f"Unexpected error in {func.__name__}: {str(e)}",
            user_message="予期しないエラーが発生しました。アプリを再起動してお試しください。",
            original_error=e,
            details={'function_name': func.__name__}
        )
        return False, None, enhanced_error


def wrap_exception(original_exception: Exception, context: str = None) -> EnhancedQuizAppError:
    """
    既存の例外を強化エラーでラップ
    
    Args:
        original_exception: 元の例外
        context: エラーが発生したコンテキスト
    
    Returns:
        EnhancedQuizAppError: ラップされた強化エラー
    """
    # 既に強化エラーの場合はそのまま返す
    if isinstance(original_exception, EnhancedQuizAppError):
        return original_exception
    
    # 型に応じて適切な強化エラーを選択
    if isinstance(original_exception, FileNotFoundError):
        return FileNotFoundError(
            message=str(original_exception),
            original_error=original_exception
        )
    elif "csv" in str(original_exception).lower() or "format" in str(original_exception).lower():
        return CSVFormatError(
            message=str(original_exception),
            original_error=original_exception
        )
    else:
        return EnhancedQuizAppError(
            message=str(original_exception),
            user_message="予期しないエラーが発生しました。",
            original_error=original_exception,
            details={'context': context} if context else {}
        )


# デバッグ用エラー情報表示
def print_error_details(error: EnhancedQuizAppError) -> None:
    """デバッグ用：エラー詳細を整形して表示"""
    print("=" * 50)
    print(f"ERROR CODE: {error.error_code}")
    print(f"USER MESSAGE: {error.user_message}")
    print(f"TECHNICAL: {error.technical_message}")
    if error.details:
        print("DETAILS:")
        for key, value in error.details.items():
            print(f"  {key}: {value}")
    print("=" * 50)