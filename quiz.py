# quiz.py
"""
クイズプレイ専用アプリケーション（ユーザー向け）
Web化時は user_app/ に移行予定

このファイルの配置場所: プロジェクトルート/quiz.py
"""

import sys
import tkinter as tk
from pathlib import Path

from app.config import get_settings
from app.core.service_factory import initialize_services, shutdown_services, get_quiz_service
from desktop.controller import DesktopController
from desktop.ui.main_window import MainWindow
from utils.logger import get_logger, set_log_level


def check_quiz_readiness() -> tuple[bool, str]:
    """
    クイズ実行可能性をチェック
    
    Returns:
        tuple[bool, str]: (準備完了フラグ, メッセージ)
    """
    try:
        quiz_service = get_quiz_service()
        question_count = quiz_service.get_question_count()
        
        if question_count == 0:
            return False, "問題データがありません。管理者にお問い合わせください。"
        
        return True, f"{question_count}問の問題が利用可能です。"
        
    except Exception as e:
        return False, f"システムエラー: {str(e)}"


def create_user_application() -> tuple[tk.Tk, DesktopController, MainWindow]:
    """
    ユーザー向けアプリケーションを作成
    
    Returns:
        tuple: (root, controller, main_window)
    """
    logger = get_logger()
    
    # tkinterルートウィンドウ作成
    root = tk.Tk()
    
    # コントローラー作成（ユーザー機能のみ）
    controller = DesktopController()
    
    # メインウィンドウ作成
    main_window = MainWindow(root, controller)
    
    # ユーザー向けUIコールバックのみ設定
    controller.set_ui_callbacks({
        'show_question': main_window.show_question,
        'show_answer_result': main_window.show_answer_result,
        'show_results': main_window.show_results,
        'show_statistics': main_window.show_statistics,
        'show_settings': main_window.show_settings,
        'show_main_menu': main_window.show_main_menu,
        'show_error': main_window.show_error,
        'show_info': main_window.show_info
    })
    
    logger.info("ユーザー向けアプリケーション作成完了")
    
    return root, controller, main_window


def main():
    """ユーザー向けメイン関数"""
    logger = None
    
    try:
        # 設定読み込み
        settings = get_settings()
        
        # ログレベル設定
        set_log_level(settings.log_level)
        logger = get_logger()
        
        logger.info("=== クイズアプリケーション起動（ユーザー版） ===")
        logger.info(f"デバッグモード: {settings.debug}")
        
        # サービス初期化
        logger.info("サービス初期化中...")
        initialize_services(settings.database_url)
        logger.info("サービス初期化完了")
        
        # クイズ実行可能性チェック
        is_ready, message = check_quiz_readiness()
        logger.info(f"準備状況: {message}")
        
        if not is_ready:
            print(f"\n❌ エラー: {message}")
            print("\n📋 解決方法:")
            print("   1. 管理者用アプリを起動: python admin.py")
            print("   2. CSVファイルをインポートしてください")
            print("   3. その後、再度このアプリを起動してください")
            print("\n💡 管理者用アプリの使用方法:")
            print("   - GUI版: python admin.py")
            print("   - CLI版: python admin.py --import your_file.csv")
            
            input("\nEnterキーを押して終了...")
            return
        
        # ユーザーアプリケーション作成
        logger.info("ユーザーUIアプリケーション作成中...")
        root, controller, main_window = create_user_application()
        
        # アプリケーション情報表示
        app_info = controller.get_app_info()
        logger.info(f"利用可能問題数: {app_info.get('question_count', 0)}問")
        
        # メインウィンドウ表示
        main_window.show_main_menu()
        
        logger.info("ユーザーアプリケーション開始 - メインループ実行")
        
        # メインループ開始
        root.mainloop()
        
    except KeyboardInterrupt:
        logger.info("ユーザーによる中断")
    except Exception as e:
        if logger:
            logger.error(f"ユーザーアプリケーションエラー: {e}")
        else:
            print(f"起動エラー: {e}")
        
        if settings and settings.debug:
            import traceback
            traceback.print_exc()
        
        print(f"\n❌ アプリケーションエラーが発生しました: {e}")
        print("\n📋 トラブルシューティング:")
        print("   1. データベースファイルが破損している可能性があります")
        print("   2. quiz.db を削除して再度お試しください")
        print("   3. 問題が続く場合は管理者にお問い合わせください")
        
        input("\nEnterキーを押して終了...")
        sys.exit(1)
    
    finally:
        # クリーンアップ
        try:
            if logger:
                logger.info("ユーザーアプリケーション終了処理開始")
            shutdown_services()
            if logger:
                logger.info("ユーザーアプリケーション終了完了")
        except Exception as e:
            print(f"終了処理エラー: {e}")


if __name__ == "__main__":
    main()