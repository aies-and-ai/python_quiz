"""
tkinterを使用したクイズアプリのUIクラス
"""

import tkinter as tk
import os
from tkinter import ttk, messagebox, scrolledtext
from typing import Callable, Optional, Dict, List
import config


class QuizUI:
    """クイズアプリのUIを管理するクラス"""
    
    def __init__(self, root: tk.Tk):
        """
        初期化
        
        Args:
            root (tk.Tk): メインウィンドウ
        """
        self.root = root
        self.setup_window()
        
        # コールバック関数
        self.on_answer_callback: Optional[Callable] = None
        self.on_next_callback: Optional[Callable] = None
        self.on_restart_callback: Optional[Callable] = None
        self.on_retry_wrong_callback: Optional[Callable] = None
        self.on_show_history_callback: Optional[Callable] = None
        self.on_show_statistics_callback: Optional[Callable] = None
        self.on_start_quiz_callback: Optional[Callable] = None
        self.on_settings_callback: Optional[Callable] = None
        
        # UI要素
        self.current_frame = None
        self.quiz_started = False  # クイズが開始されているかのフラグ
        self.create_main_frame()
    
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
    
    def create_main_frame(self) -> None:
        """メインフレームを作成"""
        if self.current_frame:
            self.current_frame.destroy()
        
        self.current_frame = tk.Frame(self.root, bg=config.BG_COLOR)
        self.current_frame.pack(fill=tk.BOTH, expand=True, padx=config.PADDING, pady=config.PADDING)
    
    def show_start_menu(self, csv_file: str, data_manager=None) -> None:
        """
        スタートメニューを表示
        
        Args:
            csv_file (str): 使用するCSVファイル名
            data_manager: データマネージャー（統計表示用）
        """
        self.create_main_frame()
        self.quiz_started = False
        
        # タイトル
        title_label = tk.Label(
            self.current_frame,
            text="4択クイズアプリ",
            font=("Arial", 24, "bold"),
            bg=config.BG_COLOR,
            fg="#2C3E50"
        )
        title_label.pack(pady=(40, 20))
        
        # CSVファイル名表示
        file_info = tk.Label(
            self.current_frame,
            text=f"問題ファイル: {os.path.basename(csv_file)}",
            font=config.OPTION_FONT,
            bg=config.BG_COLOR,
            fg="#34495E"
        )
        file_info.pack(pady=(0, 30))
        
        # 統計情報があれば簡易表示
        if data_manager:
            try:
                stats = data_manager.get_statistics()
                best_scores = data_manager.get_best_scores()
                csv_key = os.path.basename(csv_file)
                
                stats_text = f"総プレイ回数: {stats['total_quizzes']}回"
                if csv_key in best_scores:
                    best = best_scores[csv_key]
                    stats_text += f" | このファイルのベスト: {best['best_score']}問正解 ({best['best_accuracy']:.1f}%)"
                
                stats_label = tk.Label(
                    self.current_frame,
                    text=stats_text,
                    font=("Arial", 11),
                    bg=config.BG_COLOR,
                    fg="#7F8C8D"
                )
                stats_label.pack(pady=(0, 40))
            except Exception:
                pass  # 統計表示でエラーがあってもメニューは表示
        
        # メニューボタンフレーム
        menu_frame = tk.Frame(self.current_frame, bg=config.BG_COLOR)
        menu_frame.pack(expand=True)
        
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
        history_btn = tk.Button(
            menu_frame,
            text="📊 履歴を見る",
            font=config.BUTTON_FONT,
            command=self._on_show_history_clicked,
            bg="#3498DB",
            fg="white",
            width=20,
            height=2
        )
        history_btn.pack(pady=10)
        
        # 統計情報ボタン
        stats_btn = tk.Button(
            menu_frame,
            text="📈 統計情報",
            font=config.BUTTON_FONT,
            command=self._on_show_statistics_clicked,
            bg="#9B59B6",
            fg="white",
            width=20,
            height=2
        )
        stats_btn.pack(pady=10)
        
        # 設定ボタン
        settings_btn = tk.Button(
            menu_frame,
            text="⚙️ 設定",
            font=config.BUTTON_FONT,
            command=self._on_settings_clicked,
            bg="#95A5A6",
            fg="white",
            width=20,
            height=2
        )
        settings_btn.pack(pady=10)
        
        # 終了ボタン
        quit_btn = tk.Button(
            menu_frame,
            text="❌ 終了",
            font=config.BUTTON_FONT,
            command=self.root.quit,
            bg="#E74C3C",
            fg="white",
            width=20,
            height=2
        )
        quit_btn.pack(pady=15)
    
    def show_question(self, question_data: Dict, progress: Dict) -> None:
        """
        問題を表示
        
        Args:
            question_data (Dict): 問題データ
            progress (Dict): 進行状況
        """
        self.create_main_frame()
        self.quiz_started = True
        
        # 進行状況表示
        progress_text = f"問題 {progress['current']}/{progress['total']} - スコア: {progress['score']}"
        progress_label = tk.Label(
            self.current_frame,
            text=progress_text,
            font=config.SCORE_FONT,
            bg=config.BG_COLOR
        )
        progress_label.pack(pady=(0, 20))
        
        # プログレスバー
        progress_var = tk.DoubleVar(value=progress['percentage'])
        progress_bar = ttk.Progressbar(
            self.current_frame,
            variable=progress_var,
            maximum=100,
            length=400
        )
        progress_bar.pack(pady=(0, 20))
        
        # 問題文表示
        question_frame = tk.Frame(self.current_frame, bg=config.QUESTION_BG, relief=tk.RAISED, bd=2)
        question_frame.pack(fill=tk.X, pady=(0, 30))
        
        question_label = tk.Label(
            question_frame,
            text=question_data['question'],
            font=config.QUESTION_FONT,
            bg=config.QUESTION_BG,
            wraplength=700,
            justify=tk.LEFT
        )
        question_label.pack(padx=20, pady=20)
        
        # 選択肢ボタン
        self.option_buttons = []
        for i, option in enumerate(question_data['options']):
            btn = tk.Button(
                self.current_frame,
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
        
        if self.on_answer_callback:
            self.on_answer_callback(option_index)
    
    def show_answer_result(self, result: Dict) -> None:
        """
        回答結果を表示
        
        Args:
            result (Dict): 回答結果データ
        """
        # 正解・不正解の色付け
        for i, btn in enumerate(self.option_buttons):
            if i == result['correct_answer']:
                btn.configure(bg=config.CORRECT_COLOR)
            elif i == result['selected_option'] and not result['is_correct']:
                btn.configure(bg=config.INCORRECT_COLOR)
        
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
        
        # 解説表示
        if result['question'].get('explanation'):
            explanation_frame = tk.Frame(self.current_frame, bg=config.QUESTION_BG, relief=tk.RAISED, bd=1)
            explanation_frame.pack(fill=tk.X, pady=10)
            
            explanation_label = tk.Label(
                explanation_frame,
                text=f"解説: {result['question']['explanation']}",
                font=config.OPTION_FONT,
                bg=config.QUESTION_BG,
                wraplength=700,
                justify=tk.LEFT
            )
            explanation_label.pack(padx=20, pady=10)
        
        # 次へボタン
        next_btn = tk.Button(
            self.current_frame,
            text="次の問題へ",
            font=config.BUTTON_FONT,
            command=self._on_next_clicked,
            bg="#4CAF50",
            fg="white",
            width=20,
            height=2
        )
        next_btn.pack(pady=20)
    
    def _on_next_clicked(self) -> None:
        """次へボタンがクリックされた時の処理"""
        if self.on_next_callback:
            self.on_next_callback()
    
    def show_final_results(self, results: Dict) -> None:
        """
        最終結果を表示
        
        Args:
            results (Dict): 最終結果データ
        """
        self.create_main_frame()
        
        # タイトル
        title_label = tk.Label(
            self.current_frame,
            text="クイズ結果",
            font=("Arial", 20, "bold"),
            bg=config.BG_COLOR
        )
        title_label.pack(pady=20)
        
        # スコア表示
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
            self.current_frame,
            text=display_text,
            font=config.SCORE_FONT,
            bg=config.BG_COLOR,
            fg="green" if "新記録" in best_info_text else "black"
        )
        score_label.pack(pady=20)
        
        # 間違えた問題の表示
        if results['wrong_questions']:
            wrong_frame = tk.LabelFrame(
                self.current_frame,
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
            
            for i, wrong in enumerate(results['wrong_questions'], 1):
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
        
        # ボタンフレーム
        button_frame = tk.Frame(self.current_frame, bg=config.BG_COLOR)
        button_frame.pack(pady=20)
        
        # 履歴表示ボタン
        history_btn = tk.Button(
            button_frame,
            text="履歴表示",
            font=config.BUTTON_FONT,
            command=self._on_show_history_clicked,
            bg="#9C27B0",
            fg="white",
            width=12,
            height=2
        )
        history_btn.pack(side=tk.LEFT, padx=5)
        
        # 統計表示ボタン
        stats_btn = tk.Button(
            button_frame,
            text="統計情報",
            font=config.BUTTON_FONT,
            command=self._on_show_statistics_clicked,
            bg="#607D8B",
            fg="white",
            width=12,
            height=2
        )
        stats_btn.pack(side=tk.LEFT, padx=5)
        
        # リスタートボタン
        restart_btn = tk.Button(
            button_frame,
            text="もう一度",
            font=config.BUTTON_FONT,
            command=self._on_restart_clicked,
            bg="#2196F3",
            fg="white",
            width=12,
            height=2
        )
        restart_btn.pack(side=tk.LEFT, padx=5)
        
        # 間違えた問題のみボタン
        if results['wrong_questions']:
            retry_btn = tk.Button(
                button_frame,
                text="間違えた問題のみ",
                font=config.BUTTON_FONT,
                command=self._on_retry_wrong_clicked,
                bg="#FF9800",
                fg="white",
                width=15,
                height=2
            )
            retry_btn.pack(side=tk.LEFT, padx=5)
        
        # 終了ボタン
        quit_btn = tk.Button(
            button_frame,
            text="終了",
            font=config.BUTTON_FONT,
            command=self.root.quit,
            bg="#f44336",
            fg="white",
            width=12,
            height=2
        )
        quit_btn.pack(side=tk.LEFT, padx=5)
    
    def _on_restart_clicked(self) -> None:
        """リスタートボタンがクリックされた時の処理"""
        if self.on_restart_callback:
            self.on_restart_callback()
    
    def _on_retry_wrong_clicked(self) -> None:
        """間違えた問題のみボタンがクリックされた時の処理"""
        if self.on_retry_wrong_callback:
            self.on_retry_wrong_callback()
    
    def _on_show_history_clicked(self) -> None:
        """履歴表示ボタンがクリックされた時の処理"""
        if self.on_show_history_callback:
            self.on_show_history_callback()
    
    def _on_show_statistics_clicked(self) -> None:
        """統計情報ボタンがクリックされた時の処理"""
        if self.on_show_statistics_callback:
            self.on_show_statistics_callback()
    
    def _on_start_quiz_clicked(self) -> None:
        """クイズ開始ボタンがクリックされた時の処理"""
        if self.on_start_quiz_callback:
            self.on_start_quiz_callback()
    
    def _on_settings_clicked(self) -> None:
        """設定ボタンがクリックされた時の処理"""
        if self.on_settings_callback:
            self.on_settings_callback()
    
    def show_history(self, history: List[Dict], best_scores: Dict, statistics: Dict) -> None:
        """
        履歴を表示
        
        Args:
            history (List[Dict]): クイズ履歴
            best_scores (Dict): ベストスコア
            statistics (Dict): 統計情報
        """
        self.create_main_frame()
        
        # タイトル
        title_label = tk.Label(
            self.current_frame,
            text="クイズ履歴",
            font=("Arial", 18, "bold"),
            bg=config.BG_COLOR
        )
        title_label.pack(pady=(0, 20))
        
        # 統計サマリー
        stats_text = f"総プレイ回数: {statistics['total_quizzes']}回 | 全体正答率: {statistics.get('overall_accuracy', 0):.1f}%"
        stats_label = tk.Label(
            self.current_frame,
            text=stats_text,
            font=config.SCORE_FONT,
            bg=config.BG_COLOR
        )
        stats_label.pack(pady=(0, 15))
        
        # 履歴表示用スクロールエリア
        history_frame = tk.LabelFrame(
            self.current_frame,
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
        
        # 戻るボタン
        back_btn = tk.Button(
            self.current_frame,
            text="🔙 メニューに戻る",
            font=config.BUTTON_FONT,
            command=self._go_back_to_menu,
            bg="#4CAF50",
            fg="white",
            width=20,
            height=2
        )
        back_btn.pack(pady=10)
    
    def show_statistics(self, statistics: Dict, wrong_summary: Dict, recent_performance: List[Dict]) -> None:
        """
        統計情報を表示
        
        Args:
            statistics (Dict): 統計情報
            wrong_summary (Dict): 間違いサマリー
            recent_performance (List[Dict]): 最近のパフォーマンス
        """
        self.create_main_frame()
        
        # タイトル
        title_label = tk.Label(
            self.current_frame,
            text="統計情報",
            font=("Arial", 18, "bold"),
            bg=config.BG_COLOR
        )
        title_label.pack(pady=(0, 20))
        
        # 統計情報表示
        stats_text = f"""総プレイ回数: {statistics['total_quizzes']}回
総問題数: {statistics['total_questions']}問
総正解数: {statistics['total_correct']}問
全体正答率: {statistics.get('overall_accuracy', 0):.1f}%"""
        
        stats_label = tk.Label(
            self.current_frame,
            text=stats_text,
            font=config.OPTION_FONT,
            bg=config.BG_COLOR,
            justify=tk.LEFT
        )
        stats_label.pack(pady=(0, 20))
        
        # よく間違える問題
        if wrong_summary:
            wrong_frame = tk.LabelFrame(
                self.current_frame,
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
        
        # 戻るボタン
        back_btn = tk.Button(
            self.current_frame,
            text="🔙 メニューに戻る",
            font=config.BUTTON_FONT,
            command=self._go_back_to_menu,
            bg="#4CAF50",
            fg="white",
            width=20,
            height=2
        )
        back_btn.pack(pady=10)
    
    def _go_back_to_results(self) -> None:
        """結果画面に戻る（簡易実装）"""
        if self.quiz_started:
            self.show_info("結果画面に戻るには「もう一度」を押してください")
        else:
            # クイズ未開始の場合はメニューに戻る
            if self.on_restart_callback:
                self.on_restart_callback()
    
    def _go_back_to_menu(self) -> None:
        """メニューに戻る"""
        if self.on_restart_callback:
            self.on_restart_callback()
    
    def show_settings(self, current_settings: Dict) -> None:
        """
        設定画面を表示
        
        Args:
            current_settings (Dict): 現在の設定値
        """
        self.create_main_frame()
        
        # タイトル
        title_label = tk.Label(
            self.current_frame,
            text="⚙️ 設定",
            font=("Arial", 18, "bold"),
            bg=config.BG_COLOR
        )
        title_label.pack(pady=(20, 30))
        
        # 設定項目フレーム
        settings_frame = tk.Frame(self.current_frame, bg=config.BG_COLOR)
        settings_frame.pack(expand=True)
        
        # 問題シャッフル設定
        shuffle_frame = tk.Frame(settings_frame, bg=config.BG_COLOR)
        shuffle_frame.pack(pady=15, fill=tk.X)
        
        tk.Label(
            shuffle_frame,
            text="問題の順序をシャッフル:",
            font=config.OPTION_FONT,
            bg=config.BG_COLOR
        ).pack(side=tk.LEFT)
        
        self.shuffle_questions_var = tk.BooleanVar(value=current_settings.get('shuffle_questions', True))
        shuffle_check = tk.Checkbutton(
            shuffle_frame,
            variable=self.shuffle_questions_var,
            bg=config.BG_COLOR,
            font=config.OPTION_FONT
        )
        shuffle_check.pack(side=tk.RIGHT)
        
        # 選択肢シャッフル設定
        options_frame = tk.Frame(settings_frame, bg=config.BG_COLOR)
        options_frame.pack(pady=15, fill=tk.X)
        
        tk.Label(
            options_frame,
            text="選択肢の順序をシャッフル:",
            font=config.OPTION_FONT,
            bg=config.BG_COLOR
        ).pack(side=tk.LEFT)
        
        self.shuffle_options_var = tk.BooleanVar(value=current_settings.get('shuffle_options', True))
        options_check = tk.Checkbutton(
            options_frame,
            variable=self.shuffle_options_var,
            bg=config.BG_COLOR,
            font=config.OPTION_FONT
        )
        options_check.pack(side=tk.RIGHT)
        
        # 自動保存設定
        save_frame = tk.Frame(settings_frame, bg=config.BG_COLOR)
        save_frame.pack(pady=15, fill=tk.X)
        
        tk.Label(
            save_frame,
            text="結果を自動保存:",
            font=config.OPTION_FONT,
            bg=config.BG_COLOR
        ).pack(side=tk.LEFT)
        
        self.auto_save_var = tk.BooleanVar(value=current_settings.get('auto_save', True))
        save_check = tk.Checkbutton(
            save_frame,
            variable=self.auto_save_var,
            bg=config.BG_COLOR,
            font=config.OPTION_FONT
        )
        save_check.pack(side=tk.RIGHT)
        
        # ボタンフレーム
        button_frame = tk.Frame(self.current_frame, bg=config.BG_COLOR)
        button_frame.pack(pady=30)
        
        # 設定保存ボタン
        save_btn = tk.Button(
            button_frame,
            text="💾 設定を保存",
            font=config.BUTTON_FONT,
            command=self._save_settings,
            bg="#27AE60",
            fg="white",
            width=15,
            height=2
        )
        save_btn.pack(side=tk.LEFT, padx=10)
        
        # メニューに戻るボタン
        back_btn = tk.Button(
            button_frame,
            text="🔙 メニューに戻る",
            font=config.BUTTON_FONT,
            command=self._go_back_to_menu,
            bg="#95A5A6",
            fg="white",
            width=15,
            height=2
        )
        back_btn.pack(side=tk.LEFT, padx=10)
    
    def _save_settings(self) -> None:
        """設定を保存"""
        settings = {
            'shuffle_questions': self.shuffle_questions_var.get(),
            'shuffle_options': self.shuffle_options_var.get(),
            'auto_save': self.auto_save_var.get()
        }
        
        if self.on_settings_callback:
            self.on_settings_callback(settings)
        
        self.show_info("設定を保存しました")
        self._go_back_to_menu()
    
    def show_error(self, message: str) -> None:
        """エラーメッセージを表示"""
        messagebox.showerror("エラー", message)
    
    def show_info(self, message: str) -> None:
        """情報メッセージを表示"""
        messagebox.showinfo("情報", message)
    
    def set_callbacks(self, 
                     on_answer: Callable = None,
                     on_next: Callable = None,
                     on_restart: Callable = None,
                     on_retry_wrong: Callable = None,
                     on_show_history: Callable = None,
                     on_show_statistics: Callable = None,
                     on_start_quiz: Callable = None,
                     on_settings: Callable = None) -> None:
        """コールバック関数を設定"""
        self.on_answer_callback = on_answer
        self.on_next_callback = on_next
        self.on_restart_callback = on_restart
        self.on_retry_wrong_callback = on_retry_wrong
        self.on_show_history_callback = on_show_history
        self.on_show_statistics_callback = on_show_statistics
        self.on_start_quiz_callback = on_start_quiz
        self.on_settings_callback = on_settings