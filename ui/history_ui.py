"""
履歴・統計表示画面のUIクラス
"""

import tkinter as tk
from tkinter import scrolledtext
from typing import Callable, Optional, Dict, List
from ui.base_ui import BaseUI
import config


class HistoryUI(BaseUI):
    """履歴・統計表示画面を管理するクラス"""
    
    def __init__(self, root: tk.Tk):
        """初期化"""
        super().__init__(root)
        
        # コールバック関数
        self.on_back_to_menu: Optional[Callable] = None
    
    def show_history(self, history: List[Dict], best_scores: Dict, statistics: Dict) -> None:
        """
        履歴を表示
        
        Args:
            history (List[Dict]): クイズ履歴
            best_scores (Dict): ベストスコア
            statistics (Dict): 統計情報
        """
        frame = self.create_frame()
        
        # タイトル
        title = self.create_title(frame, "クイズ履歴")
        title.pack(pady=(0, 20))
        
        # 統計サマリー
        stats_text = f"総プレイ回数: {statistics['total_quizzes']}回 | 全体正答率: {statistics.get('overall_accuracy', 0):.1f}%"
        stats_label = tk.Label(
            frame,
            text=stats_text,
            font=config.SCORE_FONT,
            bg=config.BG_COLOR
        )
        stats_label.pack(pady=(0, 15))
        
        # 履歴表示用スクロールエリア
        self._show_history_list(frame, history)
        
        # 戻るボタン
        self._create_back_button(frame)
    
    def _show_history_list(self, frame: tk.Frame, history: List[Dict]) -> None:
        """履歴リストを表示"""
        history_frame = tk.LabelFrame(
            frame,
            text="最近の履歴（最新10件）",
            font=config.OPTION_FONT,
            bg=config.BG_COLOR
        )
        history_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        text_area = scrolledtext.ScrolledText(
            history_frame,
            height=15,
            font=("Arial", 10),
            wrap=tk.WORD
        )
        text_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 履歴データを表示
        if history:
            for i, record in enumerate(history, 1):
                timestamp = record['timestamp'][:19].replace('T', ' ')
                text_area.insert(tk.END, f"{i}. {timestamp} - {record['csv_file']}\n")
                text_area.insert(tk.END, f"   スコア: {record['score']}/{record['total_questions']} ({record['accuracy']:.1f}%)\n")
                if record['wrong_count'] > 0:
                    text_area.insert(tk.END, f"   間違い: {record['wrong_count']}問\n")
                text_area.insert(tk.END, "\n")
        else:
            text_area.insert(tk.END, "履歴がありません")
        
        text_area.configure(state=tk.DISABLED)
    
    def show_statistics(self, statistics: Dict, wrong_summary: Dict, recent_performance: List[Dict]) -> None:
        """
        統計情報を表示
        
        Args:
            statistics (Dict): 統計情報
            wrong_summary (Dict): 間違いサマリー
            recent_performance (List[Dict]): 最近のパフォーマンス
        """
        frame = self.create_frame()
        
        # タイトル
        title = self.create_title(frame, "統計情報")
        title.pack(pady=(0, 20))
        
        # 統計情報表示
        self._show_statistics_summary(frame, statistics)
        
        # よく間違える問題
        if wrong_summary:
            self._show_wrong_questions_summary(frame, wrong_summary)
        
        # 戻るボタン
        self._create_back_button(frame)
    
    def _show_statistics_summary(self, frame: tk.Frame, statistics: Dict) -> None:
        """統計サマリーを表示"""
        stats_text = f"""総プレイ回数: {statistics['total_quizzes']}回
総問題数: {statistics['total_questions']}問
総正解数: {statistics['total_correct']}問
全体正答率: {statistics.get('overall_accuracy', 0):.1f}%"""
        
        stats_label = tk.Label(
            frame,
            text=stats_text,
            font=config.OPTION_FONT,
            bg=config.BG_COLOR,
            justify=tk.LEFT
        )
        stats_label.pack(pady=(0, 20))
    
    def _show_wrong_questions_summary(self, frame: tk.Frame, wrong_summary: Dict) -> None:
        """よく間違える問題のサマリーを表示"""
        wrong_frame = tk.LabelFrame(
            frame,
            text="よく間違える問題（上位5問）",
            font=config.OPTION_FONT,
            bg=config.BG_COLOR
        )
        wrong_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        wrong_text = scrolledtext.ScrolledText(
            wrong_frame,
            height=8,
            font=("Arial", 9),
            wrap=tk.WORD
        )
        wrong_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        for i, (question, data) in enumerate(list(wrong_summary.items())[:5], 1):
            wrong_text.insert(tk.END, f"{i}. 間違い回数: {data['count']}回\n")
            wrong_text.insert(tk.END, f"   問題: {question}\n")
            wrong_text.insert(tk.END, f"   正解: {data['correct_answer']}\n\n")
        
        wrong_text.configure(state=tk.DISABLED)
    
    def _create_back_button(self, frame: tk.Frame) -> None:
        """戻るボタンを作成"""
        back_btn = self.create_button(
            frame,
            "🔙 メニューに戻る",
            self._on_back_clicked,
            "#4CAF50"
        )
        back_btn.pack(pady=10)
    
    def _on_back_clicked(self) -> None:
        """戻るボタンがクリックされた時の処理"""
        if self.on_back_to_menu:
            self.on_back_to_menu()
    
    def set_callbacks(self, on_back_to_menu: Callable = None) -> None:
        """コールバック関数を設定"""
        self.on_back_to_menu = on_back_to_menu