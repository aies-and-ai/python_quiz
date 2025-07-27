# csv_reader.py
"""
CSVファイルから4択クイズデータを読み込むクラス
Week 4: pydanticモデルとデータバリデーション強化版 + DB統合
"""

import csv
import os
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path
from enhanced_exceptions import CSVFormatError, FileNotFoundError, wrap_exception
from quiz_schema import QuizSchema
from models import QuestionModel, DataQualityReport
from logger import get_logger

# データベース統合用（オプション）
try:
    from database import get_db_session, DatabaseQuestion
    DATABASE_AVAILABLE = True
except ImportError:
    DATABASE_AVAILABLE = False


class QuizCSVReader:
    """CSVファイルからクイズデータを読み込むクラス（Week 4強化版 + DB統合）"""
    
    def __init__(self, file_path: str, auto_import_to_db: bool = False, database_url: str = None):
        """
        初期化
        
        Args:
            file_path (str): CSVファイルのパス
            auto_import_to_db (bool): 読み込み時に自動でDBにインポートするか
            database_url (str): データベースURL（auto_import_to_dbがTrueの時のみ使用）
        """
        self.logger = get_logger()
        self.file_path = file_path
        self.auto_import_to_db = auto_import_to_db and DATABASE_AVAILABLE
        self.database_url = database_url
        self.validation_result = None
        self.detected_headers = []
        self.data_quality_report: Optional[DataQualityReport] = None
        
        # データベース統合関連
        self.db_import_result = None
        self.imported_question_ids = []
        
        self.logger.debug(f"QuizCSVReader initializing with file: {file_path}")
        if self.auto_import_to_db:
            self.logger.debug("Auto-import to database enabled")
        
        self._validate_file()
        self._analyze_csv_structure()
    
    def _validate_file(self) -> None:
        """ファイルの存在をチェック（強化版）"""
        if not os.path.exists(self.file_path):
            raise FileNotFoundError(
                message=f"CSV file not found: {self.file_path}",
                file_path=self.file_path,
                user_message=f"CSVファイル「{os.path.basename(self.file_path)}」が見つかりません。"
            )
        
        # ファイルサイズチェック
        try:
            file_size = os.path.getsize(self.file_path)
            if file_size == 0:
                raise CSVFormatError(
                    message=f"CSV file is empty: {self.file_path}",
                    file_path=self.file_path,
                    user_message="CSVファイルが空です。問題データが含まれているかご確認ください。"
                )
            
            # 大きすぎるファイルの警告（50MB以上）
            max_size = 50 * 1024 * 1024  # 50MB
            if file_size > max_size:
                self.logger.warning(f"Large CSV file detected: {file_size / 1024 / 1024:.1f}MB")
                
        except OSError as e:
            raise CSVFormatError(
                message=f"Cannot access file: {self.file_path} - {str(e)}",
                file_path=self.file_path,
                original_error=e,
                user_message="ファイルにアクセスできません。ファイルが使用中でないかご確認ください。"
            )
    
    def _analyze_csv_structure(self) -> None:
        """CSVファイルの構造を分析（強化版）"""
        try:
            with open(self.file_path, 'r', encoding='utf-8') as file:
                # まず最初の数行を読んでエンコーディングと形式を確認
                first_lines = []
                for i, line in enumerate(file):
                    first_lines.append(line.strip())
                    if i >= 2:  # 最初の3行で判断
                        break
                
                if not first_lines:
                    raise CSVFormatError(
                        message="CSV file appears to be empty",
                        file_path=self.file_path,
                        user_message="CSVファイルにデータが含まれていません。"
                    )
                
                # ファイルポインタを先頭に戻す
                file.seek(0)
                reader = csv.reader(file)
                self.detected_headers = next(reader)
                
                if not self.detected_headers:
                    raise CSVFormatError(
                        message="No headers found in CSV file",
                        file_path=self.file_path,
                        line_number=1,
                        user_message="CSVファイルのヘッダー行が見つかりません。"
                    )
            
            # スキーマのバリデーション
            self.validation_result = QuizSchema.validate_csv_headers(self.detected_headers)
            
            if not self.validation_result["is_valid"]:
                missing_fields = self.validation_result.get('missing_required', [])
                raise CSVFormatError(
                    message=f"CSV schema validation failed: missing {missing_fields}",
                    file_path=self.file_path,
                    user_message=f"CSVファイルに必要な列が不足しています: {', '.join(missing_fields)}",
                    details={
                        'missing_fields': missing_fields,
                        'detected_headers': self.detected_headers
                    }
                )
                
        except UnicodeDecodeError as e:
            raise CSVFormatError(
                message=f"File encoding error: {str(e)}",
                file_path=self.file_path,
                original_error=e,
                user_message="ファイルの文字エンコーディングが正しくありません。UTF-8形式で保存し直してください。"
            )
        except StopIteration:
            raise CSVFormatError(
                message="CSV file appears to have no data rows",
                file_path=self.file_path,
                user_message="CSVファイルにヘッダー行以外のデータが見つかりません。"
            )
        except Exception as e:
            if isinstance(e, CSVFormatError):
                raise
            # 予期しないエラーをラップ
            raise wrap_exception(e, "csv_structure_analysis")
    
    def load_questions(self) -> List[Dict]:
        """
        CSVファイルから問題データを読み込む（Week 4強化版 + DB統合）
        
        Returns:
            List[Dict]: バリデーション済み問題データのリスト
        """
        questions = []
        validation_errors = []
        warnings = []
        
        try:
            self.logger.debug(f"Loading questions from {self.file_path}")
            with open(self.file_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                
                for row_num, row in enumerate(reader, start=2):  # ヘッダー行の次から
                    try:
                        # pydanticモデルでバリデーション
                        question_model = QuestionModel.from_csv_dict(row, row_num)
                        
                        # 従来形式の辞書に変換して追加
                        question_dict = question_model.to_legacy_dict()
                        questions.append(question_dict)
                        
                        # 品質チェック
                        self._check_question_quality(question_model, row_num, warnings)
                        
                    except Exception as e:
                        if isinstance(e, CSVFormatError):
                            validation_errors.append({
                                'row': row_num,
                                'error': str(e),
                                'type': 'validation_error'
                            })
                            self.logger.error(f"Validation error at row {row_num}: {str(e)}")
                        else:
                            validation_errors.append({
                                'row': row_num,
                                'error': f"Unexpected error: {str(e)}",
                                'type': 'unexpected_error'
                            })
                            self.logger.error(f"Unexpected error at row {row_num}: {str(e)}")
            
            # データ品質レポートを生成
            self._generate_quality_report(questions, validation_errors, warnings)
            
            # 自動データベースインポート
            if self.auto_import_to_db and questions:
                self._auto_import_to_database(questions)
            
            self.logger.info(f"Successfully loaded {len(questions)} questions from {self.file_path}")
            
            # エラーがある場合の処理
            if validation_errors:
                error_count = len(validation_errors)
                if error_count > len(questions):  # エラーが多すぎる場合
                    raise CSVFormatError(
                        message=f"Too many validation errors: {error_count} errors, {len(questions)} valid questions",
                        file_path=self.file_path,
                        user_message=f"CSVファイルに多数のエラーがあります（{error_count}個のエラー）。データの形式をご確認ください。"
                    )
                else:
                    # 警告として記録
                    self.logger.warning(f"CSV loaded with {error_count} validation errors")
                        
        except UnicodeDecodeError as e:
            raise CSVFormatError(
                message=f"File encoding error during load: {str(e)}",
                file_path=self.file_path,
                original_error=e,
                user_message="ファイルの文字エンコーディングエラーです。UTF-8形式で保存し直してください。"
            )
        except Exception as e:
            if isinstance(e, (CSVFormatError, FileNotFoundError)):
                raise
            raise wrap_exception(e, "csv_question_loading")
        
        if not questions:
            raise CSVFormatError(
                message="No valid questions found in CSV file",
                file_path=self.file_path,
                user_message="CSVファイルに有効な問題データが見つかりませんでした。データの内容をご確認ください。"
            )
        
        return questions
    
    def _auto_import_to_database(self, questions: List[Dict]) -> None:
        """
        問題データを自動的にデータベースにインポート
        
        Args:
            questions: 問題データリスト
        """
        if not DATABASE_AVAILABLE:
            self.logger.warning("Database not available for auto-import")
            return
        
        try:
            from pathlib import Path
            csv_filename = Path(self.file_path).name
            imported_count = 0
            duplicate_count = 0
            
            with get_db_session(self.database_url) as session:
                for question_dict in questions:
                    # 重複チェック
                    existing = session.query(DatabaseQuestion).filter(
                        DatabaseQuestion.question == question_dict['question'],
                        DatabaseQuestion.csv_source_file == csv_filename
                    ).first()
                    
                    if existing:
                        duplicate_count += 1
                        self.imported_question_ids.append(existing.id)
                        continue
                    
                    # 新規作成
                    db_question = DatabaseQuestion.from_legacy_dict(
                        question_dict,
                        csv_filename
                    )
                    
                    session.add(db_question)
                    session.flush()  # IDを取得するため
                    
                    self.imported_question_ids.append(db_question.id)
                    imported_count += 1
                
                session.commit()
            
            self.db_import_result = {
                'imported_count': imported_count,
                'duplicate_count': duplicate_count,
                'total_questions': len(questions),
                'csv_filename': csv_filename
            }
            
            self.logger.info(f"Auto-imported {imported_count} questions to database ({duplicate_count} duplicates skipped)")
            
        except Exception as e:
            self.logger.error(f"Auto-import to database failed: {e}")
            self.db_import_result = {
                'error': str(e),
                'imported_count': 0
            }
    
    def import_to_database(self, database_url: str = None, overwrite: bool = False) -> Dict[str, Any]:
        """
        現在読み込み済みの問題データをデータベースにインポート
        
        Args:
            database_url: データベースURL
            overwrite: 既存データを上書きするか
            
        Returns:
            Dict: インポート結果
        """
        if not DATABASE_AVAILABLE:
            return {'error': 'Database not available', 'imported_count': 0}
        
        try:
            # 問題データを再取得（まだ読み込んでいない場合）
            if not hasattr(self, '_cached_questions'):
                self._cached_questions = self.load_questions()
            
            if not self._cached_questions:
                return {'error': 'No questions to import', 'imported_count': 0}
            
            from pathlib import Path
            csv_filename = Path(self.file_path).name
            imported_count = 0
            duplicate_count = 0
            
            with get_db_session(database_url or self.database_url) as session:
                for question_dict in self._cached_questions:
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
                    imported_count += 1
                
                session.commit()
            
            result = {
                'imported_count': imported_count,
                'duplicate_count': duplicate_count,
                'total_questions': len(self._cached_questions),
                'csv_filename': csv_filename,
                'overwrite_mode': overwrite
            }
            
            self.logger.info(f"Manual import completed: {imported_count} questions imported")
            
            return result
            
        except Exception as e:
            self.logger.error(f"Manual import failed: {e}")
            return {'error': str(e), 'imported_count': 0}
    
    def _check_question_quality(self, question: QuestionModel, row_num: int, warnings: List[Dict]) -> None:
        """個別問題の品質をチェック"""
        
        # 問題文の長さチェック
        if len(question.question) < 10:
            warnings.append({
                'row': row_num,
                'type': 'short_question',
                'message': f"問題文が短すぎる可能性があります（{len(question.question)}文字）"
            })
        
        if len(question.question) > 500:
            warnings.append({
                'row': row_num,
                'type': 'long_question',
                'message': f"問題文が長すぎる可能性があります（{len(question.question)}文字）"
            })
        
        # 選択肢の長さのバランスチェック
        option_lengths = [len(opt) for opt in question.options]
        max_length = max(option_lengths)
        min_length = min(option_lengths)
        
        if max_length > min_length * 3:  # 最長が最短の3倍以上
            warnings.append({
                'row': row_num,
                'type': 'unbalanced_options',
                'message': f"選択肢の長さにばらつきがあります（最短{min_length}文字、最長{max_length}文字）"
            })
        
        # 選択肢の内容チェック
        for i, option in enumerate(question.options):
            # 明らかに不適切な選択肢
            if option.lower() in ['test', 'テスト', 'dummy', 'sample', 'サンプル']:
                warnings.append({
                    'row': row_num,
                    'type': 'placeholder_option',
                    'message': f"選択肢{i+1}にプレースホルダーらしき文言があります: '{option}'"
                })
        
        # 解説の有無チェック
        if not question.explanation and not any(question.option_explanations):
            warnings.append({
                'row': row_num,
                'type': 'no_explanation',
                'message': "解説が設定されていません"
            })
        
        # メタデータの充実度チェック
        metadata_score = 0
        if question.title: metadata_score += 1
        if question.genre: metadata_score += 1
        if question.difficulty: metadata_score += 1
        if question.tags: metadata_score += 1
        if question.source: metadata_score += 1
        
        if metadata_score == 0:
            warnings.append({
                'row': row_num,
                'type': 'no_metadata',
                'message': "メタデータ（タイトル、ジャンル、難易度等）が設定されていません"
            })
    
    def _generate_quality_report(self, questions: List[Dict], errors: List[Dict], warnings: List[Dict]) -> None:
        """データ品質レポートを生成"""
        total_questions = len(questions) + len(errors)
        valid_questions = len(questions)
        
        # 各種カウント
        has_explanations_count = 0
        has_option_explanations_count = 0
        has_metadata_count = 0
        
        for q in questions:
            # 解説の有無
            if q.get('explanation') or any(q.get('option_explanations', [])):
                has_explanations_count += 1
            
            # 選択肢解説の有無
            if any(q.get('option_explanations', [])):
                has_option_explanations_count += 1
            
            # メタデータの有無
            extra_data = q.get('extra_data', {})
            if extra_data or any(key in q for key in ['title', 'genre', 'difficulty', 'tags', 'source']):
                has_metadata_count += 1
        
        # 品質スコアの計算
        quality_score = self._calculate_quality_score(
            valid_questions, total_questions, has_explanations_count,
            has_metadata_count, len(errors), len(warnings)
        )
        
        self.data_quality_report = DataQualityReport(
            file_path=self.file_path,
            total_questions=total_questions,
            valid_questions=valid_questions,
            has_explanations_count=has_explanations_count,
            has_option_explanations_count=has_option_explanations_count,
            has_metadata_count=has_metadata_count,
            validation_errors=errors,
            warnings=warnings,
            quality_score=quality_score
        )
    
    def _calculate_quality_score(self, valid: int, total: int, explanations: int, 
                               metadata: int, errors: int, warnings: int) -> float:
        """品質スコアを計算"""
        if total == 0:
            return 0.0
        
        # ベーススコア（有効データの割合）
        base_score = (valid / total) * 100
        
        # ボーナススコア
        explanation_bonus = (explanations / valid * 20) if valid > 0 else 0
        metadata_bonus = (metadata / valid * 10) if valid > 0 else 0
        
        # ペナルティ
        error_penalty = min(errors * 5, 30)  # エラー1個につき5点減点、最大30点
        warning_penalty = min(warnings * 1, 20)  # 警告1個につき1点減点、最大20点
        
        final_score = base_score + explanation_bonus + metadata_bonus - error_penalty - warning_penalty
        
        return max(0.0, min(100.0, final_score))
    
    def get_question_count(self) -> int:
        """問題数を取得"""
        try:
            questions = self.load_questions()
            return len(questions)
        except Exception:
            return 0
    
    def get_schema_info(self) -> Dict[str, Any]:
        """使用中のスキーマ情報を取得"""
        if not self.validation_result:
            return {}
        
        return {
            "schema_info": self.validation_result["schema_info"],
            "available_fields": self.validation_result["available_fields"],
            "display_fields": self.validation_result["display_fields"],
            "unknown_fields": self.validation_result["unknown_fields"]
        }
    
    def get_data_quality_report(self) -> Optional[DataQualityReport]:
        """データ品質レポートを取得"""
        return self.data_quality_report
    
    def get_field_label(self, field_name: str) -> str:
        """フィールド名の日本語ラベルを取得"""
        return QuizSchema.get_field_label(field_name)
    
    def validate_format(self) -> bool:
        """CSVファイルの形式が正しいかチェック"""
        try:
            self.load_questions()
            return True
        except Exception:
            return False
    
    def is_database_available(self) -> bool:
        """データベース機能が利用可能かチェック"""
        return DATABASE_AVAILABLE
    
    def can_auto_import(self) -> bool:
        """自動インポートが有効かチェック"""
        return self.auto_import_to_db and DATABASE_AVAILABLE
    
    def get_database_import_result(self) -> Optional[Dict[str, Any]]:
        """データベースインポート結果を取得"""
        return self.db_import_result
    
    def get_imported_question_ids(self) -> List[int]:
        """インポートされた問題のIDリストを取得"""
        return self.imported_question_ids.copy() if self.imported_question_ids else []
    
    def get_sample_extra_data(self) -> Dict[str, str]:
        """サンプルの追加データを取得（UI表示用）"""
        if not self.validation_result:
            return {}
        
        sample_data = {}
        display_fields = self.validation_result.get("display_fields", [])
        
        for field in display_fields:
            label = self.get_field_label(field)
            sample_data[field] = label
        
        return sample_data
    
    def export_quality_report(self, output_path: str) -> None:
        """品質レポートをファイルに出力"""
        if not self.data_quality_report:
            self.logger.warning("Quality report not available")
            return
        
        try:
            report = self.data_quality_report
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write("=== データ品質レポート ===\n")
                f.write(f"ファイル: {report.file_path}\n")
                f.write(f"総問題数: {report.total_questions}\n")
                f.write(f"有効問題数: {report.valid_questions}\n")
                f.write(f"成功率: {report.get_success_rate():.1f}%\n")
                f.write(f"品質スコア: {report.quality_score:.1f}/100\n")
                f.write(f"解説カバー率: {report.get_explanation_coverage():.1f}%\n")
                f.write(f"メタデータカバー率: {report.get_metadata_coverage():.1f}%\n")
                f.write("\n")
                
                if report.validation_errors:
                    f.write("=== バリデーションエラー ===\n")
                    for error in report.validation_errors:
                        f.write(f"行{error['row']}: {error['error']}\n")
                    f.write("\n")
                
                if report.warnings:
                    f.write("=== 警告 ===\n")
                    for warning in report.warnings:
                        f.write(f"行{warning['row']}: {warning['message']}\n")
                    f.write("\n")
                
                f.write("=== 品質評価 ===\n")
                if report.is_high_quality():
                    f.write("✅ 高品質なデータです\n")
                else:
                    f.write("⚠️ データ品質の改善を推奨します\n")
                
                # データベースインポート結果も追記
                if self.db_import_result:
                    f.write("\n=== データベースインポート結果 ===\n")
                    if 'error' in self.db_import_result:
                        f.write(f"エラー: {self.db_import_result['error']}\n")
                    else:
                        f.write(f"インポート済み: {self.db_import_result.get('imported_count', 0)}問\n")
                        f.write(f"重複スキップ: {self.db_import_result.get('duplicate_count', 0)}問\n")
                        f.write(f"CSVファイル: {self.db_import_result.get('csv_filename', 'N/A')}\n")
            
            self.logger.info(f"Quality report exported to {output_path}")
            
        except Exception as e:
            self.logger.error(f"Failed to export quality report: {e}")
    
    def get_quality_summary(self) -> str:
        """品質サマリーを文字列で取得"""
        if not self.data_quality_report:
            return "品質レポートが生成されていません"
        
        report = self.data_quality_report
        
        summary = f"""品質スコア: {report.quality_score:.1f}/100
有効問題数: {report.valid_questions}/{report.total_questions} ({report.get_success_rate():.1f}%)
解説カバー率: {report.get_explanation_coverage():.1f}%
エラー数: {len(report.validation_errors)}
警告数: {len(report.warnings)}"""

        # データベースインポート結果も追加
        if self.db_import_result:
            if 'error' in self.db_import_result:
                summary += f"\nDBインポート: エラー"
            else:
                summary += f"\nDBインポート: {self.db_import_result.get('imported_count', 0)}問追加"
        
        return summary