"""
問題表示・回答画面のUIクラス
"""

import tkinter as tk
from tkinter import ttk
from typing import Callable, Optional, Dict, List
from ui.base_ui import BaseUI
import config


class QuizUI(BaseUI):
    """問題表示・回答画面を管理するクラス"""
    
    def __init__(self, root: tk.Tk):
        """初期化"""
        super().__init__(root)
        
        # コールバック関数
        self.on_answer: Optional[Callable] = None
        self.on_next: Optional[Callable] = None
        
        # UI要素
        self.option_buttons: List[tk.Button] = []
    
    def show_question(self, question_data: Dict, progress: Dict) -> None:
        """
        問題を表示
        
        Args:
            question_data (Dict): 問題データ
            progress (Dict): 進行状況
        """
        frame = self.create_frame()
        
        # 進行状況表示
        self._show_progress(frame, progress)
        
        # 問題の追加情報表示（タイトル、ジャンル、難易度など）
        self._show_question_info(frame, question_data)
        
        # 問題文表示
        self._show_question_text(frame, question_data['question'])
        
        # 選択肢ボタン表示
        self._show_options(frame, question_data['options'])
    
    def _show_progress(self, frame: tk.Frame, progress: Dict) -> None:
        """進行状況を表示"""
        # 進行状況テキスト
        progress_text = f"問題 {progress['current']}/{progress['total']} - スコア: {progress['score']}"
        progress_label = tk.Label(
            frame,
            text=progress_text,
            font=config.SCORE_FONT,
            bg=config.BG_COLOR
        )
        progress_label.pack(pady=(0, 20))
        
        # プログレスバー
        progress_var = tk.DoubleVar(value=progress['percentage'])
        progress_bar = ttk.Progressbar(
            frame,
            variable=progress_var,
            maximum=100,
            length=400
        )
        progress_bar.pack(pady=(0, 20))
    
    def _show_question_info(self, frame: tk.Frame, question_data: Dict) -> None:
        """問題の追加情報を表示（タイトル、ジャンル、難易度など）"""
        extra_data = question_data.get('extra_data', {})
        
        if not extra_data:
            return
        
        info_frame = tk.Frame(frame, bg=config.BG_COLOR)
        info_frame.pack(pady=(0, 15))
        
        # タイトルがあれば大きく表示
        if 'title' in extra_data and extra_data['title']:
            title_label = tk.Label(
                info_frame,
                text=extra_data['title'],
                font=("Arial", 14, "bold"),
                bg=config.BG_COLOR,
                fg="#2C3E50"
            )
            title_label.pack(pady=(0, 5))
        
        # その他の情報を横並びで表示
        info_items = []
        display_order = ['genre', 'category', 'difficulty', 'level', 'source', 'unit', 'chapter']
        
        for field in display_order:
            if field in extra_data and extra_data[field]:
                # フィールド名を日本語化
                field_labels = {
                    'genre': 'ジャンル',
                    'category': 'カテゴリ', 
                    'difficulty': '難易度',
                    'level': 'レベル',
                    'source': '出典',
                    'unit': '単元',
                    'chapter': '章'
                }
                label = field_labels.get(field, field.title())
                info_items.append(f"{label}: {extra_data[field]}")
        
        if info_items:
            info_text = " | ".join(info_items)
            info_label = tk.Label(
                info_frame,
                text=info_text,
                font=("Arial", 10),
                bg=config.BG_COLOR,
                fg="#7F8C8D"
            )
            info_label.pack()
    
    def _show_question_text(self, frame: tk.Frame, question_text: str) -> None:
        """問題文を表示"""
        question_frame = tk.Frame(frame, bg=config.QUESTION_BG, relief=tk.RAISED, bd=2)
        question_frame.pack(fill=tk.X, pady=(0, 30))
        
        question_label = tk.Label(
            question_frame,
            text=question_text,
            font=config.QUESTION_FONT,
            bg=config.QUESTION_BG,
            wraplength=700,
            justify=tk.LEFT
        )
        question_label.pack(padx=20, pady=20)
    
    def _show_options(self, frame: tk.Frame, options: List[str]) -> None:
        """選択肢を表示"""
        self.option_buttons = []
        for i, option in enumerate(options):
            btn = tk.Button(
                frame,
                text=f"{i+1}. {option}",
                font=config.OPTION_FONT,
                bg=config.BUTTON_COLOR,
                width=config.BUTTON_WIDTH,
                height=config.BUTTON_HEIGHT,
                wraplength=600,
                justify=tk.LEFT,
                command=lambda idx=i: self._on_option_selected(idx)
            )
            btn.pack(fill=tk.X, pady=5)
            self.option_buttons.append(btn)
    
    def _on_option_selected(self, option_index: int) -> None:
        """選択肢が選択された時の処理"""
        # ボタンを無効化
        for btn in self.option_buttons:
            btn.configure(state=tk.DISABLED)
        
        if self.on_answer:
            self.on_answer(option_index)
    
    def show_answer_result(self, result: Dict) -> None:
        """
        回答結果を表示（選択肢ごとの解説付き）
        
        Args:
            result (Dict): 回答結果データ
        """
        # 各選択肢ボタンを結果に応じて更新
        self._update_option_buttons_with_explanations(result)
        
        # 結果メッセージ
        result_text = "正解！" if result['is_correct'] else "不正解"
        result_label = tk.Label(
            self.current_frame,
            text=result_text,
            font=config.SCORE_FONT,
            fg="green" if result['is_correct'] else "red",
            bg=config.BG_COLOR
        )
        result_label.pack(pady=10)
        
        # 全体解説表示
        if result['question'].get('explanation'):
            self._show_explanation(result['question']['explanation'])
        
        # 次へボタン
        next_btn = self.create_button(
            self.current_frame,
            "次の問題へ",
            self._on_next_clicked,
            "#4CAF50"
        )
        next_btn.pack(pady=20)
    
    def _show_explanation(self, explanation: str) -> None:
        """解説を表示"""
        explanation_frame = tk.Frame(self.current_frame, bg=config.QUESTION_BG, relief=tk.RAISED, bd=1)
        explanation_frame.pack(fill=tk.X, pady=10)
        
        explanation_label = tk.Label(
            explanation_frame,
            text=f"解説: {explanation}",
            font=config.OPTION_FONT,
            bg=config.QUESTION_BG,
            wraplength=700,
            justify=tk.LEFT
        )
        explanation_label.pack(padx=20, pady=10)
    
    def _update_option_buttons_with_explanations(self, result: Dict) -> None:
        """選択肢ボタンを結果と解説付きで更新"""
        question_data = result['question']
        option_explanations = question_data.get('option_explanations', [''] * 4)
        
        # まず既存のボタンを削除
        for btn in self.option_buttons:
            btn.destroy()
        
        # 新しく結果付きの選択肢を作成
        for i in range(4):
            # アイコンと色の決定
            if i == result['correct_answer']:
                bg_color = config.CORRECT_COLOR
                icon = "✅"
                status = " (正解)"
            elif i == result['selected_option'] and not result['is_correct']:
                bg_color = config.INCORRECT_COLOR  
                icon = "❌"
                status = " (あなたの選択)"
            else:
                bg_color = "#f8f9fa"  # 薄いグレー
                icon = "⚪"
                status = ""
            
            # 選択肢テキストの作成
            option_text = f"{i+1}. {question_data['options'][i]}{status}"
            
            # 選択肢ボタンを作成
            option_btn = tk.Button(
                self.current_frame,
                text=option_text,
                font=config.OPTION_FONT,
                bg=bg_color,
                width=config.BUTTON_WIDTH,
                height=2,
                wraplength=600,
                justify=tk.LEFT,
                state=tk.DISABLED,
                relief=tk.RAISED,
                bd=2
            )
            option_btn.pack(fill=tk.X, pady=2)
            
            # 解説がある場合は解説ラベルを作成
            if option_explanations[i]:
                explanation_text = f"   {icon} {option_explanations[i]}"
                explanation_label = tk.Label(
                    self.current_frame,
                    text=explanation_text,
                    font=("Arial", 10),
                    bg=config.BG_COLOR,
                    fg="#2C3E50",
                    wraplength=650,
                    justify=tk.LEFT,
                    anchor="w"
                )
                explanation_label.pack(fill=tk.X, padx=30, pady=(2, 8))
    
    def _show_hint(self, hint: str) -> None:
        """ヒントを表示（削除予定）"""
        pass  # ヒント機能は削除
    
    def _on_next_clicked(self) -> None:
        """次へボタンがクリックされた時の処理"""
        if self.on_next:
            self.on_next()
    
    def set_callbacks(self, on_answer: Callable = None, on_next: Callable = None) -> None:
        """コールバック関数を設定"""
        self.on_answer = on_answer
        self.on_next = on_next