"""
シンプルCSVインポーター
複雑な機能を削除し、基本的なCSV→データベース変換のみ実装
"""

import csv
import os
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional

# パッケージルートをパスに追加（相対インポートエラー回避）
project_root = Path(__file__).parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# 絶対インポートで修正
from app.core.models import Question, ImportResult, create_question_from_csv_row, validate_csv_headers
from app.core.database import DatabaseService
from app.core.exceptions import CSVImportError, DatabaseError
from utils.logger import get_logger


class CSVImporter:
    """CSVファイルをデータベースにインポートするクラス"""
    
    def __init__(self, db_service: DatabaseService):
        """初期化"""
        self.db = db_service
        self.logger = get_logger()
    
    def import_from_csv(self, csv_file_path: str, overwrite: bool = False) -> Dict[str, Any]:
        """
        CSVファイルからデータベースにインポート
        
        Args:
            csv_file_path: CSVファイルのパス
            overwrite: 既存データを上書きするか
            
        Returns:
            Dict: インポート結果
        """
        result = ImportResult(success=False)
        
        try:
            self.logger.info(f"CSVインポート開始: {csv_file_path}")
            
            # ファイル存在チェック
            if not os.path.exists(csv_file_path):
                raise CSVImportError(f"ファイルが見つかりません: {csv_file_path}")
            
            # CSV読み込み
            questions = self._read_csv_file(csv_file_path, result)
            
            if not questions and result.error_count == 0:
                result.add_warning("有効な問題が見つかりませんでした")
                result.success = True
                return result.to_dict()
            
            # データベースに保存
            if questions:
                self._save_to_database(questions, csv_file_path, overwrite, result)
            
            result.success = result.error_count == 0
            
            self.logger.info(f"CSVインポート完了: {result.imported_count}問インポート")
            
        except Exception as e:
            self.logger.error(f"CSVインポートエラー: {e}")
            result.add_error(str(e))
        
        return result.to_dict()
    
    def _read_csv_file(self, csv_file_path: str, result: ImportResult) -> List[Question]:
        """CSVファイルを読み込み"""
        questions = []
        csv_filename = os.path.basename(csv_file_path)
        
        try:
            with open(csv_file_path, 'r', encoding='utf-8') as file:
                # ヘッダー確認
                reader = csv.reader(file)
                headers = next(reader)
                
                is_valid, missing_headers = validate_csv_headers(headers)
                if not is_valid:
                    raise CSVImportError(f"必要な列が不足しています: {', '.join(missing_headers)}")
                
                # データ読み込み
                file.seek(0)  # ファイルポインタを先頭に戻す
                dict_reader = csv.DictReader(file)
                
                question_id = 1
                for row_num, row in enumerate(dict_reader, start=2):
                    try:
                        # 空行スキップ
                        if not any(value.strip() for value in row.values()):
                            continue
                        
                        # 問題作成
                        question = create_question_from_csv_row(row, question_id)
                        questions.append(question)
                        question_id += 1
                        
                    except ValueError as e:
                        result.add_error(f"行{row_num}: {str(e)}")
                        continue
                    except Exception as e:
                        result.add_error(f"行{row_num}: 予期しないエラー - {str(e)}")
                        continue
        
        except UnicodeDecodeError:
            # UTF-8で読めない場合、Shift_JISを試行
            try:
                self.logger.warning("UTF-8で読み込めません。Shift_JISで再試行...")
                questions = self._read_csv_with_encoding(csv_file_path, 'shift_jis', result)
            except Exception:
                raise CSVImportError("ファイルの文字エンコーディングが対応していません（UTF-8またはShift_JIS）")
        
        except FileNotFoundError:
            raise CSVImportError(f"ファイルが見つかりません: {csv_file_path}")
        except Exception as e:
            raise CSVImportError(f"CSVファイル読み込みエラー: {str(e)}")
        
        return questions
    
    def _read_csv_with_encoding(self, csv_file_path: str, encoding: str, result: ImportResult) -> List[Question]:
        """指定エンコーディングでCSVを読み込み"""
        questions = []
        
        with open(csv_file_path, 'r', encoding=encoding) as file:
            dict_reader = csv.DictReader(file)
            
            # ヘッダー確認
            headers = dict_reader.fieldnames
            is_valid, missing_headers = validate_csv_headers(headers)
            if not is_valid:
                raise CSVImportError(f"必要な列が不足しています: {', '.join(missing_headers)}")
            
            question_id = 1
            for row_num, row in enumerate(dict_reader, start=2):
                try:
                    if not any(value.strip() for value in row.values()):
                        continue
                    
                    question = create_question_from_csv_row(row, question_id)
                    questions.append(question)
                    question_id += 1
                    
                except ValueError as e:
                    result.add_error(f"行{row_num}: {str(e)}")
                    continue
                except Exception as e:
                    result.add_error(f"行{row_num}: 予期しないエラー - {str(e)}")
                    continue
        
        return questions
    
    def _save_to_database(self, questions: List[Question], csv_file_path: str, 
                         overwrite: bool, result: ImportResult) -> None:
        """データベースに保存"""
        csv_filename = os.path.basename(csv_file_path)
        
        try:
            for question in questions:
                try:
                    # 重複チェック（overwriteがFalseの場合）
                    if not overwrite:
                        existing = self.db.find_question_by_text(question.text, csv_filename)
                        if existing:
                            result.skipped_count += 1
                            continue
                    
                    # データベースに保存
                    saved_question = self.db.save_question(question, csv_filename)
                    
                    if saved_question:
                        result.imported_count += 1
                    else:
                        result.add_error(f"問題の保存に失敗: {question.text[:50]}...")
                
                except Exception as e:
                    result.add_error(f"問題保存エラー: {str(e)}")
                    continue
        
        except Exception as e:
            raise DatabaseError(f"データベース保存エラー: {str(e)}")
    
    def validate_csv_file(self, csv_file_path: str) -> Dict[str, Any]:
        """
        CSVファイルの妥当性をチェック（保存せずに検証のみ）
        
        Args:
            csv_file_path: CSVファイルのパス
            
        Returns:
            Dict: 検証結果
        """
        result = {
            'is_valid': False,
            'total_rows': 0,
            'valid_questions': 0,
            'errors': [],
            'warnings': []
        }
        
        try:
            if not os.path.exists(csv_file_path):
                result['errors'].append(f"ファイルが見つかりません: {csv_file_path}")
                return result
            
            with open(csv_file_path, 'r', encoding='utf-8') as file:
                dict_reader = csv.DictReader(file)
                
                # ヘッダー確認
                headers = dict_reader.fieldnames
                is_valid, missing_headers = validate_csv_headers(headers)
                if not is_valid:
                    result['errors'].append(f"必要な列が不足: {', '.join(missing_headers)}")
                    return result
                
                # データ確認
                question_id = 1
                for row_num, row in enumerate(dict_reader, start=2):
                    result['total_rows'] += 1
                    
                    try:
                        if not any(value.strip() for value in row.values()):
                            continue
                        
                        create_question_from_csv_row(row, question_id)
                        result['valid_questions'] += 1
                        question_id += 1
                        
                    except ValueError as e:
                        result['errors'].append(f"行{row_num}: {str(e)}")
                    except Exception as e:
                        result['errors'].append(f"行{row_num}: {str(e)}")
            
            result['is_valid'] = len(result['errors']) == 0 and result['valid_questions'] > 0
            
            if result['valid_questions'] == 0:
                result['warnings'].append("有効な問題が見つかりませんでした")
            
        except UnicodeDecodeError:
            result['warnings'].append("UTF-8で読み込めません。Shift_JISの可能性があります")
            # Shift_JISで再試行
            try:
                return self._validate_csv_with_encoding(csv_file_path, 'shift_jis')
            except Exception:
                result['errors'].append("文字エンコーディングが対応していません")
        
        except Exception as e:
            result['errors'].append(f"ファイル読み込みエラー: {str(e)}")
        
        return result
    
    def _validate_csv_with_encoding(self, csv_file_path: str, encoding: str) -> Dict[str, Any]:
        """指定エンコーディングでCSV検証"""
        result = {
            'is_valid': False,
            'total_rows': 0,
            'valid_questions': 0,
            'errors': [],
            'warnings': [f"エンコーディング: {encoding}"]
        }
        
        try:
            with open(csv_file_path, 'r', encoding=encoding) as file:
                dict_reader = csv.DictReader(file)
                
                headers = dict_reader.fieldnames
                is_valid, missing_headers = validate_csv_headers(headers)
                if not is_valid:
                    result['errors'].append(f"必要な列が不足: {', '.join(missing_headers)}")
                    return result
                
                question_id = 1
                for row_num, row in enumerate(dict_reader, start=2):
                    result['total_rows'] += 1
                    
                    try:
                        if not any(value.strip() for value in row.values()):
                            continue
                        
                        create_question_from_csv_row(row, question_id)
                        result['valid_questions'] += 1
                        question_id += 1
                        
                    except ValueError as e:
                        result['errors'].append(f"行{row_num}: {str(e)}")
                    except Exception as e:
                        result['errors'].append(f"行{row_num}: {str(e)}")
            
            result['is_valid'] = len(result['errors']) == 0 and result['valid_questions'] > 0
            
        except Exception as e:
            result['errors'].append(f"ファイル読み込みエラー: {str(e)}")
        
        return result
    
    def get_csv_preview(self, csv_file_path: str, max_rows: int = 5) -> Dict[str, Any]:
        """
        CSVファイルのプレビューを取得
        
        Args:
            csv_file_path: CSVファイルのパス
            max_rows: 最大表示行数
            
        Returns:
            Dict: プレビュー情報
        """
        preview = {
            'headers': [],
            'sample_rows': [],
            'total_rows': 0,
            'errors': []
        }
        
        try:
            if not os.path.exists(csv_file_path):
                preview['errors'].append(f"ファイルが見つかりません: {csv_file_path}")
                return preview
            
            with open(csv_file_path, 'r', encoding='utf-8') as file:
                dict_reader = csv.DictReader(file)
                preview['headers'] = dict_reader.fieldnames or []
                
                for i, row in enumerate(dict_reader):
                    if i < max_rows:
                        preview['sample_rows'].append(dict(row))
                    preview['total_rows'] += 1
        
        except UnicodeDecodeError:
            # Shift_JISで再試行
            try:
                with open(csv_file_path, 'r', encoding='shift_jis') as file:
                    dict_reader = csv.DictReader(file)
                    preview['headers'] = dict_reader.fieldnames or []
                    
                    for i, row in enumerate(dict_reader):
                        if i < max_rows:
                            preview['sample_rows'].append(dict(row))
                        preview['total_rows'] += 1
                    
                    preview['encoding'] = 'shift_jis'
            except Exception:
                preview['errors'].append("文字エンコーディングが対応していません")
        
        except Exception as e:
            preview['errors'].append(f"ファイル読み込みエラー: {str(e)}")
        
        return preview
    
    def import_multiple_csv_files(self, csv_directory: str, 
                                 pattern: str = "*.csv") -> Dict[str, Any]:
        """
        複数のCSVファイルを一括インポート
        
        Args:
            csv_directory: CSVファイルディレクトリ
            pattern: ファイル名パターン
            
        Returns:
            Dict: 一括インポート結果
        """
        overall_result = {
            'success': True,
            'total_files': 0,
            'successful_files': 0,
            'failed_files': 0,
            'total_imported': 0,
            'file_results': [],
            'errors': []
        }
        
        try:
            csv_dir = Path(csv_directory)
            
            if not csv_dir.exists():
                overall_result['errors'].append(f"ディレクトリが見つかりません: {csv_directory}")
                overall_result['success'] = False
                return overall_result
            
            csv_files = list(csv_dir.glob(pattern))
            overall_result['total_files'] = len(csv_files)
            
            if not csv_files:
                overall_result['errors'].append(f"CSVファイルが見つかりません: {csv_directory}")
                return overall_result
            
            self.logger.info(f"{len(csv_files)}個のCSVファイルを一括インポート開始")
            
            for csv_file in csv_files:
                file_result = self.import_from_csv(str(csv_file), overwrite=False)
                file_result['filename'] = csv_file.name
                overall_result['file_results'].append(file_result)
                
                if file_result['success']:
                    overall_result['successful_files'] += 1
                    overall_result['total_imported'] += file_result.get('imported_count', 0)
                else:
                    overall_result['failed_files'] += 1
            
            overall_result['success'] = overall_result['failed_files'] == 0
            
            self.logger.info(f"一括インポート完了: {overall_result['total_imported']}問インポート")
            
        except Exception as e:
            self.logger.error(f"一括インポートエラー: {e}")
            overall_result['errors'].append(str(e))
            overall_result['success'] = False
        
        return overall_result