#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
4択クイズアプリ - メインエントリーポイント (Week 3対応)
循環インポート問題を解決
"""

import sys
import os
import traceback
from enhanced_exceptions import EnhancedQuizAppError, ConfigurationError
from logger import setup_app_logging, log_app_start, log_app_end, log_error, log_user_action
# Week 3 追加
from settings import create_default_env_file, get_settings_manager


def main():
    """メイン関数"""
    try:
        # ログシステム初期化
        quiz_logger = setup_app_logging()
        
        # Week 3: 設定システム初期化
        print("設定を読み込み中...")
        settings_manager = get_settings_manager()
        settings = settings_manager.get_settings()
        
        # .envファイルがない場合は作成を提案
        if not os.path.exists(".env"):
            print("設定ファイル(.env)が見つかりません。")
            response = input("デフォルト設定ファイルを作成しますか？ (y/n): ")
            if response.lower() in ['y', 'yes', 'はい']:
                create_default_env_file()
                print("設定ファイルが作成されました。次回起動時から有効になります。")
        
        print("4択クイズアプリを開始します...")
        
        # 設定の妥当性チェック
        validation = settings_manager.validate_settings()
        if not validation["is_valid"]:
            print("⚠️  設定に問題があります:")
            for error in validation["errors"]:
                print(f"   エラー: {error}")
            return
        
        if validation["warnings"]:
            print("ℹ️  設定に関する注意点:")
            for warning in validation["warnings"]:
                print(f"   警告: {warning}")
        
        # コマンドライン引数からCSVファイルパスを取得
        csv_file = None
        if len(sys.argv) > 1:
            csv_file = sys.argv[1]
            if not os.path.exists(csv_file):
                print(f"エラー: ファイル '{csv_file}' が見つかりません")
                from enhanced_exceptions import FileNotFoundError
                log_error(FileNotFoundError(f"File not found: {csv_file}"), "command_line_arg")
                sys.exit(1)
            print(f"CSVファイル: {csv_file}")
        else:
            # 新しい設定システムからデフォルトファイルを取得
            csv_file = settings.default_csv_file
            print(f"デフォルトCSVファイルを使用: {csv_file}")
        
        # アプリ開始ログ
        log_app_start(csv_file)
        
        print("コントローラーを作成中...")
        # QuizControllerは循環インポートを避けるためここでインポート
        from quiz_controller import QuizController
        controller = QuizController(csv_file)
        print("コントローラー作成完了")
        
        print("アプリケーション開始...")
        controller.run()
        print("アプリケーション正常終了")
        
    except ConfigurationError as e:
        print(f"設定エラー: {e.get_user_message()}")
        print(f"エラーコード: {e.error_code}")
        sys.exit(1)
    except EnhancedQuizAppError as e:
        print(f"アプリエラー: {e.get_user_message()}")
        print(f"エラーコード: {e.error_code}")
        sys.exit(1)
    except KeyboardInterrupt:
        print("\nアプリケーションが中断されました")
        log_user_action("app_interrupted", "KeyboardInterrupt")
        sys.exit(0)
    except Exception as e:
        print(f"予期しないエラーが発生しました: {e}")
        print(f"エラータイプ: {type(e)}")
        log_error(e, "unexpected_error")
        traceback.print_exc()
        sys.exit(1)
    finally:
        # アプリ終了ログ
        log_app_end()
    
    print("アプリケーションを終了しました")


if __name__ == "__main__":
    main()