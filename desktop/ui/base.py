"""
基本UIコンポーネント
共通機能とスタイル定義
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Optional, Callable, Dict, Any
from app.config import get_settings


class BaseWindow:
    """基本ウィンドウクラス"""
    
    def __init__(self, parent: Optional[tk.Widget] = None):
        """初期化"""
        self.settings = get_settings()
        self.parent = parent
        self.frame: Optional[tk.Frame] = None
        
        # カラーテーマ
        self.colors = {
            'bg': '#f0f0f0',
            'fg': '#333333',
            'button_bg': '#4CAF50',
            'button_fg': 'white',
            'button_hover': '#45a049',
            'correct': '#4CAF50',
            'incorrect': '#f44336',
            'question_bg': '#ffffff',
            'border': '#cccccc'
        }
        
        # フォント設定
        self.fonts = {
            'title': ('Arial', 18, 'bold'),
            'subtitle': ('Arial', 14, 'bold'),
            'normal': ('Arial', 12),
            'button': ('Arial', 11),
            'question': ('Arial', 13, 'bold'),
            'option': ('Arial', 11)
        }
    
    def create_frame(self, parent: tk.Widget) -> tk.Frame:
        """新しいフレームを作成"""
        if self.frame:
            self.frame.destroy()
        
        self.frame = tk.Frame(parent, bg=self.colors['bg'])
        self.frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        return self.frame
    
    def create_title_label(self, parent: tk.Widget, text: str) -> tk.Label:
        """タイトルラベルを作成"""
        return tk.Label(
            parent,
            text=text,
            font=self.fonts['title'],
            bg=self.colors['bg'],
            fg=self.colors['fg']
        )
    
    def create_button(self, 
                     parent: tk.Widget,
                     text: str,
                     command: Callable,
                     style: str = 'normal',
                     width: int = 20,
                     height: int = 2) -> tk.Button:
        """ボタンを作成"""
        
        button_styles = {
            'normal': {'bg': self.colors['button_bg'], 'fg': self.colors['button_fg']},
            'primary': {'bg': '#2196F3', 'fg': 'white'},
            'success': {'bg': '#4CAF50', 'fg': 'white'},
            'warning': {'bg': '#FF9800', 'fg': 'white'},
            'danger': {'bg': '#f44336', 'fg': 'white'},
            'secondary': {'bg': '#6c757d', 'fg': 'white'}
        }
        
        style_config = button_styles.get(style, button_styles['normal'])
        
        button = tk.Button(
            parent,
            text=text,
            command=command,
            font=self.fonts['button'],
            width=width,
            height=height,
            relief=tk.RAISED,
            bd=2,
            cursor='hand2',
            **style_config
        )
        
        # ホバー効果
        def on_enter(e):
            button.configure(relief=tk.RAISED, bd=3)
        
        def on_leave(e):
            button.configure(relief=tk.RAISED, bd=2)
        
        button.bind("<Enter>", on_enter)
        button.bind("<Leave>", on_leave)
        
        return button
    
    def create_progress_bar(self, parent: tk.Widget, length: int = 400) -> ttk.Progressbar:
        """プログレスバーを作成"""
        return ttk.Progressbar(
            parent,
            length=length,
            mode='determinate'
        )
    
    def create_text_widget(self, 
                          parent: tk.Widget,
                          width: int = 60,
                          height: int = 10,
                          readonly: bool = True) -> tk.Text:
        """テキストウィジェットを作成"""
        text_widget = tk.Text(
            parent,
            width=width,
            height=height,
            font=self.fonts['normal'],
            wrap=tk.WORD,
            bg=self.colors['question_bg'],
            relief=tk.SUNKEN,
            bd=1
        )
        
        if readonly:
            text_widget.configure(state=tk.DISABLED)
        
        return text_widget
    
    def create_info_frame(self, parent: tk.Widget, title: str) -> tuple[tk.LabelFrame, tk.Frame]:
        """情報表示用フレームを作成"""
        label_frame = tk.LabelFrame(
            parent,
            text=title,
            font=self.fonts['subtitle'],
            bg=self.colors['bg'],
            fg=self.colors['fg'],
            relief=tk.GROOVE,
            bd=2
        )
        
        content_frame = tk.Frame(label_frame, bg=self.colors['bg'])
        content_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        return label_frame, content_frame
    
    def show_error(self, message: str, title: str = "エラー") -> None:
        """エラーダイアログを表示"""
        messagebox.showerror(title, message)
    
    def show_info(self, message: str, title: str = "情報") -> None:
        """情報ダイアログを表示"""
        messagebox.showinfo(title, message)
    
    def show_warning(self, message: str, title: str = "警告") -> None:
        """警告ダイアログを表示"""
        messagebox.showwarning(title, message)
    
    def ask_yes_no(self, message: str, title: str = "確認") -> bool:
        """はい/いいえダイアログを表示"""
        return messagebox.askyesno(title, message)
    
    def center_window(self, window: tk.Tk, width: int, height: int) -> None:
        """ウィンドウを画面中央に配置"""
        screen_width = window.winfo_screenwidth()
        screen_height = window.winfo_screenheight()
        
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        
        window.geometry(f"{width}x{height}+{x}+{y}")


class QuestionWidget(BaseWindow):
    """問題表示用ウィジェット"""
    
    def __init__(self, parent: tk.Widget, question_data: Dict[str, Any], on_answer: Callable):
        """初期化"""
        super().__init__()
        self.question_data = question_data
        self.on_answer = on_answer
        self.option_buttons = []
        
        self.create_question_ui(parent)
    
    def create_question_ui(self, parent: tk.Widget) -> None:
        """問題UIを作成"""
        frame = self.create_frame(parent)
        
        # 問題文フレーム
        question_frame = tk.Frame(
            frame,
            bg=self.colors['question_bg'],
            relief=tk.RAISED,
            bd=2
        )
        question_frame.pack(fill=tk.X, pady=(0, 20))
        
        # カテゴリ・難易度表示
        if self.question_data.get('category') or self.question_data.get('difficulty'):
            info_text = []
            if self.question_data.get('category'):
                info_text.append(f"カテゴリ: {self.question_data['category']}")
            if self.question_data.get('difficulty'):
                info_text.append(f"難易度: {self.question_data['difficulty']}")
            
            info_label = tk.Label(
                question_frame,
                text=" | ".join(info_text),
                font=('Arial', 10),
                bg=self.colors['question_bg'],
                fg='#666666'
            )
            info_label.pack(pady=(5, 0))
        
        # 問題文
        question_label = tk.Label(
            question_frame,
            text=self.question_data['text'],
            font=self.fonts['question'],
            bg=self.colors['question_bg'],
            fg=self.colors['fg'],
            wraplength=700,
            justify=tk.LEFT
        )
        question_label.pack(padx=20, pady=15)
        
        # 選択肢ボタン
        self.create_option_buttons(frame)
    
    def create_option_buttons(self, parent: tk.Widget) -> None:
        """選択肢ボタンを作成"""
        for i, option in enumerate(self.question_data['options']):
            btn = tk.Button(
                parent,
                text=f"{i+1}. {option}",
                font=self.fonts['option'],
                bg=self.colors['bg'],
                fg=self.colors['fg'],
                width=80,
                height=2,
                relief=tk.RAISED,
                bd=2,
                wraplength=600,
                justify=tk.LEFT,
                anchor='w',
                cursor='hand2',
                command=lambda idx=i: self.select_option(idx)
            )
            btn.pack(fill=tk.X, pady=3)
            self.option_buttons.append(btn)
    
    def select_option(self, option_index: int) -> None:
        """選択肢を選択"""
        # ボタンを無効化
        for btn in self.option_buttons:
            btn.configure(state=tk.DISABLED)
        
        # 選択されたボタンをハイライト
        selected_btn = self.option_buttons[option_index]
        selected_btn.configure(bg='#e3f2fd', relief=tk.SUNKEN)
        
        # コールバック実行
        self.on_answer(option_index)


class ProgressWidget(BaseWindow):
    """進行状況表示ウィジェット"""
    
    def __init__(self, parent: tk.Widget, progress_data: Dict[str, Any]):
        """初期化"""
        super().__init__()
        self.progress_data = progress_data
        
        self.create_progress_ui(parent)
    
    def create_progress_ui(self, parent: tk.Widget) -> None:
        """進行状況UIを作成"""
        # 進行状況テキスト
        progress_text = f"問題 {self.progress_data['current_index']}/{self.progress_data['total_questions']} - スコア: {self.progress_data['score']}"
        
        if self.progress_data.get('accuracy') is not None:
            progress_text += f" - 正答率: {self.progress_data['accuracy']:.1f}%"
        
        progress_label = tk.Label(
            parent,
            text=progress_text,
            font=self.fonts['subtitle'],
            bg=self.colors['bg'],
            fg=self.colors['fg']
        )
        progress_label.pack(pady=(0, 10))
        
        # プログレスバー
        progress_bar = self.create_progress_bar(parent)
        progress_bar.pack(pady=(0, 20))
        
        # 進行率を設定
        if self.progress_data.get('progress_percentage') is not None:
            progress_bar['value'] = self.progress_data['progress_percentage']


class ResultsWidget(BaseWindow):
    """結果表示ウィジェット"""
    
    def __init__(self, parent: tk.Widget, results_data: Dict[str, Any], callbacks: Dict[str, Callable]):
        """初期化"""
        super().__init__()
        self.results_data = results_data
        self.callbacks = callbacks
        
        self.create_results_ui(parent)
    
    def create_results_ui(self, parent: tk.Widget) -> None:
        """結果UIを作成"""
        frame = self.create_frame(parent)
        
        # タイトル
        title = self.create_title_label(frame, "クイズ結果")
        title.pack(pady=(0, 20))
        
        # スコア表示
        self.create_score_display(frame)
        
        # 統計情報表示
        if self.results_data.get('category_stats') or self.results_data.get('difficulty_stats'):
            self.create_stats_display(frame)
        
        # 間違えた問題表示
        if self.results_data.get('wrong_questions'):
            self.create_wrong_questions_display(frame)
        
        # アクションボタン
        self.create_action_buttons(frame)
    
    def create_score_display(self, parent: tk.Widget) -> None:
        """スコア表示を作成"""
        score_frame = tk.Frame(parent, bg=self.colors['bg'])
        score_frame.pack(pady=(0, 20))
        
        score_text = f"スコア: {self.results_data['score']}/{self.results_data['total_questions']}"
        accuracy_text = f"正答率: {self.results_data['accuracy']:.1f}%"
        
        score_label = tk.Label(
            score_frame,
            text=f"{score_text}\n{accuracy_text}",
            font=self.fonts['title'],
            bg=self.colors['bg'],
            fg=self.colors['fg']
        )
        score_label.pack()
    
    def create_stats_display(self, parent: tk.Widget) -> None:
        """統計情報表示を作成"""
        stats_frame, content_frame = self.create_info_frame(parent, "詳細統計")
        stats_frame.pack(fill=tk.X, pady=(0, 20))
        
        # カテゴリ別統計
        if self.results_data.get('category_stats'):
            self.create_category_stats(content_frame)
        
        # 難易度別統計
        if self.results_data.get('difficulty_stats'):
            self.create_difficulty_stats(content_frame)
    
    def create_category_stats(self, parent: tk.Widget) -> None:
        """カテゴリ別統計を作成"""
        cat_label = tk.Label(
            parent,
            text="カテゴリ別成績:",
            font=self.fonts['normal'],
            bg=self.colors['bg'],
            anchor='w'
        )
        cat_label.pack(fill=tk.X, pady=(5, 0))
        
        for category, stats in self.results_data['category_stats'].items():
            if stats['total'] > 0:
                accuracy = (stats['correct'] / stats['total']) * 100
                stats_text = f"  {category}: {stats['correct']}/{stats['total']} ({accuracy:.1f}%)"
                
                stats_label = tk.Label(
                    parent,
                    text=stats_text,
                    font=('Arial', 10),
                    bg=self.colors['bg'],
                    anchor='w'
                )
                stats_label.pack(fill=tk.X)
    
    def create_difficulty_stats(self, parent: tk.Widget) -> None:
        """難易度別統計を作成"""
        diff_label = tk.Label(
            parent,
            text="難易度別成績:",
            font=self.fonts['normal'],
            bg=self.colors['bg'],
            anchor='w'
        )
        diff_label.pack(fill=tk.X, pady=(10, 0))
        
        for difficulty, stats in self.results_data['difficulty_stats'].items():
            if stats['total'] > 0:
                accuracy = (stats['correct'] / stats['total']) * 100
                stats_text = f"  {difficulty}: {stats['correct']}/{stats['total']} ({accuracy:.1f}%)"
                
                stats_label = tk.Label(
                    parent,
                    text=stats_text,
                    font=('Arial', 10),
                    bg=self.colors['bg'],
                    anchor='w'
                )
                stats_label.pack(fill=tk.X)
    
    def create_wrong_questions_display(self, parent: tk.Widget) -> None:
        """間違えた問題表示を作成"""
        wrong_frame, content_frame = self.create_info_frame(parent, "間違えた問題")
        wrong_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 20))
        
        # スクロール可能なテキストエリア
        text_frame = tk.Frame(content_frame, bg=self.colors['bg'])
        text_frame.pack(fill=tk.BOTH, expand=True)
        
        text_widget = tk.Text(
            text_frame,
            height=8,
            font=('Arial', 10),
            wrap=tk.WORD,
            bg=self.colors['question_bg']
        )
        
        scrollbar = tk.Scrollbar(text_frame, orient=tk.VERTICAL, command=text_widget.yview)
        text_widget.configure(yscrollcommand=scrollbar.set)
        
        text_widget.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        # 間違えた問題の詳細を表示
        for i, wrong in enumerate(self.results_data['wrong_questions'], 1):
            question = wrong['question']
            selected_option = question['options'][wrong['selected_option']]
            correct_option = question['options'][wrong['correct_answer']]
            
            text_widget.insert(tk.END, f"{i}. {question['text']}\n")
            text_widget.insert(tk.END, f"   あなたの回答: {selected_option}\n")
            text_widget.insert(tk.END, f"   正解: {correct_option}\n")
            
            if question.get('explanation'):
                text_widget.insert(tk.END, f"   解説: {question['explanation']}\n")
            
            text_widget.insert(tk.END, "\n")
        
        text_widget.configure(state=tk.DISABLED)
    
    def create_action_buttons(self, parent: tk.Widget) -> None:
        """アクションボタンを作成"""
        button_frame = tk.Frame(parent, bg=self.colors['bg'])
        button_frame.pack(pady=20)
        
        # もう一度ボタン
        restart_btn = self.create_button(
            button_frame,
            "🔄 もう一度",
            lambda: self.callbacks.get('restart', lambda: None)(),
            'primary',
            width=12,
            height=2
        )
        restart_btn.pack(side=tk.LEFT, padx=5)
        
        # 間違えた問題のみボタン（間違いがある場合のみ）
        if self.results_data.get('wrong_questions'):
            retry_btn = self.create_button(
                button_frame,
                "❌ 間違えた問題のみ",
                lambda: self.callbacks.get('retry_wrong', lambda: None)(),
                'warning',
                width=16,
                height=2
            )
            retry_btn.pack(side=tk.LEFT, padx=5)
        
        # 統計情報ボタン
        stats_btn = self.create_button(
            button_frame,
            "📊 統計情報",
            lambda: self.callbacks.get('show_statistics', lambda: None)(),
            'secondary',
            width=12,
            height=2
        )
        stats_btn.pack(side=tk.LEFT, padx=5)
        
        # メニューに戻るボタン
        menu_btn = self.create_button(
            button_frame,
            "🏠 メニューに戻る",
            lambda: self.callbacks.get('back_to_menu', lambda: None)(),
            'success',
            width=14,
            height=2
        )
        menu_btn.pack(side=tk.LEFT, padx=5)