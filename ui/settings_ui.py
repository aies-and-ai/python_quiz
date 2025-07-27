"""
設定画面のUIクラス
"""

import tkinter as tk
from typing import Callable, Optional, Dict
from ui.base_ui import BaseUI
import config


class SettingsUI(BaseUI):
    """設定画面を管理するクラス"""
    
    def __init__(self, root: tk.Tk):
        """初期化"""
        super().__init__(root)
        
        # コールバック関数
        self.on_save_settings: Optional[Callable] = None
        self.on_back_to_menu: Optional[Callable] = None
        
        # 設定変数
        self.shuffle_questions_var: Optional[tk.BooleanVar] = None
        self.shuffle_options_var: Optional[tk.BooleanVar] = None
        self.auto_save_var: Optional[tk.BooleanVar] = None
    
    def show_settings(self, current_settings: Dict) -> None:
        """
        設定画面を表示
        
        Args:
            current_settings (Dict): 現在の設定値
        """
        frame = self.create_frame()
        
        # タイトル
        title = self.create_title(frame, "⚙️ 設定")
        title.pack(pady=(20, 30))
        
        # 設定項目フレーム
        settings_frame = tk.Frame(frame, bg=config.BG_COLOR)
        settings_frame.pack(expand=True)
        
        # 設定項目を作成
        self._create_setting_items(settings_frame, current_settings)
        
        # ボタンフレーム
        self._create_settings_buttons(frame)
    
    def _create_setting_items(self, settings_frame: tk.Frame, current_settings: Dict) -> None:
        """設定項目を作成"""
        # 問題シャッフル設定
        self._create_shuffle_questions_setting(settings_frame, current_settings)
        
        # 選択肢シャッフル設定
        self._create_shuffle_options_setting(settings_frame, current_settings)
        
        # 自動保存設定
        self._create_auto_save_setting(settings_frame, current_settings)
    
    def _create_shuffle_questions_setting(self, frame: tk.Frame, settings: Dict) -> None:
        """問題シャッフル設定を作成"""
        shuffle_frame = tk.Frame(frame, bg=config.BG_COLOR)
        shuffle_frame.pack(pady=15, fill=tk.X)
        
        tk.Label(
            shuffle_frame,
            text="問題の順序をシャッフル:",
            font=config.OPTION_FONT,
            bg=config.BG_COLOR
        ).pack(side=tk.LEFT)
        
        self.shuffle_questions_var = tk.BooleanVar(value=settings.get('shuffle_questions', True))
        shuffle_check = tk.Checkbutton(
            shuffle_frame,
            variable=self.shuffle_questions_var,
            bg=config.BG_COLOR,
            font=config.OPTION_FONT
        )
        shuffle_check.pack(side=tk.RIGHT)
    
    def _create_shuffle_options_setting(self, frame: tk.Frame, settings: Dict) -> None:
        """選択肢シャッフル設定を作成"""
        options_frame = tk.Frame(frame, bg=config.BG_COLOR)
        options_frame.pack(pady=15, fill=tk.X)
        
        tk.Label(
            options_frame,
            text="選択肢の順序をシャッフル:",
            font=config.OPTION_FONT,
            bg=config.BG_COLOR
        ).pack(side=tk.LEFT)
        
        self.shuffle_options_var = tk.BooleanVar(value=settings.get('shuffle_options', True))
        options_check = tk.Checkbutton(
            options_frame,
            variable=self.shuffle_options_var,
            bg=config.BG_COLOR,
            font=config.OPTION_FONT
        )
        options_check.pack(side=tk.RIGHT)
    
    def _create_auto_save_setting(self, frame: tk.Frame, settings: Dict) -> None:
        """自動保存設定を作成"""
        save_frame = tk.Frame(frame, bg=config.BG_COLOR)
        save_frame.pack(pady=15, fill=tk.X)
        
        tk.Label(
            save_frame,
            text="結果を自動保存:",
            font=config.OPTION_FONT,
            bg=config.BG_COLOR
        ).pack(side=tk.LEFT)
        
        self.auto_save_var = tk.BooleanVar(value=settings.get('auto_save', True))
        save_check = tk.Checkbutton(
            save_frame,
            variable=self.auto_save_var,
            bg=config.BG_COLOR,
            font=config.OPTION_FONT
        )
        save_check.pack(side=tk.RIGHT)
    
    def _create_settings_buttons(self, frame: tk.Frame) -> None:
        """設定画面のボタンを作成"""
        button_frame = tk.Frame(frame, bg=config.BG_COLOR)
        button_frame.pack(pady=30)
        
        # 設定保存ボタン
        save_btn = self.create_button(
            button_frame,
            "💾 設定を保存",
            self._on_save_clicked,
            "#27AE60",
            15
        )
        save_btn.pack(side=tk.LEFT, padx=10)
        
        # メニューに戻るボタン
        back_btn = self.create_button(
            button_frame,
            "🔙 メニューに戻る",
            self._on_back_clicked,
            "#95A5A6",
            15
        )
        back_btn.pack(side=tk.LEFT, padx=10)
    
    def _on_save_clicked(self) -> None:
        """設定保存ボタンがクリックされた時の処理"""
        settings = {
            'shuffle_questions': self.shuffle_questions_var.get(),
            'shuffle_options': self.shuffle_options_var.get(),
            'auto_save': self.auto_save_var.get()
        }
        
        if self.on_save_settings:
            self.on_save_settings(settings)
        
        self.show_info("設定を保存しました")
        self._on_back_clicked()
    
    def _on_back_clicked(self) -> None:
        """戻るボタンがクリックされた時の処理"""
        if self.on_back_to_menu:
            self.on_back_to_menu()
    
    def set_callbacks(self, 
                     on_save_settings: Callable = None,
                     on_back_to_menu: Callable = None) -> None:
        """コールバック関数を設定"""
        self.on_save_settings = on_save_settings
        self.on_back_to_menu = on_back_to_menu