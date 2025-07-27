"""
クイズアプリのコントローラークラス - ゲームロジックを制御
"""

import tkinter as tk
import os
from typing import Dict
from quiz_data import QuizData
from ui.ui_manager import UIManager
from data_manager import QuizDataManager
from exceptions import QuizAppError, CSVFormatError, FileNotFoundError
import config


class QuizController:
    """クイズアプリのメインコントローラー"""
    
    def __init__(self, csv_file: str = None):
        """
        初期化
        
        Args:
            csv_file (str): CSVファイルのパス
        """
        self.csv_file = csv_file or config.DEFAULT_CSV_FILE
        self.quiz_data = None
        self.ui_manager = None
        self.root = None
        self.data_manager = QuizDataManager(config.DATA_FILE) if config.AUTO_SAVE else None
        
        self.current_answer_result = None
        self.current_settings = {
            'shuffle_questions': config.SHUFFLE_QUESTIONS,
            'shuffle_options': config.SHUFFLE_OPTIONS,
            'auto_save': config.AUTO_SAVE
        }
    
    def start_application(self) -> None:
        """アプリケーションを開始"""
        try:
            print("tkinterウィンドウを作成中...")
            # tkinterのメインウィンドウを作成
            self.root = tk.Tk()
            print("tkinterウィンドウ作成完了")
            
            print("UI管理クラスを初期化中...")
            # UI管理クラスを初期化
            self.ui_manager = UIManager(self.root)
            print("UI管理クラス初期化完了")
            
            print("コールバックを設定中...")
            # コールバックを設定
            self.ui_manager.set_callbacks(
                # スタートメニュー
                on_start_quiz=self.handle_start_quiz,
                on_show_history=self.handle_show_history,
                on_show_statistics=self.handle_show_statistics,
                on_show_settings=self.handle_show_settings,
                on_quit=self.handle_quit,
                
                # クイズ
                on_answer=self.handle_answer,
                on_next=self.handle_next_question,
                
                # 結果
                on_restart=self.handle_restart,
                on_retry_wrong=self.handle_retry_wrong,
                
                # 設定
                on_save_settings=self.handle_save_settings,
                
                # 共通
                on_back_to_menu=self.handle_back_to_menu
            )
            print("コールバック設定完了")
            
            print("クイズデータを読み込み中...")
            # クイズデータを読み込み
            self.initialize_quiz(
                shuffle=config.SHUFFLE_QUESTIONS,
                shuffle_options=config.SHUFFLE_OPTIONS
            )
            print("クイズデータ読み込み完了")
            
            print("スタートメニューを表示中...")
            # スタートメニューを表示
            self.show_start_menu()
            print("スタートメニュー表示完了")
            
            print("メインループを開始します...")
            # メインループを開始
            self.root.mainloop()
            print("メインループが終了しました")
            
        except Exception as e:
            print(f"start_application内でエラー: {e}")
            import traceback
            traceback.print_exc()
            if self.ui_manager:
                self.ui_manager.show_error(f"アプリケーションの開始に失敗しました: {str(e)}")
            else:
                print(f"アプリケーションの開始に失敗しました: {str(e)}")
    
    def initialize_quiz(self, shuffle: bool = True, shuffle_options: bool = True) -> None:
        """
        クイズを初期化
        
        Args:
            shuffle (bool): 問題をシャッフルするかどうか
            shuffle_options (bool): 選択肢をシャッフルするかどうか
        """
        try:
            self.quiz_data = QuizData(self.csv_file, shuffle=shuffle, shuffle_options=shuffle_options)
        except FileNotFoundError as e:
            raise QuizAppError(f"CSVファイルが見つかりません: {self.csv_file}")
        except CSVFormatError as e:
            raise QuizAppError(f"CSVファイルの形式が正しくありません: {str(e)}")
        except Exception as e:
            raise QuizAppError(f"クイズデータの読み込みに失敗しました: {str(e)}")
    
    def show_start_menu(self) -> None:
        """スタートメニューを表示"""
        self.ui_manager.show_start_menu(self.csv_file, self.data_manager)
    
    def handle_start_quiz(self) -> None:
        """クイズ開始処理"""
        self.show_current_question()
    
    def handle_show_history(self) -> None:
        """履歴を表示"""
        if not self.data_manager:
            self.ui_manager.show_info("データ保存機能が無効です")
            return
        
        try:
            history = self.data_manager.get_quiz_history(limit=10)
            best_scores = self.data_manager.get_best_scores()
            statistics = self.data_manager.get_statistics()
            
            self.ui_manager.show_history(history, best_scores, statistics)
        except Exception as e:
            self.ui_manager.show_error(f"履歴の表示に失敗しました: {str(e)}")
    
    def handle_show_statistics(self) -> None:
        """統計情報を表示"""
        if not self.data_manager:
            self.ui_manager.show_info("データ保存機能が無効です")
            return
        
        try:
            statistics = self.data_manager.get_statistics()
            wrong_summary = self.data_manager.get_wrong_questions_summary()
            recent_performance = self.data_manager.get_recent_performance(self.csv_file)
            
            self.ui_manager.show_statistics(statistics, wrong_summary, recent_performance)
        except Exception as e:
            self.ui_manager.show_error(f"統計情報の表示に失敗しました: {str(e)}")
    
    def handle_show_settings(self) -> None:
        """設定画面を表示"""
        self.ui_manager.show_settings(self.current_settings)
    
    def handle_save_settings(self, settings: Dict) -> None:
        """設定を保存"""
        # 設定を更新
        self.current_settings.update(settings)
        
        # 設定をconfigに反映（一時的）
        config.SHUFFLE_QUESTIONS = settings.get('shuffle_questions', True)
        config.SHUFFLE_OPTIONS = settings.get('shuffle_options', True)
        config.AUTO_SAVE = settings.get('auto_save', True)
        
        # データマネージャーの更新
        if config.AUTO_SAVE and not self.data_manager:
            self.data_manager = QuizDataManager(config.DATA_FILE)
        elif not config.AUTO_SAVE:
            self.data_manager = None
    
    def handle_quit(self) -> None:
        """アプリを終了"""
        self.root.quit()
    
    def handle_back_to_menu(self) -> None:
        """メニューに戻る"""
        self.show_start_menu()
    
    def show_current_question(self) -> None:
        """現在の問題を表示"""
        if not self.quiz_data.has_next_question():
            self.show_final_results()
            return
        
        question_data = self.quiz_data.get_current_question()
        progress = self.quiz_data.get_progress()
        
        self.ui_manager.show_question(question_data, progress)
    
    def handle_answer(self, selected_option: int) -> None:
        """
        回答を処理
        
        Args:
            selected_option (int): 選択された選択肢のインデックス
        """
        try:
            self.current_answer_result = self.quiz_data.answer_question(selected_option)
            self.ui_manager.show_answer_result(self.current_answer_result)
        except Exception as e:
            self.ui_manager.show_error(f"回答の処理中にエラーが発生しました: {str(e)}")
    
    def handle_next_question(self) -> None:
        """次の問題への遷移を処理"""
        if self.quiz_data.has_next_question():
            self.show_current_question()
        else:
            self.show_final_results()
    
    def show_final_results(self) -> None:
        """最終結果を表示"""
        results = self.quiz_data.get_final_results()
        
        # データを保存
        if self.data_manager and self.current_settings['auto_save']:
            try:
                self.data_manager.save_quiz_result(results, self.csv_file)
                
                # ベストスコア情報を取得
                best_scores = self.data_manager.get_best_scores()
                csv_key = os.path.basename(self.csv_file)
                if csv_key in best_scores:
                    results['best_score_info'] = best_scores[csv_key]
                
            except Exception as e:
                print(f"データ保存エラー: {e}")  # エラーでもクイズは続行
        
        self.ui_manager.show_results(results)
    
    def handle_restart(self) -> None:
        """クイズを最初から再開 / メニューに戻る"""
        try:
            # 設定を反映してクイズを再初期化
            self.initialize_quiz(
                shuffle=self.current_settings['shuffle_questions'],
                shuffle_options=self.current_settings['shuffle_options']
            )
            # スタートメニューを表示
            self.show_start_menu()
        except Exception as e:
            self.ui_manager.show_error(f"メニューへの復帰に失敗しました: {str(e)}")
    
    def handle_retry_wrong(self) -> None:
        """間違えた問題のみを再実行"""
        try:
            if not self.quiz_data.wrong_questions:
                self.ui_manager.show_info("間違えた問題がありません")
                return
            
            self.quiz_data.restart_with_wrong_questions()
            self.show_current_question()
        except Exception as e:
            self.ui_manager.show_error(f"間違えた問題の再実行に失敗しました: {str(e)}")
    
    def run(self) -> None:
        """アプリケーションを実行（start_applicationのエイリアス）"""
        self.start_application()