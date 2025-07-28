"""
メインウィンドウ - 新アーキテクチャ統合UI
全ての画面を統合管理するメインウィンドウクラス
"""

import tkinter as tk
from tkinter import messagebox, filedialog
from typing import Dict, Any, Optional
from pathlib import Path

from app.config import get_settings
from utils.logger import get_logger


class MainWindow:
    """メインウィンドウ - 全画面統合管理"""
    
    def __init__(self, root: tk.Tk, controller):
        """初期化"""
        self.root = root
        self.controller = controller
        self.settings = get_settings()
        self.logger = get_logger()
        
        # 現在表示中のフレーム
        self.current_frame: Optional[tk.Frame] = None
        
        # UI状態
        self.quiz_in_progress = False
        
        self._setup_window()
        self.logger.info("メインウィンドウ初期化完了")
    
    def _setup_window(self):
        """ウィンドウの基本設定"""
        self.root.title(self.settings.window_title)
        self.root.geometry(f"{self.settings.window_width}x{self.settings.window_height}")
        self.root.configure(bg="#f0f0f0")
        
        # ウィンドウを中央に配置
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (self.settings.window_width // 2)
        y = (self.root.winfo_screenheight() // 2) - (self.settings.window_height // 2)
        self.root.geometry(f"{self.settings.window_width}x{self.settings.window_height}+{x}+{y}")
        
        # 終了処理のバインド
        self.root.protocol("WM_DELETE_WINDOW", self._on_window_close)
    
    def _clear_frame(self):
        """現在のフレームをクリア"""
        if self.current_frame:
            self.current_frame.destroy()
        self.current_frame = tk.Frame(self.root, bg="#f0f0f0")
        self.current_frame.pack(fill=tk.BOTH, expand=True, padx=20, pady=20)
    
    # === メインメニュー ===
    
    def show_main_menu(self):
        """メインメニューを表示"""
        self.quiz_in_progress = False
        self._clear_frame()
        
        # アプリ情報取得
        app_info = self.controller.get_app_info()
        
        # タイトル
        title = tk.Label(
            self.current_frame,
            text="🎯 4択クイズアプリ",
            font=("Arial", 24, "bold"),
            bg="#f0f0f0",
            fg="#2C3E50"
        )
        title.pack(pady=(20, 30))
        
        # 情報表示
        info_text = f"利用可能問題数: {app_info.get('question_count', 0)}問"
        if app_info.get('categories'):
            info_text += f" | カテゴリ: {len(app_info['categories'])}種類"
        
        info_label = tk.Label(
            self.current_frame,
            text=info_text,
            font=("Arial", 12),
            bg="#f0f0f0",
            fg="#7F8C8D"
        )
        info_label.pack(pady=(0, 30))
        
        # メニューボタンフレーム
        menu_frame = tk.Frame(self.current_frame, bg="#f0f0f0")
        menu_frame.pack(expand=True)
        
        # クイズ開始ボタン
        if app_info.get('has_questions', False):
            start_btn = tk.Button(
                menu_frame,
                text="🚀 クイズを開始",
                font=("Arial", 16, "bold"),
                command=self._show_quiz_config,
                bg="#27AE60",
                fg="white",
                width=20,
                height=2,
                relief=tk.RAISED,
                bd=3
            )
            start_btn.pack(pady=10)
        else:
            # 問題がない場合はCSVインポートボタン
            import_btn = tk.Button(
                menu_frame,
                text="📁 CSVファイルをインポート",
                font=("Arial", 14, "bold"),
                command=self._import_csv_file,
                bg="#E67E22",
                fg="white",
                width=25,
                height=2
            )
            import_btn.pack(pady=10)
        
        # 統計ボタン
        stats_btn = tk.Button(
            menu_frame,
            text="📊 統計情報",
            font=("Arial", 12),
            command=self.controller.show_statistics,
            bg="#3498DB",
            fg="white",
            width=20,
            height=2
        )
        stats_btn.pack(pady=5)
        
        # 設定ボタン
        settings_btn = tk.Button(
            menu_frame,
            text="⚙️ 設定",
            font=("Arial", 12),
            command=self.controller.show_settings,
            bg="#95A5A6",
            fg="white",
            width=20,
            height=2
        )
        settings_btn.pack(pady=5)
        
        # CSVインポートボタン（問題がある場合でも表示）
        if app_info.get('has_questions', False):
            import_btn = tk.Button(
                menu_frame,
                text="📁 CSVファイル追加",
                font=("Arial", 10),
                command=self._import_csv_file,
                bg="#95A5A6",
                fg="white",
                width=20,
                height=1
            )
            import_btn.pack(pady=5)
        
        # 終了ボタン
        quit_btn = tk.Button(
            menu_frame,
            text="❌ 終了",
            font=("Arial", 12),
            command=self._on_window_close,
            bg="#E74C3C",
            fg="white",
            width=20,
            height=2
        )
        quit_btn.pack(pady=15)
    
    def _show_quiz_config(self):
        """クイズ設定画面を表示"""
        self._clear_frame()
        
        # タイトル
        title = tk.Label(
            self.current_frame,
            text="クイズ設定",
            font=("Arial", 18, "bold"),
            bg="#f0f0f0"
        )
        title.pack(pady=20)
        
        # 設定フレーム
        config_frame = tk.Frame(self.current_frame, bg="#f0f0f0")
        config_frame.pack(expand=True)
        
        # 問題数設定
        tk.Label(config_frame, text="問題数:", font=("Arial", 12), bg="#f0f0f0").pack(pady=5)
        
        question_count_var = tk.StringVar(value=str(self.settings.default_question_count))
        question_count_entry = tk.Entry(config_frame, textvariable=question_count_var, font=("Arial", 12), width=10)
        question_count_entry.pack(pady=5)
        
        # カテゴリ選択（利用可能な場合）
        app_info = self.controller.get_app_info()
        category_var = tk.StringVar(value="すべて")
        
        if app_info.get('categories'):
            tk.Label(config_frame, text="カテゴリ:", font=("Arial", 12), bg="#f0f0f0").pack(pady=(20, 5))
            
            categories = ["すべて"] + app_info['categories']
            category_menu = tk.OptionMenu(config_frame, category_var, *categories)
            category_menu.config(font=("Arial", 12))
            category_menu.pack(pady=5)
        
        # 難易度選択（利用可能な場合）
        difficulty_var = tk.StringVar(value="すべて")
        
        if app_info.get('difficulties'):
            tk.Label(config_frame, text="難易度:", font=("Arial", 12), bg="#f0f0f0").pack(pady=(20, 5))
            
            difficulties = ["すべて"] + app_info['difficulties']
            difficulty_menu = tk.OptionMenu(config_frame, difficulty_var, *difficulties)
            difficulty_menu.config(font=("Arial", 12))
            difficulty_menu.pack(pady=5)
        
        # ボタンフレーム
        button_frame = tk.Frame(config_frame, bg="#f0f0f0")
        button_frame.pack(pady=30)
        
        # 開始ボタン
        def start_quiz():
            try:
                question_count = int(question_count_var.get())
                category = None if category_var.get() == "すべて" else category_var.get()
                difficulty = None if difficulty_var.get() == "すべて" else difficulty_var.get()
                
                # パラメータ検証
                is_valid, error_msg = self.controller.validate_quiz_start_params(
                    question_count, category, difficulty
                )
                
                if not is_valid:
                    self.show_error(error_msg)
                    return
                
                # クイズ開始
                if self.controller.start_new_quiz(question_count, category, difficulty):
                    self.quiz_in_progress = True
                
            except ValueError:
                self.show_error("問題数は数値で入力してください")
        
        start_btn = tk.Button(
            button_frame,
            text="🚀 開始",
            font=("Arial", 14, "bold"),
            command=start_quiz,
            bg="#27AE60",
            fg="white",
            width=15,
            height=2
        )
        start_btn.pack(side=tk.LEFT, padx=10)
        
        # 戻るボタン
        back_btn = tk.Button(
            button_frame,
            text="🔙 戻る",
            font=("Arial", 12),
            command=self.show_main_menu,
            bg="#95A5A6",
            fg="white",
            width=15,
            height=2
        )
        back_btn.pack(side=tk.LEFT, padx=10)
    
    # === クイズ画面 ===
    
    def show_question(self, question, progress):
        """問題を表示"""
        self.quiz_in_progress = True
        self._clear_frame()
        
        # 進行状況
        progress_text = f"問題 {progress['current_index'] + 1}/{progress['total_questions']} - スコア: {progress['score']}"
        progress_label = tk.Label(
            self.current_frame,
            text=progress_text,
            font=("Arial", 14, "bold"),
            bg="#f0f0f0"
        )
        progress_label.pack(pady=10)
        
        # 問題文
        question_frame = tk.Frame(self.current_frame, bg="white", relief=tk.RAISED, bd=2)
        question_frame.pack(fill=tk.X, pady=20)
        
        question_label = tk.Label(
            question_frame,
            text=question.text,
            font=("Arial", 14),
            bg="white",
            wraplength=600,
            justify=tk.LEFT
        )
        question_label.pack(padx=20, pady=20)
        
        # 選択肢
        for i, option in enumerate(question.options):
            option_btn = tk.Button(
                self.current_frame,
                text=f"{i+1}. {option}",
                font=("Arial", 12),
                bg="#ecf0f1",
                width=60,
                height=2,
                wraplength=500,
                justify=tk.LEFT,
                command=lambda idx=i: self.controller.answer_question(idx)
            )
            option_btn.pack(fill=tk.X, pady=5)
    
    def show_answer_result(self, result):
        """回答結果を表示"""
        # 結果メッセージ
        result_text = "✅ 正解！" if result['is_correct'] else "❌ 不正解"
        result_color = "green" if result['is_correct'] else "red"
        
        result_label = tk.Label(
            self.current_frame,
            text=result_text,
            font=("Arial", 16, "bold"),
            fg=result_color,
            bg="#f0f0f0"
        )
        result_label.pack(pady=20)
        
        # 正解表示
        correct_answer = result['question'].options[result['correct_answer']]
        correct_label = tk.Label(
            self.current_frame,
            text=f"正解: {correct_answer}",
            font=("Arial", 12),
            bg="#f0f0f0"
        )
        correct_label.pack(pady=10)
        
        # 解説（あれば）
        if result['explanation']:
            explanation_frame = tk.Frame(self.current_frame, bg="lightyellow", relief=tk.RAISED, bd=1)
            explanation_frame.pack(fill=tk.X, pady=10)
            
            explanation_label = tk.Label(
                explanation_frame,
                text=f"解説: {result['explanation']}",
                font=("Arial", 11),
                bg="lightyellow",
                wraplength=600,
                justify=tk.LEFT
            )
            explanation_label.pack(padx=15, pady=10)
        
        # 次へボタン
        next_btn = tk.Button(
            self.current_frame,
            text="次の問題へ ➡️",
            font=("Arial", 14),
            command=self.controller.next_question,
            bg="#3498DB",
            fg="white",
            width=20,
            height=2
        )
        next_btn.pack(pady=20)
    
    # === 結果画面 ===
    
    def show_results(self, results):
        """最終結果を表示"""
        self.quiz_in_progress = False
        self._clear_frame()
        
        # タイトル
        title = tk.Label(
            self.current_frame,
            text="🎉 クイズ結果",
            font=("Arial", 20, "bold"),
            bg="#f0f0f0"
        )
        title.pack(pady=20)
        
        # スコア表示
        score_text = f"スコア: {results['score']}/{results['total_questions']}"
        accuracy_text = f"正答率: {results['accuracy']:.1f}%"
        
        score_label = tk.Label(
            self.current_frame,
            text=f"{score_text}\n{accuracy_text}",
            font=("Arial", 16, "bold"),
            bg="#f0f0f0"
        )
        score_label.pack(pady=20)
        
        # ボタンフレーム
        button_frame = tk.Frame(self.current_frame, bg="#f0f0f0")
        button_frame.pack(pady=30)
        
        # もう一度ボタン
        retry_btn = tk.Button(
            button_frame,
            text="🔄 もう一度",
            font=("Arial", 12),
            command=self.controller.restart_quiz,
            bg="#3498DB",
            fg="white",
            width=15,
            height=2
        )
        retry_btn.pack(side=tk.LEFT, padx=10)
        
        # 間違えた問題のみボタン（間違いがある場合）
        if results.get('wrong_questions'):
            wrong_only_btn = tk.Button(
                button_frame,
                text="❌ 間違いのみ",
                font=("Arial", 12),
                command=self.controller.retry_wrong_questions,
                bg="#E67E22",
                fg="white",
                width=15,
                height=2
            )
            wrong_only_btn.pack(side=tk.LEFT, padx=10)
        
        # メインメニューボタン
        menu_btn = tk.Button(
            button_frame,
            text="🏠 メニュー",
            font=("Arial", 12),
            command=self.show_main_menu,
            bg="#27AE60",
            fg="white",
            width=15,
            height=2
        )
        menu_btn.pack(side=tk.LEFT, padx=10)
    
    # === その他の画面 ===
    
    def show_statistics(self, stats_data):
        """統計情報を表示"""
        self._clear_frame()
        
        # タイトル
        title = tk.Label(
            self.current_frame,
            text="📊 統計情報",
            font=("Arial", 18, "bold"),
            bg="#f0f0f0"
        )
        title.pack(pady=20)
        
        # 統計データ表示
        stats_text = f"""総セッション数: {stats_data.get('total_sessions', 0)}回
総回答数: {stats_data.get('total_questions_answered', 0)}問
総正解数: {stats_data.get('total_correct_answers', 0)}問
全体正答率: {stats_data.get('overall_accuracy', 0):.1f}%
ベストスコア: {stats_data.get('best_score', 0)}問
ベスト正答率: {stats_data.get('best_accuracy', 0):.1f}%"""
        
        stats_label = tk.Label(
            self.current_frame,
            text=stats_text,
            font=("Arial", 12),
            bg="#f0f0f0",
            justify=tk.LEFT
        )
        stats_label.pack(pady=20)
        
        # 戻るボタン
        back_btn = tk.Button(
            self.current_frame,
            text="🔙 メニューに戻る",
            font=("Arial", 12),
            command=self.show_main_menu,
            bg="#95A5A6",
            fg="white",
            width=20,
            height=2
        )
        back_btn.pack(pady=20)
    
    def show_settings(self, current_settings):
        """設定画面を表示"""
        self._clear_frame()
        
        # タイトル
        title = tk.Label(
            self.current_frame,
            text="⚙️ 設定",
            font=("Arial", 18, "bold"),
            bg="#f0f0f0"
        )
        title.pack(pady=20)
        
        # 設定項目フレーム
        settings_frame = tk.Frame(self.current_frame, bg="#f0f0f0")
        settings_frame.pack(expand=True)
        
        # 設定変数
        shuffle_questions_var = tk.BooleanVar(value=current_settings.get('shuffle_questions', True))
        shuffle_options_var = tk.BooleanVar(value=current_settings.get('shuffle_options', True))
        
        # 問題シャッフル設定
        shuffle_q_frame = tk.Frame(settings_frame, bg="#f0f0f0")
        shuffle_q_frame.pack(pady=15, fill=tk.X)
        
        tk.Label(shuffle_q_frame, text="問題の順序をシャッフル:", font=("Arial", 12), bg="#f0f0f0").pack(side=tk.LEFT)
        tk.Checkbutton(shuffle_q_frame, variable=shuffle_questions_var, bg="#f0f0f0").pack(side=tk.RIGHT)
        
        # 選択肢シャッフル設定
        shuffle_o_frame = tk.Frame(settings_frame, bg="#f0f0f0")
        shuffle_o_frame.pack(pady=15, fill=tk.X)
        
        tk.Label(shuffle_o_frame, text="選択肢の順序をシャッフル:", font=("Arial", 12), bg="#f0f0f0").pack(side=tk.LEFT)
        tk.Checkbutton(shuffle_o_frame, variable=shuffle_options_var, bg="#f0f0f0").pack(side=tk.RIGHT)
        
        # ボタンフレーム
        button_frame = tk.Frame(settings_frame, bg="#f0f0f0")
        button_frame.pack(pady=30)
        
        # 保存ボタン
        def save_settings():
            new_settings = {
                'shuffle_questions': shuffle_questions_var.get(),
                'shuffle_options': shuffle_options_var.get()
            }
            
            if self.controller.save_settings(new_settings):
                self.show_info("設定を保存しました")
                self.show_main_menu()
        
        save_btn = tk.Button(
            button_frame,
            text="💾 保存",
            font=("Arial", 12),
            command=save_settings,
            bg="#27AE60",
            fg="white",
            width=15,
            height=2
        )
        save_btn.pack(side=tk.LEFT, padx=10)
        
        # 戻るボタン
        back_btn = tk.Button(
            button_frame,
            text="🔙 戻る",
            font=("Arial", 12),
            command=self.show_main_menu,
            bg="#95A5A6",
            fg="white",
            width=15,
            height=2
        )
        back_btn.pack(side=tk.LEFT, padx=10)
    
    # === ユーティリティメソッド ===
    
    def _import_csv_file(self):
        """CSVファイルインポート"""
        file_path = filedialog.askopenfilename(
            title="CSVファイルを選択",
            filetypes=[("CSVファイル", "*.csv"), ("すべてのファイル", "*.*")]
        )
        
        if file_path:
            if self.controller.import_csv_file(file_path):
                # 成功時はメニューを更新
                self.show_main_menu()
    
    def show_error(self, message: str):
        """エラーメッセージを表示"""
        messagebox.showerror("エラー", message)
    
    def show_info(self, message: str):
        """情報メッセージを表示"""
        messagebox.showinfo("情報", message)
    
    def _on_window_close(self):
        """ウィンドウ閉じる時の処理"""
        if self.quiz_in_progress:
            result = messagebox.askyesno(
                "確認", 
                "クイズが進行中です。終了しますか？"
            )
            if not result:
                return
        
        self.controller.quit_application()
        self.root.quit()    