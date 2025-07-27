"""
結果表示画面のUIクラス
"""

import tkinter as tk
from tkinter import scrolledtext
from typing import Callable, Optional, Dict
from ui.base_ui import BaseUI
import config


class ResultUI(BaseUI):
    """結果表示画面を管理するクラス"""
    
    def __init__(self, root: tk.Tk):
        """初期化"""
        super().__init__(root)
        
        # コールバック関数
        self.on_restart: Optional[Callable] = None
        self.on_retry_wrong: Optional[Callable] = None
        self.on_show_history: Optional[Callable] = None
        self.on_show_statistics: Optional[Callable] = None
        self.on_quit: Optional[Callable] = None
    
    def show_results(self, results: Dict) -> None:
        """
        最終結果を表示
        
        Args:
            results (Dict): 最終結果データ
        """
        frame = self.create_frame()
        
        # タイトル
        title = self.create_title(frame, "クイズ結果", 20)
        title.pack(pady=20)
        
        # スコア表示
        self._show_score(frame, results)
        
        # 間違えた問題の表示
        if results['wrong_questions']:
            self._show_wrong_questions(frame, results['wrong_questions'])
        
        # ボタン群
        self._create_result_buttons(frame, results)
    
    def _show_score(self, frame: tk.Frame, results: Dict) -> None:
        """スコアを表示"""
        score_text = f"スコア: {results['score']}/{results['total_questions']}"
        accuracy_text = f"正答率: {results['accuracy']:.1f}%"
        
        # ベストスコア情報があれば表示
        best_info_text = ""
        if results.get('best_score_info'):
            best = results['best_score_info']
            if results['score'] >= best['best_score']:
                best_info_text = "🎉 新記録達成！"
            else:
                best_info_text = f"ベスト: {best['best_score']}/{results['total_questions']} ({best['best_accuracy']:.1f}%)"
        
        display_text = f"{score_text}\n{accuracy_text}"
        if best_info_text:
            display_text += f"\n{best_info_text}"
        
        score_label = tk.Label(
            frame,
            text=display_text,
            font=config.SCORE_FONT,
            bg=config.BG_COLOR,
            fg="green" if "新記録" in best_info_text else "black"
        )
        score_label.pack(pady=20)
    
    def _show_wrong_questions(self, frame: tk.Frame, wrong_questions: list) -> None:
        """間違えた問題を表示"""
        wrong_frame = tk.LabelFrame(
            frame,
            text="間違えた問題",
            font=config.OPTION_FONT,
            bg=config.BG_COLOR
        )
        wrong_frame.pack(fill=tk.BOTH, expand=True, pady=20)
        
        # スクロール可能なテキストエリア
        text_area = scrolledtext.ScrolledText(
            wrong_frame,
            height=10,
            font=("Arial", 10),
            wrap=tk.WORD
        )
        text_area.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        for i, wrong in enumerate(wrong_questions, 1):
            q = wrong['question']
            selected = q['options'][wrong['selected_option']]
            correct = q['options'][wrong['correct_answer']]
            
            text_area.insert(tk.END, f"{i}. {q['question']}\n")
            text_area.insert(tk.END, f"   あなたの回答: {selected}\n")
            text_area.insert(tk.END, f"   正解: {correct}\n")
            if q.get('explanation'):
                text_area.insert(tk.END, f"   解説: {q['explanation']}\n")
            text_area.insert(tk.END, "\n")
        
        text_area.configure(state=tk.DISABLED)
    
    def _create_result_buttons(self, frame: tk.Frame, results: Dict) -> None:
        """結果画面のボタンを作成"""
        button_frame = tk.Frame(frame, bg=config.BG_COLOR)
        button_frame.pack(pady=20)
        
        # 履歴表示ボタン
        history_btn = self.create_button(
            button_frame,
            "履歴表示",
            self._on_history_clicked,
            "#9C27B0",
            12
        )
        history_btn.pack(side=tk.LEFT, padx=5)
        
        # 統計表示ボタン
        stats_btn = self.create_button(
            button_frame,
            "統計情報",
            self._on_statistics_clicked,
            "#607D8B",
            12
        )
        stats_btn.pack(side=tk.LEFT, padx=5)
        
        # リスタートボタン
        restart_btn = self.create_button(
            button_frame,
            "もう一度",
            self._on_restart_clicked,
            "#2196F3",
            12
        )
        restart_btn.pack(side=tk.LEFT, padx=5)
        
        # 間違えた問題のみボタン
        if results['wrong_questions']:
            retry_btn = self.create_button(
                button_frame,
                "間違えた問題のみ",
                self._on_retry_wrong_clicked,
                "#FF9800",
                15
            )
            retry_btn.pack(side=tk.LEFT, padx=5)
        
        # 終了ボタン
        quit_btn = self.create_button(
            button_frame,
            "終了",
            self._on_quit_clicked,
            "#f44336",
            12
        )
        quit_btn.pack(side=tk.LEFT, padx=5)
    
    def _on_restart_clicked(self) -> None:
        """リスタートボタンがクリックされた時の処理"""
        if self.on_restart:
            self.on_restart()
    
    def _on_retry_wrong_clicked(self) -> None:
        """間違えた問題のみボタンがクリックされた時の処理"""
        if self.on_retry_wrong:
            self.on_retry_wrong()
    
    def _on_history_clicked(self) -> None:
        """履歴表示ボタンがクリックされた時の処理"""
        if self.on_show_history:
            self.on_show_history()
    
    def _on_statistics_clicked(self) -> None:
        """統計情報ボタンがクリックされた時の処理"""
        if self.on_show_statistics:
            self.on_show_statistics()
    
    def _on_quit_clicked(self) -> None:
        """終了ボタンがクリックされた時の処理"""
        if self.on_quit:
            self.on_quit()
        else:
            self.root.quit()
    
    def set_callbacks(self, 
                     on_restart: Callable = None,
                     on_retry_wrong: Callable = None,
                     on_show_history: Callable = None,
                     on_show_statistics: Callable = None,
                     on_quit: Callable = None) -> None:
        """コールバック関数を設定"""
        self.on_restart = on_restart
        self.on_retry_wrong = on_retry_wrong
        self.on_show_history = on_show_history
        self.on_show_statistics = on_show_statistics
        self.on_quit = on_quit