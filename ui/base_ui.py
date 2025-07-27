"""
共通UI機能を提供する基底クラス
"""

import tkinter as tk
from tkinter import messagebox
from typing import Optional, Callable
import config


class BaseUI:
    """すべてのUI画面クラスの基底クラス"""
    
    def __init__(self, root: tk.Tk):
        """
        初期化
        
        Args:
            root (tk.Tk): メインウィンドウ
        """
        self.root = root
        self.current_frame: Optional[tk.Frame] = None
    
    def create_frame(self) -> tk.Frame:
        """新しいフレームを作成"""
        if self.current_frame:
            self.current_frame.destroy()
        
        self.current_frame = tk.Frame(self.root, bg=config.BG_COLOR)
        self.current_frame.pack(fill=tk.BOTH, expand=True, padx=config.PADDING, pady=config.PADDING)
        return self.current_frame
    
    def show_error(self, message: str) -> None:
        """エラーメッセージを表示"""
        messagebox.showerror("エラー", message)
    
    def show_info(self, message: str) -> None:
        """情報メッセージを表示"""
        messagebox.showinfo("情報", message)
    
    def create_title(self, frame: tk.Frame, text: str, font_size: int = 18) -> tk.Label:
        """タイトルラベルを作成"""
        return tk.Label(
            frame,
            text=text,
            font=("Arial", font_size, "bold"),
            bg=config.BG_COLOR
        )
    
    def create_button(self, frame: tk.Frame, text: str, command: Callable, 
                     bg_color: str = "#4CAF50", width: int = 20, height: int = 2) -> tk.Button:
        """標準ボタンを作成"""
        return tk.Button(
            frame,
            text=text,
            font=config.BUTTON_FONT,
            command=command,
            bg=bg_color,
            fg="white",
            width=width,
            height=height
        )
    
    def hide(self) -> None:
        """画面を非表示にする"""
        if self.current_frame:
            self.current_frame.pack_forget()
    
    def show(self) -> None:
        """画面を表示する"""
        if self.current_frame:
            self.current_frame.pack(fill=tk.BOTH, expand=True, padx=config.PADDING, pady=config.PADDING)

    def show_error(self, message: str, title: str = "エラー") -> None:
        """エラーメッセージを表示（強化版）"""
        try:
            from enhanced_exceptions import EnhancedQuizAppError
            
            # メッセージが強化エラーからのものかチェック
            messagebox.showerror(title, message)
            
        except Exception as e:
            # エラー表示自体がエラーになった場合の緊急処理
            print(f"CRITICAL: Cannot display error dialog: {e}")
            print(f"Original error message: {message}")
    
    def show_enhanced_error(self, error: 'EnhancedQuizAppError') -> None:
        """強化エラーを適切に表示"""
        # ユーザー向けメッセージを表示
        user_msg = error.get_user_message()
        
        # エラーコードも含める（サポート用）
        full_message = f"{user_msg}\n\nエラーコード: {error.error_code}"
        
        self.show_error(full_message)