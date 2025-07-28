"""
結果表示ウィンドウUI
クイズ結果と統計情報の表示
"""

import tkinter as tk
from typing import Dict, Any
from .base import BaseWindow, ResultsWidget


class ResultWindow(BaseWindow):
    """結果表示ウィンドウクラス"""
    
    def __init__(self, parent: tk.Widget, controller):
        """初期化"""
        super().__init__(parent)
        self.controller = controller
        self.results_widget = None
        
        self.setup_ui(parent)
    
    def setup_ui(self, parent: tk.Widget) -> None:
        """UIセットアップ"""
        self.main_frame = self.create_frame(parent)
        
        # 初期状態では非表示
        self.main_frame.pack_forget()
    
    def show_results(self, results_data: Dict[str, Any]) -> None:
        """結果を表示"""
        # フレームを表示
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 既存のウィジェットを削除
        if self.results_widget:
            for widget in self.main_frame.winfo_children():
                widget.destroy()
        
        # コールバック設定
        callbacks = {
            'restart': self.controller.restart_quiz,
            'retry_wrong': self.controller.retry_wrong_questions,
            'show_statistics': self.controller.show_statistics,
            'back_to_menu': self.controller.restart_quiz
        }
        
        # 結果ウィジェットを作成
        self.results_widget = ResultsWidget(self.main_frame, results_data, callbacks)
    
    def hide(self) -> None:
        """ウィンドウを非表示"""
        self.main_frame.pack_forget()
    
    def show(self) -> None:
        """ウィンドウを表示"""
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)


class StatisticsWindow(BaseWindow):
    """統計情報表示ウィンドウクラス"""
    
    def __init__(self, parent: tk.Widget, controller):
        """初期化"""
        super().__init__(parent)
        self.controller = controller
        
        self.setup_ui(parent)
    
    def setup_ui(self, parent: tk.Widget) -> None:
        """UIセットアップ"""
        self.main_frame = self.create_frame(parent)
        
        # 初期状態では非表示
        self.main_frame.pack_forget()
    
    def show_statistics(self, stats_data: Dict[str, Any]) -> None:
        """統計情報を表示"""
        # フレームを表示
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 既存の内容をクリア
        for widget in self.main_frame.winfo_children():
            widget.destroy()
        
        # タイトル
        title = self.create_title_label(self.main_frame, "📊 統計情報")
        title.pack(pady=(0, 20))
        
        # 統計情報表示
        self.create_statistics_display(stats_data)
        
        # 戻るボタン
        back_btn = self.create_button(
            self.main_frame,
            "🔙 戻る",
            self.hide,
            'primary',
            width=12,
            height=2
        )
        back_btn.pack(pady=20)
    
    def create_statistics_display(self, stats_data: Dict[str, Any]) -> None:
        """統計情報表示を作成"""
        # メイン統計フレーム
        main_stats_frame, content_frame = self.create_info_frame(self.main_frame, "全体統計")
        main_stats_frame.pack(fill=tk.X, pady=(0, 20))
        
        # 統計情報を2列で表示
        stats_container = tk.Frame(content_frame, bg=self.colors['bg'])
        stats_container.pack(fill=tk.X, padx=10, pady=10)
        
        # 左列
        left_frame = tk.Frame(stats_container, bg=self.colors['bg'])
        left_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.create_stat_item(left_frame, "総プレイ回数", f"{stats_data.get('total_sessions', 0)}回")
        self.create_stat_item(left_frame, "総回答数", f"{stats_data.get('total_questions_answered', 0)}問")
        self.create_stat_item(left_frame, "総正解数", f"{stats_data.get('total_correct_answers', 0)}問")
        
        # 右列
        right_frame = tk.Frame(stats_container, bg=self.colors['bg'])
        right_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.create_stat_item(right_frame, "全体正答率", f"{stats_data.get('overall_accuracy', 0):.1f}%")
        self.create_stat_item(right_frame, "最高スコア", f"{stats_data.get('best_score', 0)}問")
        self.create_stat_item(right_frame, "最高正答率", f"{stats_data.get('best_accuracy', 0):.1f}%")
        
        # 成績評価
        self.create_performance_evaluation(stats_data)
    
    def create_stat_item(self, parent: tk.Widget, label: str, value: str) -> None:
        """統計項目を作成"""
        item_frame = tk.Frame(parent, bg=self.colors['bg'])
        item_frame.pack(fill=tk.X, pady=2)
        
        label_widget = tk.Label(
            item_frame,
            text=f"{label}:",
            font=self.fonts['normal'],
            bg=self.colors['bg'],
            fg=self.colors['fg'],
            anchor='w'
        )
        label_widget.pack(side=tk.LEFT)
        
        value_widget = tk.Label(
            item_frame,
            text=value,
            font=('Arial', 12, 'bold'),
            bg=self.colors['bg'],
            fg='#2E7D32',
            anchor='e'
        )
        value_widget.pack(side=tk.RIGHT)
    
    def create_performance_evaluation(self, stats_data: Dict[str, Any]) -> None:
        """成績評価を作成"""
        if stats_data.get('total_sessions', 0) == 0:
            return
        
        eval_frame, content_frame = self.create_info_frame(self.main_frame, "成績評価")
        eval_frame.pack(fill=tk.X, pady=(0, 20))
        
        overall_accuracy = stats_data.get('overall_accuracy', 0)
        
        # 評価メッセージの決定
        if overall_accuracy >= 90:
            evaluation = "🌟 素晴らしい！"
            message = "非常に高い正答率です。知識が豊富ですね！"
            color = '#4CAF50'
        elif overall_accuracy >= 80:
            evaluation = "🎉 とても良い！"
            message = "高い正答率を維持しています。継続して頑張りましょう！"
            color = '#8BC34A'
        elif overall_accuracy >= 70:
            evaluation = "👍 良い成績！"
            message = "安定した成績です。さらなる向上を目指しましょう！"
            color = '#FF9800'
        elif overall_accuracy >= 60:
            evaluation = "📈 向上中！"
            message = "着実に力をつけています。継続が大切です！"
            color = '#FF9800'
        else:
            evaluation = "💪 頑張ろう！"
            message = "諦めずに続けることで必ず向上します！"
            color = '#FF5722'
        
        # 評価表示
        eval_label = tk.Label(
            content_frame,
            text=evaluation,
            font=('Arial', 16, 'bold'),
            bg=self.colors['bg'],
            fg=color
        )
        eval_label.pack(pady=5)
        
        message_label = tk.Label(
            content_frame,
            text=message,
            font=self.fonts['normal'],
            bg=self.colors['bg'],
            fg=self.colors['fg'],
            wraplength=500
        )
        message_label.pack(pady=5)
        
        # 目標メッセージ
        if overall_accuracy < 90:
            next_target = 90 if overall_accuracy < 80 else 95
            improvement_needed = next_target - overall_accuracy
            
            target_label = tk.Label(
                content_frame,
                text=f"次の目標: {next_target}%まであと{improvement_needed:.1f}%！",
                font=('Arial', 10),
                bg=self.colors['bg'],
                fg='#666666'
            )
            target_label.pack(pady=(5, 0))
    
    def hide(self) -> None:
        """ウィンドウを非表示"""
        self.main_frame.pack_forget()
        
        # メインメニューに戻るコールバックを実行
        self.controller.restart_quiz()


class SettingsWindow(BaseWindow):
    """設定ウィンドウクラス"""
    
    def __init__(self, parent: tk.Widget, controller):
        """初期化"""
        super().__init__(parent)
        self.controller = controller
        
        self.setup_ui(parent)
    
    def setup_ui(self, parent: tk.Widget) -> None:
        """UIセットアップ"""
        self.main_frame = self.create_frame(parent)
        
        # 初期状態では非表示
        self.main_frame.pack_forget()
    
    def show_settings(self, current_settings: Dict[str, Any]) -> None:
        """設定画面を表示"""
        # フレームを表示
        self.main_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # 既存の内容をクリア
        for widget in self.main_frame.winfo_children():
            widget.destroy()
        
        # タイトル
        title = self.create_title_label(self.main_frame, "⚙️ 設定")
        title.pack(pady=(0, 30))
        
        # 設定項目を作成
        self.create_settings_items(current_settings)
        
        # ボタン
        self.create_settings_buttons()
    
    def create_settings_items(self, settings: Dict[str, Any]) -> None:
        """設定項目を作成"""
        settings_frame = tk.Frame(self.main_frame, bg=self.colors['bg'])
        settings_frame.pack(expand=True)
        
        # 問題シャッフル設定
        self.shuffle_questions_var = tk.BooleanVar(value=settings.get('shuffle_questions', True))
        self.create_setting_item(
            settings_frame,
            "問題の順序をシャッフル:",
            self.shuffle_questions_var
        )
        
        # 選択肢シャッフル設定
        self.shuffle_options_var = tk.BooleanVar(value=settings.get('shuffle_options', True))
        self.create_setting_item(
            settings_frame,
            "選択肢の順序をシャッフル:",
            self.shuffle_options_var
        )
        
        # デフォルト問題数設定
        count_frame = tk.Frame(settings_frame, bg=self.colors['bg'])
        count_frame.pack(pady=15, fill=tk.X)
        
        tk.Label(
            count_frame,
            text="デフォルト問題数:",
            font=self.fonts['normal'],
            bg=self.colors['bg']
        ).pack(side=tk.LEFT)
        
        self.default_count_var = tk.IntVar(value=settings.get('default_question_count', 10))
        count_spinbox = tk.Spinbox(
            count_frame,
            from_=1,
            to=100,
            textvariable=self.default_count_var,
            width=10
        )
        count_spinbox.pack(side=tk.RIGHT)
        
        # デバッグモード設定
        self.debug_var = tk.BooleanVar(value=settings.get('debug', False))
        self.create_setting_item(
            settings_frame,
            "デバッグモード:",
            self.debug_var
        )
    
    def create_setting_item(self, parent: tk.Widget, text: str, variable: tk.BooleanVar) -> None:
        """設定項目を作成"""
        frame = tk.Frame(parent, bg=self.colors['bg'])
        frame.pack(pady=15, fill=tk.X)
        
        tk.Label(
            frame,
            text=text,
            font=self.fonts['normal'],
            bg=self.colors['bg']
        ).pack(side=tk.LEFT)
        
        tk.Checkbutton(
            frame,
            variable=variable,
            bg=self.colors['bg'],
            font=self.fonts['normal']
        ).pack(side=tk.RIGHT)
    
    def create_settings_buttons(self) -> None:
        """設定ボタンを作成"""
        button_frame = tk.Frame(self.main_frame, bg=self.colors['bg'])
        button_frame.pack(pady=30)
        
        # 保存ボタン
        save_btn = self.create_button(
            button_frame,
            "💾 保存",
            self.save_settings,
            'success',
            width=12,
            height=2
        )
        save_btn.pack(side=tk.LEFT, padx=10)
        
        # キャンセルボタン
        cancel_btn = self.create_button(
            button_frame,
            "❌ キャンセル",
            self.hide,
            'secondary',
            width=12,
            height=2
        )
        cancel_btn.pack(side=tk.LEFT, padx=10)
    
    def save_settings(self) -> None:
        """設定を保存"""
        new_settings = {
            'shuffle_questions': self.shuffle_questions_var.get(),
            'shuffle_options': self.shuffle_options_var.get(),
            'default_question_count': self.default_count_var.get(),
            'debug': self.debug_var.get()
        }
        
        success = self.controller.save_settings(new_settings)
        
        if success:
            self.show_info("設定を保存しました")
            self.hide()
        else:
            self.show_error("設定の保存に失敗しました")
    
    def hide(self) -> None:
        """ウィンドウを非表示"""
        self.main_frame.pack_forget()
        
        # メインメニューに戻るコールバックを実行
        self.controller.restart_quiz()