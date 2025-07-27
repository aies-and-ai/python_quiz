"""
クイズ結果の保存・履歴管理を行うクラス
JSONファイル + SQLite データベースのハイブリッド対応
"""

import json
import os
from datetime import datetime
from typing import Dict, List, Optional
from exceptions import QuizDataError

# データベース統合用（オプション）
try:
    from database import get_db_session, QuizDatabaseManager
    DATABASE_AVAILABLE = True
except ImportError:
    DATABASE_AVAILABLE = False


class QuizDataManager:
    """クイズデータの保存・読み込みを管理するクラス（JSONファイル + SQLite対応）"""
    
    def __init__(self, data_file: str = "quiz_history.json", use_database: bool = True, database_url: str = None):
        """
        初期化
        
        Args:
            data_file (str): データ保存用JSONファイルのパス
            use_database (bool): データベースを使用するかどうか
            database_url (str): データベースURL（オプション）
        """
        self.data_file = data_file
        self.use_database = use_database and DATABASE_AVAILABLE
        self.database_url = database_url
        
        # データベース管理インスタンス
        self.db_manager = None
        if self.use_database:
            try:
                self.db_manager = QuizDatabaseManager(database_url)
            except Exception as e:
                print(f"Database initialization failed, falling back to JSON: {e}")
                self.use_database = False
        
        # JSONファイル用の履歴データ（後方互換性のため維持）
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
        クイズ結果を保存する（データベース優先、JSONファイルは後方互換性用）
        
        Args:
            results (Dict): クイズの最終結果
            csv_file (str): 使用したCSVファイル名
        """
        # データベースに保存（優先）
        if self.use_database and self.db_manager:
            try:
                # セッションIDを生成（結果にない場合）
                session_id = results.get('session_id')
                if not session_id:
                    import uuid
                    session_id = str(uuid.uuid4())
                
                success = self.db_manager.save_quiz_result(results, session_id)
                if success:
                    # データベース保存成功時はJSONファイルは更新しない
                    # （重複を避けるため）
                    return
            except Exception as e:
                print(f"Database save failed, falling back to JSON: {e}")
        
        # JSONファイルに保存（フォールバック or データベース未使用時）
        self._save_to_json_file(results, csv_file)
    
    def _save_to_json_file(self, results: Dict, csv_file: str) -> None:
        """JSONファイルに保存（従来の方式）"""
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
        クイズ履歴を取得する（データベース優先）
        
        Args:
            limit (int): 取得する履歴の最大数（最新から）
            
        Returns:
            List[Dict]: クイズ履歴のリスト
        """
        # データベースから取得（優先）
        if self.use_database and self.db_manager:
            try:
                return self.db_manager.get_quiz_history(limit or 10)
            except Exception as e:
                print(f"Database history retrieval failed, falling back to JSON: {e}")
        
        # JSONファイルから取得（フォールバック）
        history = self.history_data["quiz_history"]
        
        # 新しい順にソート
        sorted_history = sorted(history, key=lambda x: x["timestamp"], reverse=True)
        
        if limit:
            return sorted_history[:limit]
        return sorted_history
    
    def get_best_scores(self) -> Dict:
        """ベストスコアを取得する（データベース優先）"""
        # データベースから取得（優先）
        if self.use_database and self.db_manager:
            try:
                return self.db_manager.get_best_scores()
            except Exception as e:
                print(f"Database best scores retrieval failed, falling back to JSON: {e}")
        
        # JSONファイルから取得（フォールバック）
        return self.history_data["best_scores"].copy()
    
    def get_statistics(self) -> Dict:
        """統計情報を取得する（データベース優先）"""
        # データベースから取得（優先）
        if self.use_database and self.db_manager:
            try:
                return self.db_manager.get_statistics()
            except Exception as e:
                print(f"Database statistics retrieval failed, falling back to JSON: {e}")
        
        # JSONファイルから取得（フォールバック）
        stats = self.history_data["statistics"].copy()
        
        # 追加の統計を計算
        if stats["total_questions"] > 0:
            stats["overall_accuracy"] = (stats["total_correct"] / stats["total_questions"]) * 100
        else:
            stats["overall_accuracy"] = 0.0
        
        return stats
    
    def get_recent_performance(self, csv_file: str, count: int = 5) -> List[Dict]:
        """
        特定のCSVファイルの最近のパフォーマンスを取得（データベース優先）
        
        Args:
            csv_file (str): CSVファイル名
            count (int): 取得する記録数
            
        Returns:
            List[Dict]: 最近のパフォーマンス記録
        """
        # データベースから取得（優先）
        if self.use_database and self.db_manager:
            try:
                return self.db_manager.get_quiz_history(limit=count, csv_file=os.path.basename(csv_file))
            except Exception as e:
                print(f"Database recent performance retrieval failed, falling back to JSON: {e}")
        
        # JSONファイルから取得（フォールバック）
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
        """履歴をクリアする（JSONとデータベース両方）"""
        # データベースの履歴をクリア
        if self.use_database and self.db_manager:
            try:
                # データベースの履歴テーブルをクリア
                with get_db_session(self.database_url) as session:
                    from database.models import DatabaseUserHistory
                    session.query(DatabaseUserHistory).delete()
                    session.commit()
                print("Database history cleared successfully")
            except Exception as e:
                print(f"Failed to clear database history: {e}")
        
        # JSONファイルの履歴をクリア
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
        間違えた問題の集計を取得（データベース優先）
        
        Args:
            csv_file (str): 特定のCSVファイルに限定する場合
            
        Returns:
            Dict: 間違えた問題の集計データ
        """
        # データベースから取得（優先）
        if self.use_database and self.db_manager:
            try:
                return self.db_manager.get_wrong_questions_summary(csv_file)
            except Exception as e:
                print(f"Database wrong questions summary retrieval failed, falling back to JSON: {e}")
        
        # JSONファイルから取得（フォールバック）
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
    
    # === データベース関連の新機能 ===
    
    def is_database_available(self) -> bool:
        """データベースが利用可能かチェック"""
        return self.use_database and self.db_manager is not None
    
    def get_database_info(self) -> Dict:
        """データベース情報を取得"""
        if not self.is_database_available():
            return {"error": "Database not available"}
        
        try:
            return self.db_manager.get_database_info()
        except Exception as e:
            return {"error": str(e)}
    
    def migrate_json_to_database(self) -> Dict:
        """JSONファイルのデータをデータベースに移行"""
        if not self.is_database_available():
            return {"error": "Database not available", "migrated": 0}
        
        try:
            from database.migrator import QuizDataMigrator
            migrator = QuizDataMigrator(self.database_url)
            
            result = migrator.migrate_json_history_to_database(self.data_file)
            
            return {
                "success": result.success,
                "migrated": result.history_records_migrated,
                "errors": result.errors,
                "warnings": result.warnings
            }
        except Exception as e:
            return {"error": str(e), "migrated": 0}
    
    def force_json_mode(self) -> None:
        """強制的にJSONモードに切り替え（デバッグ用）"""
        self.use_database = False
        self.db_manager = None
    
    def force_database_mode(self, database_url: str = None) -> bool:
        """強制的にデータベースモードに切り替え"""
        if not DATABASE_AVAILABLE:
            return False
        
        try:
            self.db_manager = QuizDatabaseManager(database_url or self.database_url)
            self.use_database = True
            return True
        except Exception as e:
            print(f"Failed to switch to database mode: {e}")
            return False
    
    def get_storage_mode(self) -> str:
        """現在のストレージモードを取得"""
        if self.use_database:
            return "database"
        else:
            return "json_file"