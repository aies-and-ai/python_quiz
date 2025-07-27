"""
UI統合管理クラス - 各画面UIを統合管理
"""

import tkinter as tk
from typing import Dict, List, Callable, Optional
from ui.base_ui import BaseUI
from ui.start_menu_ui import StartMenuUI
from ui.quiz_ui import QuizUI
from ui.result_ui import ResultUI
from ui.history_ui import HistoryUI
from ui.settings_ui import SettingsUI
import config


class UIManager:
    """UI全体を管理する統合クラス"""
    
    def __init__(self, root: tk.Tk):
        """
        初期化
        
        Args:
            root (tk.Tk): メインウィンドウ
        """
        self.root = root
        self.setup_window()
        
        # 各UI画面を初期化
        self.start_menu_ui = StartMenuUI(root)
        self.quiz_ui = QuizUI(root)
        self.result_ui = ResultUI(root)
        self.history_ui = HistoryUI(root)
        self.settings_ui = SettingsUI(root)
        
        # 現在表示中の画面
        self.current_ui: Optional[BaseUI] = None
    
    def setup_window(self) -> None:
        """ウィンドウの基本設定"""
        self.root.title(config.WINDOW_TITLE)
        self.root.geometry(f"{config.WINDOW_WIDTH}x{config.WINDOW_HEIGHT}")
        self.root.configure(bg=config.BG_COLOR)
        self.root.resizable(True, True)
        
        # ウィンドウを中央に配置
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (config.WINDOW_WIDTH // 2)
        y = (self.root.winfo_screenheight() // 2) - (config.WINDOW_HEIGHT // 2)
        self.root.geometry(f"{config.WINDOW_WIDTH}x{config.WINDOW_HEIGHT}+{x}+{y}")
    
    def show_start_menu(self, csv_file: str, data_manager=None) -> None:
        """スタートメニューを表示"""
        self._switch_ui(self.start_menu_ui)
        self.start_menu_ui.show_menu(csv_file, data_manager)
    
    def show_question(self, question_data: Dict, progress: Dict) -> None:
        """問題を表示"""
        self._switch_ui(self.quiz_ui)
        self.quiz_ui.show_question(question_data, progress)
    
    def show_answer_result(self, result: Dict) -> None:
        """回答結果を表示"""
        self.quiz_ui.show_answer_result(result)
    
    def show_results(self, results: Dict) -> None:
        """最終結果を表示"""
        self._switch_ui(self.result_ui)
        self.result_ui.show_results(results)
    
    def show_history(self, history: List[Dict], best_scores: Dict, statistics: Dict) -> None:
        """履歴を表示"""
        self._switch_ui(self.history_ui)
        self.history_ui.show_history(history, best_scores, statistics)
    
    def show_statistics(self, statistics: Dict, wrong_summary: Dict, recent_performance: List[Dict]) -> None:
        """統計情報を表示"""
        self._switch_ui(self.history_ui)
        self.history_ui.show_statistics(statistics, wrong_summary, recent_performance)
    
    def show_settings(self, current_settings: Dict) -> None:
        """設定画面を表示"""
        self._switch_ui(self.settings_ui)
        self.settings_ui.show_settings(current_settings)
    
    def _switch_ui(self, new_ui: BaseUI) -> None:
        """UI画面を切り替え"""
        if self.current_ui:
            self.current_ui.hide()
        self.current_ui = new_ui
        new_ui.show()
    
    def set_callbacks(self, 
                     # スタートメニューのコールバック
                     on_start_quiz: Callable = None,
                     on_show_history: Callable = None,
                     on_show_statistics: Callable = None,
                     on_show_settings: Callable = None,
                     on_quit: Callable = None,
                     
                     # クイズのコールバック
                     on_answer: Callable = None,
                     on_next: Callable = None,
                     
                     # 結果のコールバック
                     on_restart: Callable = None,
                     on_retry_wrong: Callable = None,
                     
                     # 設定のコールバック
                     on_save_settings: Callable = None,
                     
                     # 共通のコールバック
                     on_back_to_menu: Callable = None) -> None:
        """全てのコールバック関数を設定"""
        
        # スタートメニューのコールバック設定
        self.start_menu_ui.set_callbacks(
            on_start_quiz=on_start_quiz,
            on_show_history=on_show_history,
            on_show_statistics=on_show_statistics,
            on_show_settings=on_show_settings,
            on_quit=on_quit
        )
        
        # クイズのコールバック設定
        self.quiz_ui.set_callbacks(
            on_answer=on_answer,
            on_next=on_next
        )
        
        # 結果のコールバック設定
        self.result_ui.set_callbacks(
            on_restart=on_restart,
            on_retry_wrong=on_retry_wrong,
            on_show_history=on_show_history,
            on_show_statistics=on_show_statistics,
            on_quit=on_quit
        )
        
        # 履歴・統計のコールバック設定
        self.history_ui.set_callbacks(
            on_back_to_menu=on_back_to_menu
        )
        
        # 設定のコールバック設定
        self.settings_ui.set_callbacks(
            on_save_settings=on_save_settings,
            on_back_to_menu=on_back_to_menu
        )
    
    def show_error(self, message: str) -> None:
        """エラーメッセージを表示"""
        if self.current_ui:
            self.current_ui.show_error(message)
    
    def show_info(self, message: str) -> None:
        """情報メッセージを表示"""
        if self.current_ui:
            self.current_ui.show_info(message)