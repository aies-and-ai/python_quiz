# admin.py
"""
データ管理専用アプリケーション（管理者向け・CLI専用）
Phase 1: GUI部分削除、CLI機能のみ保持

このファイルの配置場所: プロジェクトルート/admin.py
"""

import sys
import os
import argparse
from pathlib import Path

from app.config import get_settings
from app.core.service_factory import initialize_services, shutdown_services, get_csv_importer, get_database_service
from utils.logger import get_logger, set_log_level


class AdminCLI:
    """管理者向けコマンドライン機能"""
    
    def __init__(self):
        self.logger = get_logger()
        self.csv_importer = get_csv_importer()
        self.db_service = get_database_service()
    
    def import_csv(self, csv_file: str, overwrite: bool = False) -> bool:
        """
        CSVファイルをインポート
        
        Args:
            csv_file: CSVファイルパス
            overwrite: 上書きフラグ
            
        Returns:
            bool: 成功フラグ
        """
        if not os.path.exists(csv_file):
            print(f"❌ エラー: ファイルが見つかりません - {csv_file}")
            return False
        
        print(f"📂 CSVインポート開始: {csv_file}")
        
        try:
            result = self.csv_importer.import_from_csv(csv_file, overwrite)
            
            if result['success']:
                print(f"✅ インポート完了:")
                print(f"   成功: {result['imported_count']}問")
                print(f"   スキップ: {result['skipped_count']}問")
                print(f"   エラー: {result['error_count']}問")
                
                if result['warnings']:
                    print("⚠️ 警告:")
                    for warning in result['warnings']:
                        print(f"   - {warning}")
                
                return True
            else:
                print(f"❌ インポート失敗:")
                for error in result['errors'][:5]:
                    print(f"   - {error}")
                if len(result['errors']) > 5:
                    print(f"   ... 他{len(result['errors']) - 5}個のエラー")
                return False
                
        except Exception as e:
            print(f"❌ インポートエラー: {e}")
            return False
    
    def batch_import(self, directory: str, overwrite: bool = False) -> bool:
        """
        ディレクトリ内の全CSVファイルを一括インポート
        
        Args:
            directory: ディレクトリパス
            overwrite: 上書きフラグ
            
        Returns:
            bool: 成功フラグ
        """
        csv_dir = Path(directory)
        
        if not csv_dir.exists():
            print(f"❌ エラー: ディレクトリが見つかりません - {directory}")
            return False
        
        csv_files = list(csv_dir.glob("*.csv"))
        
        if not csv_files:
            print(f"❌ エラー: CSVファイルが見つかりません - {directory}")
            return False
        
        print(f"📁 一括インポート開始: {len(csv_files)}ファイル")
        
        success_count = 0
        total_imported = 0
        
        for csv_file in csv_files:
            print(f"\n--- {csv_file.name} ---")
            result = self.csv_importer.import_from_csv(str(csv_file), overwrite)
            if result['success']:
                success_count += 1
                total_imported += result['imported_count']
                print(f"✅ 成功: {result['imported_count']}問インポート")
            else:
                print(f"❌ 失敗: {len(result['errors'])}個のエラー")
        
        print(f"\n=== 一括インポート完了 ===")
        print(f"成功ファイル: {success_count}/{len(csv_files)}")
        print(f"総インポート数: {total_imported}問")
        
        return success_count > 0
    
    def show_database_info(self):
        """データベース情報を表示"""
        try:
            info = self.db_service.get_database_info()
            
            print("=== データベース情報 ===")
            print(f"問題数: {info['question_count']}問")
            print(f"セッション数: {info['session_count']}件")
            print(f"履歴数: {info['history_count']}件")
            
            if info['categories']:
                print(f"カテゴリ: {', '.join(info['categories'])}")
            else:
                print("カテゴリ: なし")
                
            if info['difficulties']:
                print(f"難易度: {', '.join(info['difficulties'])}")
            else:
                print("難易度: なし")
            
            print(f"データベース: {get_settings().database_url}")
            
        except Exception as e:
            print(f"❌ データベース情報取得エラー: {e}")
    
    def validate_csv(self, csv_file: str):
        """CSVファイルの妥当性をチェック"""
        if not os.path.exists(csv_file):
            print(f"❌ エラー: ファイルが見つかりません - {csv_file}")
            return
        
        print(f"🔍 CSVファイル検証: {csv_file}")
        
        try:
            result = self.csv_importer.validate_csv_file(csv_file)
            
            print(f"ファイル形式: {'✅ 有効' if result['is_valid'] else '❌ 無効'}")
            print(f"総行数: {result['total_rows']}")
            print(f"有効問題数: {result['valid_questions']}")
            
            if result['errors']:
                print("\nエラー:")
                for error in result['errors'][:10]:
                    print(f"  - {error}")
                if len(result['errors']) > 10:
                    print(f"  ... 他{len(result['errors']) - 10}個のエラー")
            
            if result['warnings']:
                print("\n警告:")
                for warning in result['warnings']:
                    print(f"  - {warning}")
                    
        except Exception as e:
            print(f"❌ 検証エラー: {e}")
    
    def clear_database(self):
        """データベースクリア（確認付き）"""
        print("⚠️ 警告: この操作はすべてのデータを削除します")
        confirm = input("続行しますか？ (yes/no): ")
        
        if confirm.lower() != 'yes':
            print("操作をキャンセルしました")
            return
        
        try:
            # 実装は簡素化のため省略
            print("🗑️ データベースクリア機能は未実装です")
            print("手動でquiz.dbファイルを削除してください")
        except Exception as e:
            print(f"❌ クリアエラー: {e}")


def main():
    """管理者向けメイン関数（CLI専用）"""
    parser = argparse.ArgumentParser(
        description="クイズアプリ管理者ツール（CLI専用）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  python admin.py --info                   # データベース情報を表示
  python admin.py --import file.csv        # CSVファイルをインポート
  python admin.py --batch ./data/          # フォルダを一括インポート
  python admin.py --validate file.csv      # CSVファイルを検証
        """
    )
    
    parser.add_argument("--import", dest="import_file", help="CSVファイルをインポート")
    parser.add_argument("--batch", dest="batch_dir", help="ディレクトリ内の全CSVファイルを一括インポート")
    parser.add_argument("--info", action="store_true", help="データベース情報を表示")
    parser.add_argument("--validate", dest="validate_file", help="CSVファイルの妥当性をチェック")
    parser.add_argument("--clear", action="store_true", help="データベースをクリア")
    parser.add_argument("--overwrite", action="store_true", help="既存データを上書き")
    
    args = parser.parse_args()
    
    try:
        # 設定読み込み
        settings = get_settings()
        set_log_level(settings.log_level)
        logger = get_logger()
        
        logger.info("=== クイズアプリケーション管理者ツール起動（CLI専用） ===")
        
        # サービス初期化
        initialize_services(settings.database_url)
        
        # CLI機能の実行
        cli = AdminCLI()
        
        if args.import_file:
            success = cli.import_csv(args.import_file, args.overwrite)
            sys.exit(0 if success else 1)
        
        if args.batch_dir:
            success = cli.batch_import(args.batch_dir, args.overwrite)
            sys.exit(0 if success else 1)
        
        if args.validate_file:
            cli.validate_csv(args.validate_file)
            sys.exit(0)
        
        if args.clear:
            cli.clear_database()
            sys.exit(0)
        
        if args.info:
            cli.show_database_info()
            sys.exit(0)
        
        # 引数なしの場合はヘルプ表示
        parser.print_help()
    
    except KeyboardInterrupt:
        logger.info("管理者による中断")
    except Exception as e:
        logger.error(f"管理者ツールエラー: {e}")
        print(f"❌ 管理者ツールエラー: {e}")
        
        if settings and settings.debug:
            import traceback
            traceback.print_exc()
        
        sys.exit(1)
    
    finally:
        logger.info("管理者ツール終了処理")
        shutdown_services()


if __name__ == "__main__":
    main()