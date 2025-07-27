# database/migrator.py
"""
データ移行ツール
既存のCSVファイルとJSONファイルをSQLiteデータベースに移行
"""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

from database import (
    get_db_session, 
    DatabaseQuestion, 
    DatabaseUserHistory, 
    DatabaseQuizSession,
    DatabaseStatistics
)
from csv_reader import QuizCSVReader
from enhanced_exceptions import CSVFormatError, QuizDataError, wrap_exception
from logger import get_logger


@dataclass
class MigrationResult:
    """移行結果を格納するデータクラス"""
    success: bool
    questions_migrated: int = 0
    history_records_migrated: int = 0
    sessions_migrated: int = 0
    errors: List[str] = None
    warnings: List[str] = None
    duration_seconds: float = 0.0
    
    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []


class QuizDataMigrator:
    """クイズデータ移行管理クラス"""
    
    def __init__(self, database_url: Optional[str] = None):
        """
        初期化
        
        Args:
            database_url: データベースURL（Noneの場合デフォルト使用）
        """
        self.logger = get_logger()
        self.database_url = database_url
        
    def migrate_csv_to_database(self, csv_file_path: str, overwrite: bool = False) -> MigrationResult:
        """
        CSVファイルをデータベースに移行
        
        Args:
            csv_file_path: CSVファイルのパス
            overwrite: 既存データを上書きするかどうか
            
        Returns:
            MigrationResult: 移行結果
        """
        start_time = datetime.now()
        result = MigrationResult(success=False)
        
        try:
            self.logger.info(f"Starting CSV migration: {csv_file_path}")
            
            # CSVファイルの存在確認
            if not Path(csv_file_path).exists():
                result.errors.append(f"CSV file not found: {csv_file_path}")
                return result
            
            # CSV読み込み
            try:
                csv_reader = QuizCSVReader(csv_file_path)
                questions_data = csv_reader.load_questions()
                
                if not questions_data:
                    result.warnings.append("No questions found in CSV file")
                    result.success = True
                    return result
                    
            except Exception as e:
                result.errors.append(f"Failed to read CSV: {str(e)}")
                return result
            
            # データベースに保存
            csv_filename = Path(csv_file_path).name
            migrated_count = 0
            duplicate_count = 0
            
            with get_db_session(self.database_url) as session:
                for i, question_dict in enumerate(questions_data):
                    try:
                        # 重複チェック（overwriteがFalseの場合）
                        if not overwrite:
                            existing = session.query(DatabaseQuestion).filter(
                                DatabaseQuestion.question == question_dict['question'],
                                DatabaseQuestion.csv_source_file == csv_filename
                            ).first()
                            
                            if existing:
                                duplicate_count += 1
                                continue
                        
                        # DatabaseQuestionに変換
                        db_question = DatabaseQuestion.from_legacy_dict(
                            question_dict, 
                            csv_filename
                        )
                        
                        session.add(db_question)
                        migrated_count += 1
                        
                        # 100件ごとにコミット（大量データ対応）
                        if migrated_count % 100 == 0:
                            session.commit()
                            self.logger.debug(f"Migrated {migrated_count} questions...")
                    
                    except Exception as e:
                        result.warnings.append(f"Failed to migrate question {i+1}: {str(e)}")
                        continue
                
                # 最終コミット
                session.commit()
            
            result.questions_migrated = migrated_count
            result.success = True
            
            if duplicate_count > 0:
                result.warnings.append(f"Skipped {duplicate_count} duplicate questions")
            
            self.logger.info(f"CSV migration completed: {migrated_count} questions migrated")
            
        except Exception as e:
            self.logger.error(f"CSV migration failed: {e}")
            result.errors.append(f"Migration failed: {str(e)}")
        
        finally:
            end_time = datetime.now()
            result.duration_seconds = (end_time - start_time).total_seconds()
        
        return result
    
    def migrate_json_history_to_database(self, json_file_path: str, overwrite: bool = False) -> MigrationResult:
        """
        JSONファイルの履歴データをデータベースに移行
        
        Args:
            json_file_path: JSONファイルのパス（data_manager.pyが作成したファイル）
            overwrite: 既存データを上書きするかどうか
            
        Returns:
            MigrationResult: 移行結果
        """
        start_time = datetime.now()
        result = MigrationResult(success=False)
        
        try:
            self.logger.info(f"Starting JSON history migration: {json_file_path}")
            
            # JSONファイルの存在確認
            if not Path(json_file_path).exists():
                result.errors.append(f"JSON file not found: {json_file_path}")
                return result
            
            # JSON読み込み
            try:
                with open(json_file_path, 'r', encoding='utf-8') as f:
                    history_data = json.load(f)
                    
                if not isinstance(history_data, dict):
                    result.errors.append("Invalid JSON format")
                    return result
                    
                quiz_history = history_data.get('quiz_history', [])
                
                if not quiz_history:
                    result.warnings.append("No quiz history found in JSON file")
                    result.success = True
                    return result
                    
            except json.JSONDecodeError as e:
                result.errors.append(f"Failed to parse JSON: {str(e)}")
                return result
            except Exception as e:
                result.errors.append(f"Failed to read JSON file: {str(e)}")
                return result
            
            # データベースに保存
            migrated_count = 0
            duplicate_count = 0
            
            with get_db_session(self.database_url) as session:
                for i, history_record in enumerate(quiz_history):
                    try:
                        # データの妥当性チェック
                        required_fields = ['timestamp', 'csv_file', 'total_questions', 'score', 'accuracy']
                        if not all(field in history_record for field in required_fields):
                            result.warnings.append(f"Invalid history record {i+1}: missing required fields")
                            continue
                        
                        # 重複チェック（overwriteがFalseの場合）
                        if not overwrite:
                            existing = session.query(DatabaseUserHistory).filter(
                                DatabaseUserHistory.timestamp == datetime.fromisoformat(history_record['timestamp'].replace('Z', '+00:00')),
                                DatabaseUserHistory.csv_file == history_record['csv_file'],
                                DatabaseUserHistory.score == history_record['score']
                            ).first()
                            
                            if existing:
                                duplicate_count += 1
                                continue
                        
                        # セッションIDを生成（既存の履歴にはないため）
                        import uuid
                        session_id = str(uuid.uuid4())
                        
                        # DatabaseUserHistoryに変換
                        db_history = DatabaseUserHistory(
                            session_id=session_id,
                            csv_file=history_record['csv_file'],
                            total_questions=history_record['total_questions'],
                            score=history_record['score'],
                            accuracy=history_record['accuracy'],
                            wrong_count=history_record.get('wrong_count', 0),
                            timestamp=datetime.fromisoformat(history_record['timestamp'].replace('Z', '+00:00')),
                            duration_seconds=history_record.get('duration_seconds'),
                            wrong_questions_data=history_record.get('wrong_questions', []),
                            performance_data={}
                        )
                        
                        session.add(db_history)
                        migrated_count += 1
                        
                        # 100件ごとにコミット
                        if migrated_count % 100 == 0:
                            session.commit()
                            self.logger.debug(f"Migrated {migrated_count} history records...")
                    
                    except Exception as e:
                        result.warnings.append(f"Failed to migrate history record {i+1}: {str(e)}")
                        continue
                
                # 最終コミット
                session.commit()
            
            result.history_records_migrated = migrated_count
            result.success = True
            
            if duplicate_count > 0:
                result.warnings.append(f"Skipped {duplicate_count} duplicate history records")
            
            self.logger.info(f"JSON history migration completed: {migrated_count} records migrated")
            
        except Exception as e:
            self.logger.error(f"JSON history migration failed: {e}")
            result.errors.append(f"Migration failed: {str(e)}")
        
        finally:
            end_time = datetime.now()
            result.duration_seconds = (end_time - start_time).total_seconds()
        
        return result
    
    def migrate_all_csv_files(self, csv_directory: str, pattern: str = "*.csv") -> MigrationResult:
        """
        指定ディレクトリ内の全CSVファイルを移行
        
        Args:
            csv_directory: CSVファイルが格納されているディレクトリ
            pattern: ファイル名パターン（デフォルト: "*.csv"）
            
        Returns:
            MigrationResult: 全体の移行結果
        """
        start_time = datetime.now()
        overall_result = MigrationResult(success=False)
        
        try:
            csv_dir = Path(csv_directory)
            
            if not csv_dir.exists():
                overall_result.errors.append(f"Directory not found: {csv_directory}")
                return overall_result
            
            # CSVファイルを検索
            csv_files = list(csv_dir.glob(pattern))
            
            if not csv_files:
                overall_result.warnings.append(f"No CSV files found in {csv_directory}")
                overall_result.success = True
                return overall_result
            
            self.logger.info(f"Found {len(csv_files)} CSV files to migrate")
            
            # 各CSVファイルを移行
            total_questions = 0
            failed_files = []
            
            for csv_file in csv_files:
                self.logger.info(f"Migrating {csv_file.name}...")
                
                result = self.migrate_csv_to_database(str(csv_file), overwrite=False)
                
                if result.success:
                    total_questions += result.questions_migrated
                    if result.warnings:
                        overall_result.warnings.extend([f"{csv_file.name}: {w}" for w in result.warnings])
                else:
                    failed_files.append(csv_file.name)
                    overall_result.errors.extend([f"{csv_file.name}: {e}" for e in result.errors])
            
            overall_result.questions_migrated = total_questions
            
            if failed_files:
                overall_result.errors.append(f"Failed to migrate {len(failed_files)} files: {', '.join(failed_files)}")
                overall_result.success = len(failed_files) < len(csv_files)  # 部分的成功も許可
            else:
                overall_result.success = True
            
            self.logger.info(f"Batch CSV migration completed: {total_questions} total questions from {len(csv_files)} files")
            
        except Exception as e:
            self.logger.error(f"Batch CSV migration failed: {e}")
            overall_result.errors.append(f"Batch migration failed: {str(e)}")
        
        finally:
            end_time = datetime.now()
            overall_result.duration_seconds = (end_time - start_time).total_seconds()
        
        return overall_result
    
    def backup_existing_data(self, backup_dir: str = "backup") -> bool:
        """
        移行前に既存データをバックアップ
        
        Args:
            backup_dir: バックアップディレクトリ
            
        Returns:
            bool: バックアップ成功かどうか
        """
        try:
            backup_path = Path(backup_dir)
            backup_path.mkdir(exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # 既存のJSONファイルをバックアップ
            json_files = ["quiz_history.json", "statistics.json"]
            backed_up_files = []
            
            for json_file in json_files:
                if Path(json_file).exists():
                    backup_file = backup_path / f"{json_file}_{timestamp}.backup"
                    import shutil
                    shutil.copy2(json_file, backup_file)
                    backed_up_files.append(str(backup_file))
            
            if backed_up_files:
                self.logger.info(f"Backed up files: {', '.join(backed_up_files)}")
            else:
                self.logger.info("No existing data files found to backup")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Backup failed: {e}")
            return False
    
    def generate_migration_report(self, results: List[MigrationResult]) -> str:
        """
        移行結果のレポートを生成
        
        Args:
            results: 移行結果のリスト
            
        Returns:
            str: 移行レポート（テキスト形式）
        """
        report_lines = []
        report_lines.append("=== データ移行レポート ===")
        report_lines.append(f"生成日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append("")
        
        total_questions = sum(r.questions_migrated for r in results)
        total_history = sum(r.history_records_migrated for r in results)
        total_errors = sum(len(r.errors) for r in results)
        total_warnings = sum(len(r.warnings) for r in results)
        
        report_lines.append("=== サマリー ===")
        report_lines.append(f"移行された問題数: {total_questions}")
        report_lines.append(f"移行された履歴数: {total_history}")
        report_lines.append(f"エラー数: {total_errors}")
        report_lines.append(f"警告数: {total_warnings}")
        report_lines.append("")
        
        for i, result in enumerate(results, 1):
            report_lines.append(f"=== 移行 {i} ===")
            report_lines.append(f"成功: {'はい' if result.success else 'いいえ'}")
            report_lines.append(f"問題数: {result.questions_migrated}")
            report_lines.append(f"履歴数: {result.history_records_migrated}")
            report_lines.append(f"所要時間: {result.duration_seconds:.2f}秒")
            
            if result.errors:
                report_lines.append("エラー:")
                for error in result.errors:
                    report_lines.append(f"  - {error}")
            
            if result.warnings:
                report_lines.append("警告:")
                for warning in result.warnings:
                    report_lines.append(f"  - {warning}")
            
            report_lines.append("")
        
        return "\n".join(report_lines)


# 便利関数
def quick_csv_migration(csv_file: str, database_url: str = None) -> MigrationResult:
    """
    CSVファイルを素早く移行する便利関数
    
    Args:
        csv_file: CSVファイルのパス
        database_url: データベースURL
        
    Returns:
        MigrationResult: 移行結果
    """
    migrator = QuizDataMigrator(database_url)
    return migrator.migrate_csv_to_database(csv_file)


def quick_history_migration(json_file: str = "quiz_history.json", database_url: str = None) -> MigrationResult:
    """
    履歴JSONファイルを素早く移行する便利関数
    
    Args:
        json_file: JSONファイルのパス
        database_url: データベースURL
        
    Returns:
        MigrationResult: 移行結果
    """
    migrator = QuizDataMigrator(database_url)
    return migrator.migrate_json_history_to_database(json_file)


if __name__ == "__main__":
    # 使用例：スタンドアロン実行
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python migrator.py <csv_file> [json_file]")
        sys.exit(1)
    
    csv_file = sys.argv[1]
    json_file = sys.argv[2] if len(sys.argv) > 2 else "quiz_history.json"
    
    migrator = QuizDataMigrator()
    
    # バックアップ
    print("Creating backup...")
    migrator.backup_existing_data()
    
    # CSV移行
    print(f"Migrating CSV: {csv_file}")
    csv_result = migrator.migrate_csv_to_database(csv_file)
    
    # JSON移行
    if Path(json_file).exists():
        print(f"Migrating JSON: {json_file}")
        json_result = migrator.migrate_json_history_to_database(json_file)
    else:
        print(f"JSON file not found, skipping: {json_file}")
        json_result = MigrationResult(success=True)
    
    # レポート生成
    report = migrator.generate_migration_report([csv_result, json_result])
    print("\n" + report)
    
    # レポートファイル出力
    with open("migration_report.txt", "w", encoding="utf-8") as f:
        f.write(report)
    
    print("\nMigration report saved to: migration_report.txt")