"""
クイズ結果の保存・履歴管理を行うクラス
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional
from exceptions import QuizDataError


class QuizDataManager:
    """クイズデータの保存・読み込みを管理するクラス"""
    
    def __init__(self, data_file: str = "quiz_history.json"):
        """
        初期化
        
        Args:
            data_file (str): データ保存用JSONファイルのパス
        """
        self.data_file = data_file
        self.history_data = self._load_history()
    
    def _load_history(self) -> Dict:
        """履歴データを読み込む"""
        if not os.path.exists(self.data_file):
            return {
                "version": "1.0",
                "created": datetime.now().isoformat(),
                "quiz_history": [],
                "best_scores": {},
                "statistics": {
                    "total_quizzes": 0,
                    "total_questions": 0,
                    "total_correct": 0
                }
            }
        
        try:
            with open(self.data_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            raise QuizDataError(f"履歴ファイルの読み込みに失敗しました: {str(e)}")
    
    def _save_history(self) -> None:
        """履歴データを保存する"""
        try:
            # バックアップファイルを作成
            if os.path.exists(self.data_file):
                backup_file = f"{self.data_file}.backup"
                if os.path.exists(backup_file):
                    os.remove(backup_file)
                os.rename(self.data_file, backup_file)
            
            with open(self.data_file, 'w', encoding='utf-8') as f:
                json.dump(self.history_data, f, ensure_ascii=False, indent=2)
                
        except IOError as e:
            raise QuizDataError(f"履歴ファイルの保存に失敗しました: {str(e)}")
    
    def save_quiz_result(self, results: Dict, csv_file: str) -> None:
        """
        クイズ結果を保存する
        
        Args:
            results (Dict): クイズの最終結果
            csv_file (str): 使用したCSVファイル名
        """
        # クイズ結果の記録
        quiz_record = {
            "timestamp": datetime.now().isoformat(),
            "csv_file": os.path.basename(csv_file),
            "total_questions": results['total_questions'],
            "score": results['score'],
            "accuracy": results['accuracy'],
            "wrong_count": len(results['wrong_questions']),
            "duration_seconds": None,  # 将来の時間計測機能用
            "wrong_questions": [
                {
                    "question": wrong['question']['question'],
                    "selected_option": wrong['question']['options'][wrong['selected_option']],
                    "correct_option": wrong['question']['options'][wrong['correct_answer']],
                    "explanation": wrong['question'].get('explanation', '')
                }
                for wrong in results['wrong_questions']
            ]
        }
        
        # 履歴に追加
        self.history_data["quiz_history"].append(quiz_record)
        
        # ベストスコアの更新
        self._update_best_score(csv_file, results)
        
        # 統計の更新
        self._update_statistics(results)
        
        # ファイルに保存
        self._save_history()
    
    def _update_best_score(self, csv_file: str, results: Dict) -> None:
        """ベストスコアを更新する"""
        file_key = os.path.basename(csv_file)
        
        if file_key not in self.history_data["best_scores"]:
            # 初回記録
            self.history_data["best_scores"][file_key] = {
                "best_score": results['score'],
                "best_accuracy": results['accuracy'],
                "total_questions": results['total_questions'],
                "achieved_date": datetime.now().isoformat(),
                "play_count": 1
            }
        else:
            # 既存記録の更新
            best_data = self.history_data["best_scores"][file_key]
            best_data["play_count"] += 1
            
            # スコア更新判定
            if results['score'] > best_data["best_score"]:
                best_data["best_score"] = results['score']
                best_data["best_accuracy"] = results['accuracy']
                best_data["achieved_date"] = datetime.now().isoformat()
            elif results['score'] == best_data["best_score"] and results['accuracy'] > best_data["best_accuracy"]:
                best_data["best_accuracy"] = results['accuracy']
                best_data["achieved_date"] = datetime.now().isoformat()
    
    def _update_statistics(self, results: Dict) -> None:
        """統計情報を更新する"""
        stats = self.history_data["statistics"]
        stats["total_quizzes"] += 1
        stats["total_questions"] += results['total_questions']
        stats["total_correct"] += results['score']
    
    def get_quiz_history(self, limit: int = None) -> List[Dict]:
        """
        クイズ履歴を取得する
        
        Args:
            limit (int): 取得する履歴の最大数（最新から）
            
        Returns:
            List[Dict]: クイズ履歴のリスト
        """
        history = self.history_data["quiz_history"]
        
        # 新しい順にソート
        sorted_history = sorted(history, key=lambda x: x["timestamp"], reverse=True)
        
        if limit:
            return sorted_history[:limit]
        return sorted_history
    
    def get_best_scores(self) -> Dict:
        """ベストスコアを取得する"""
        return self.history_data["best_scores"].copy()
    
    def get_statistics(self) -> Dict:
        """統計情報を取得する"""
        stats = self.history_data["statistics"].copy()
        
        # 追加の統計を計算
        if stats["total_questions"] > 0:
            stats["overall_accuracy"] = (stats["total_correct"] / stats["total_questions"]) * 100
        else:
            stats["overall_accuracy"] = 0.0
        
        return stats
    
    def get_recent_performance(self, csv_file: str, count: int = 5) -> List[Dict]:
        """
        特定のCSVファイルの最近のパフォーマンスを取得
        
        Args:
            csv_file (str): CSVファイル名
            count (int): 取得する記録数
            
        Returns:
            List[Dict]: 最近のパフォーマンス記録
        """
        file_key = os.path.basename(csv_file)
        
        # 該当するCSVファイルの履歴を抽出
        filtered_history = [
            record for record in self.history_data["quiz_history"]
            if record["csv_file"] == file_key
        ]
        
        # 新しい順にソートして指定数を返す
        sorted_history = sorted(filtered_history, key=lambda x: x["timestamp"], reverse=True)
        return sorted_history[:count]
    
    def clear_history(self) -> None:
        """履歴をクリアする"""
        self.history_data = {
            "version": "1.0",
            "created": datetime.now().isoformat(),
            "quiz_history": [],
            "best_scores": {},
            "statistics": {
                "total_quizzes": 0,
                "total_questions": 0,
                "total_correct": 0
            }
        }
        self._save_history()
    
    def export_history(self, export_file: str) -> None:
        """
        履歴を別のファイルにエクスポート
        
        Args:
            export_file (str): エクスポート先ファイル名
        """
        try:
            with open(export_file, 'w', encoding='utf-8') as f:
                json.dump(self.history_data, f, ensure_ascii=False, indent=2)
        except IOError as e:
            raise QuizDataError(f"履歴のエクスポートに失敗しました: {str(e)}")
    
    def get_wrong_questions_summary(self, csv_file: str = None) -> Dict:
        """
        間違えた問題の集計を取得
        
        Args:
            csv_file (str): 特定のCSVファイルに限定する場合
            
        Returns:
            Dict: 間違えた問題の集計データ
        """
        wrong_questions = {}
        
        for record in self.history_data["quiz_history"]:
            # CSVファイル指定がある場合はフィルタリング
            if csv_file and record["csv_file"] != os.path.basename(csv_file):
                continue
            
            for wrong in record["wrong_questions"]:
                question_text = wrong["question"]
                if question_text not in wrong_questions:
                    wrong_questions[question_text] = {
                        "count": 0,
                        "correct_answer": wrong["correct_option"],
                        "common_mistakes": {}
                    }
                
                wrong_questions[question_text]["count"] += 1
                
                # よくある間違いを記録
                mistake = wrong["selected_option"]
                if mistake not in wrong_questions[question_text]["common_mistakes"]:
                    wrong_questions[question_text]["common_mistakes"][mistake] = 0
                wrong_questions[question_text]["common_mistakes"][mistake] += 1
        
        # 間違い回数でソート
        sorted_wrong = dict(sorted(wrong_questions.items(), key=lambda x: x[1]["count"], reverse=True))
        
        return sorted_wrong