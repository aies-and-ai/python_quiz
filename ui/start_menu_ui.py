"""
スタートメニュー画面のUIクラス
"""

import tkinter as tk
import os
from typing import Callable, Optional
from ui.base_ui import BaseUI
import config


class StartMenuUI(BaseUI):
    """スタートメニュー画面を管理するクラス"""
    
    def __init__(self, root: tk.Tk):
        """初期化"""
        super().__init__(root)
        
        # コールバック関数
        self.on_start_quiz: Optional[Callable] = None
        self.on_show_history: Optional[Callable] = None
        self.on_show_statistics: Optional[Callable] = None
        self.on_show_settings: Optional[Callable] = None
        self.on_quit: Optional[Callable] = None
    
    def show_menu(self, csv_file: str, data_manager=None) -> None:
        """
        スタートメニューを表示
        
        Args:
            csv_file (str): 使用するCSVファイル名
            data_manager: データマネージャー（統計表示用）
        """
        frame = self.create_frame()
        
        # タイトル
        title = self.create_title(frame, "4択クイズアプリ", 24)
        title.configure(fg="#2C3E50")
        title.pack(pady=(40, 20))
        
        # CSVファイル名とスキーマ情報表示
        self._show_file_info(frame, csv_file, data_manager)
        
        # 統計情報があれば簡易表示
        if data_manager:
            self._show_stats_summary(frame, csv_file, data_manager)
        
        # メニューボタンフレーム
        menu_frame = tk.Frame(frame, bg=config.BG_COLOR)
        menu_frame.pack(expand=True)
        
        # メニューボタンを作成
        self._create_menu_buttons(menu_frame)
    
    def _show_file_info(self, frame: tk.Frame, csv_file: str, data_manager) -> None:
        """CSVファイル情報とスキーマ情報を表示"""
        file_info = tk.Label(
            frame,
            text=f"問題ファイル: {os.path.basename(csv_file)}",
            font=config.OPTION_FONT,
            bg=config.BG_COLOR,
            fg="#34495E"
        )
        file_info.pack(pady=(0, 10))
        
        # スキーマ情報も表示（可能な場合）
        try:
            from csv_reader import QuizCSVReader
            reader = QuizCSVReader(csv_file)
            schema_info = reader.get_schema_info()
            
            if schema_info and schema_info.get('schema_info'):
                schema_name = schema_info['schema_info']['name']
                schema_label = tk.Label(
                    frame,
                    text=f"形式: {schema_name}",
                    font=("Arial", 10),
                    bg=config.BG_COLOR,
                    fg="#7F8C8D"
                )
                schema_label.pack(pady=(0, 20))
        except Exception:
            # スキーマ情報取得に失敗してもメニューは表示
            frame_spacer = tk.Label(frame, text="", bg=config.BG_COLOR)
            frame_spacer.pack(pady=(0, 20))
    
    def _show_stats_summary(self, frame: tk.Frame, csv_file: str, data_manager) -> None:
        """統計サマリーを表示"""
        try:
            stats = data_manager.get_statistics()
            best_scores = data_manager.get_best_scores()
            csv_key = os.path.basename(csv_file)
            
            stats_text = f"総プレイ回数: {stats['total_quizzes']}回"
            if csv_key in best_scores:
                best = best_scores[csv_key]
                stats_text += f" | このファイルのベスト: {best['best_score']}問正解 ({best['best_accuracy']:.1f}%)"
            
            stats_label = tk.Label(
                frame,
                text=stats_text,
                font=("Arial", 11),
                bg=config.BG_COLOR,
                fg="#7F8C8D"
            )
            stats_label.pack(pady=(0, 30))
        except Exception:
            pass  # 統計表示でエラーがあってもメニューは表示
    
    def _create_menu_buttons(self, menu_frame: tk.Frame) -> None:
        """メニューボタンを作成"""
        # クイズ開始ボタン
        start_btn = tk.Button(
            menu_frame,
            text="🎯 クイズを開始",
            font=("Arial", 16, "bold"),
            command=self._on_start_quiz_clicked,
            bg="#27AE60",
            fg="white",
            width=20,
            height=3,
            relief=tk.RAISED,
            bd=3
        )
        start_btn.pack(pady=15)
        
        # 履歴表示ボタン
        history_btn = self.create_button(
            menu_frame,
            "📊 履歴を見る",
            self._on_history_clicked,
            "#3498DB"
        )
        history_btn.pack(pady=10)
        
        # 統計情報ボタン
        stats_btn = self.create_button(
            menu_frame,
            "📈 統計情報",
            self._on_statistics_clicked,
            "#9B59B6"
        )
        stats_btn.pack(pady=10)
        
        # 設定ボタン
        settings_btn = self.create_button(
            menu_frame,
            "⚙️ 設定",
            self._on_settings_clicked,
            "#95A5A6"
        )
        settings_btn.pack(pady=10)
        
        # 終了ボタン
        quit_btn = self.create_button(
            menu_frame,
            "❌ 終了",
            self._on_quit_clicked,
            "#E74C3C"
        )
        quit_btn.pack(pady=15)
    
    def _on_start_quiz_clicked(self) -> None:
        """クイズ開始ボタンがクリックされた時の処理"""
        if self.on_start_quiz:
            self.on_start_quiz()
    
    def _on_history_clicked(self) -> None:
        """履歴ボタンがクリックされた時の処理"""
        if self.on_show_history:
            self.on_show_history()
    
    def _on_statistics_clicked(self) -> None:
        """統計ボタンがクリックされた時の処理"""
        if self.on_show_statistics:
            self.on_show_statistics()
    
    def _on_settings_clicked(self) -> None:
        """設定ボタンがクリックされた時の処理"""
        if self.on_show_settings:
            self.on_show_settings()
    
    def _on_quit_clicked(self) -> None:
        """終了ボタンがクリックされた時の処理"""
        if self.on_quit:
            self.on_quit()
        else:
            self.root.quit()
    
    def set_callbacks(self, 
                     on_start_quiz: Callable = None,
                     on_show_history: Callable = None,
                     on_show_statistics: Callable = None,
                     on_show_settings: Callable = None,
                     on_quit: Callable = None) -> None:
        """コールバック関数を設定"""
        self.on_start_quiz = on_start_quiz
        self.on_show_history = on_show_history
        self.on_show_statistics = on_show_statistics
        self.on_show_settings = on_show_settings
        self.on_quit = on_quit