"""
クイズ実行ウィンドウUI
問題表示と回答処理
"""

import tkinter as tk
from typing import Dict, Any, Callable
from .base import BaseWindow, QuestionWidget, ProgressWidget


class QuizWindow(BaseWindow):
    """クイズ実行ウィンドウクラス"""
    
    def __init__(self, parent: tk.Widget, controller):
        """初期化"""
        super().__init__(parent)
        self.controller = controller
        self.current_question_widget = None
        self.current_progress_widget = None
        self.answer_result_frame = None
        
        self.setup_ui(parent)
    
    def setup_ui(self, parent: tk.Widget) -> None:
        """UIセットアップ"""
        self.main_frame = self.create_frame(parent)
        
        # タイトル
        self.title_label = self.create_title_label(self.main_frame, "クイズ実行中")
        self.title_label.pack(pady=(0, 10))
        
        # 進行状況エリア
        self.progress_frame = tk.Frame(self.main_frame, bg=self.colors['bg'])
        self.progress_frame.pack(fill=tk.X, pady=(0, 20))
        
        # 問題表示エリア
        self.question_frame = tk.Frame(self.main_frame, bg=self.colors['bg'])
        self.question_frame.pack(fill=tk.BOTH, expand=True)
        
        # アクションボタンエリア
        self.action_frame = tk.Frame(self.main_frame, bg=self.colors['bg'])
        self.action_frame.pack(side=tk.BOTTOM, fill=tk.X, pady=10)
        
        # 初期状態では非表示
        self.main_frame.pack_forget()
    
    def show_question(self, question_data: Dict[str, Any], progress_data: Dict[str, Any]) -> None:
        """問題と進行状況を表示"""
        # フレームを表示
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 進行状況ウィジェットを更新
        self.update_progress(progress_data)
        
        # 既存の問題ウィジェットを削除
        if self.current_question_widget:
            self.current_question_widget.frame.destroy()
        
        # 回答結果フレームを削除
        if self.answer_result_frame:
            self.answer_result_frame.destroy()
            self.answer_result_frame = None
        
        # 新しい問題ウィジェットを作成
        self.current_question_widget = QuestionWidget(
            self.question_frame,
            question_data,
            self.on_answer_selected
        )
        
        # アクションボタンを非表示
        self.hide_action_buttons()
    
    def update_progress(self, progress_data: Dict[str, Any]) -> None:
        """進行状況を更新"""
        # 既存の進行状況ウィジェットを削除
        if self.current_progress_widget:
            for widget in self.progress_frame.winfo_children():
                widget.destroy()
        
        # 新しい進行状況ウィジェットを作成
        self.current_progress_widget = ProgressWidget(self.progress_frame, progress_data)
    
    def on_answer_selected(self, option_index: int) -> None:
        """選択肢が選択された時の処理"""
        # コントローラーに回答を送信
        self.controller.answer_question(option_index)
    
    def show_answer_result(self, result_data: Dict[str, Any]) -> None:
        """回答結果を表示"""
        # 既存の回答結果フレームを削除
        if self.answer_result_frame:
            self.answer_result_frame.destroy()
        
        # 回答結果フレームを作成
        self.answer_result_frame = tk.Frame(self.question_frame, bg=self.colors['bg'])
        self.answer_result_frame.pack(fill=tk.X, pady=20)
        
        # 選択肢ボタンを結果に応じて更新
        self.update_option_buttons_with_result(result_data)
        
        # 結果メッセージ
        result_text = "🎉 正解！" if result_data['is_correct'] else "❌ 不正解"
        result_color = '#4CAF50' if result_data['is_correct'] else '#f44336'
        
        result_label = tk.Label(
            self.answer_result_frame,
            text=result_text,
            font=('Arial', 16, 'bold'),
            fg=result_color,
            bg=self.colors['bg']
        )
        result_label.pack(pady=10)
        
        # 現在のスコア表示
        score_text = f"現在のスコア: {result_data['current_score']}/{result_data['total_questions']}"
        if result_data.get('accuracy') is not None:
            score_text += f" ({result_data['accuracy']:.1f}%)"
        
        score_label = tk.Label(
            self.answer_result_frame,
            text=score_text,
            font=self.fonts['subtitle'],
            bg=self.colors['bg'],
            fg=self.colors['fg']
        )
        score_label.pack(pady=5)
        
        # 解説表示
        if result_data.get('explanation'):
            self.show_explanation(result_data['explanation'])
        
        # 次へボタンまたは結果表示ボタン
        if result_data['is_session_completed']:
            self.show_completion_button()
        else:
            self.show_next_button()
    
    def update_option_buttons_with_result(self, result_data: Dict[str, Any]) -> None:
        """選択肢ボタンを結果に応じて更新"""
        if not self.current_question_widget:
            return
        
        buttons = self.current_question_widget.option_buttons
        selected_option = result_data['selected_option']
        correct_answer = result_data['correct_answer']
        
        for i, button in enumerate(buttons):
            if i == correct_answer:
                # 正解の選択肢
                button.configure(
                    bg=self.colors['correct'],
                    fg='white',
                    relief=tk.RAISED,
                    bd=3
                )
            elif i == selected_option and not result_data['is_correct']:
                # 間違って選択した選択肢
                button