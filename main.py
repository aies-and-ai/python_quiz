# main.py
"""
クイズアプリケーション メインエントリーポイント（統合版・検証用）

⚠️ 重要な注意事項 ⚠️
このファイルは統合版・検証用として保持されています。
通常の使用では以下の専用アプリケーションをご利用ください：

📱 ユーザー向け（クイズプレイ）:
   python quiz.py

🛠️ 管理者向け（データ管理）:
   python admin.py

このファイルの配置場所: プロジェクトルート/main.py
"""

import sys
import tkinter as tk
from pathlib import Path
from typing import Optional

# 新アーキテクチャのインポート
from app.config import get_settings
from app.core.service_factory import initialize_services, shutdown_services, get_csv_importer
from desktop.controller import DesktopController
from desktop.ui.main_window import MainWindow
from utils.logger import get_logger, set_log_level


def show_deprecation_notice():
    """統合版使用時の注意事項を表示"""
    print("=" * 60)
    print("🔔 統合版アプリケーション起動")
    print("=" * 60)
    print()
    print("⚠️ このファイル（main.py）は統合版・検証用です。")
    print("   通常の使用では以下の専用アプリをご利用ください：")
    print()
    print("📱 ユーザー向け（クイズプレイ）:")
    print("   python quiz.py")
    print()
    print("🛠️ 管理者向け（データ管理）:")
    print("   python admin.py")
    print()
    print("💡 このまま統合版を使用する場合は10秒後に開始します...")
    print("   中断する場合は Ctrl+C を押してください。")
    print("=" * 60)
    
    try:
        import time
        for i in range(10, 0, -1):
            print(f"開始まであと {i} 秒...", end="\r")
            time.sleep(1)
        print("                    ", end="\r")  # カウントダウンをクリア
        print("🚀 統合版アプリケーションを開始します...")
    except KeyboardInterrupt:
        print("\n\n👋 統合版の起動を中断しました。")
        print("推奨アプリをご利用ください：")
        print("  - ユーザー向け: python quiz.py")
        print("  - 管理者向け: python admin.py")
        sys.exit(0)


def check_initial_setup() -> tuple[bool, list[str]]:
    """初期セットアップをチェック"""
    issues = []
    
    # データベースファイルの確認
    settings = get_settings()
    db_path = settings.get_database_path()
    
    if db_path:
        db_file = Path(db_path)
        if not db_file.parent.exists():
            try:
                db_file.parent.mkdir(parents=True, exist_ok=True)
            except Exception as e:
                issues.append(f"データベースディレクトリの作成に失敗: {e}")
    
    # サンプルCSVファイルの確認
    sample_csv = Path("data/sample_quiz.csv")
    if not sample_csv.exists():
        issues.append(f"サンプルCSVファイルが見つかりません: {sample_csv}")
    
    return len(issues) == 0, issues


def auto_import_csv_files() -> bool:
    """初回起動時にCSVファイルを自動インポート"""
    logger = get_logger()
    
    try:
        csv_importer = get_csv_importer()
        data_dir = Path("data")
        
        if not data_dir.exists():
            logger.info("dataディレクトリが見つかりません - CSVインポートをスキップ")
            return True
        
        csv_files = list(data_dir.glob("*.csv"))
        
        if not csv_files:
            logger.info("CSVファイルが見つかりません - インポートをスキップ")
            return True
        
        logger.info(f"{len(csv_files)}個のCSVファイルを発見 - 自動インポート開始")
        
        total_imported = 0
        for csv_file in csv_files:
            try:
                result = csv_importer.import_from_csv(str(csv_file))
                imported = result.get('imported_count', 0)
                total_imported += imported
                
                logger.info(f"{csv_file.name}: {imported}問インポート")
                
            except Exception as e:
                logger.warning(f"{csv_file.name}のインポートに失敗: {e}")
                continue
        
        logger.info(f"自動インポート完了: 合計{total_imported}問")
        return True
        
    except Exception as e:
        logger.error(f"自動インポートエラー: {e}")
        return False


def create_main_application() -> tuple[tk.Tk, DesktopController, MainWindow]:
    """メインアプリケーションを作成"""
    logger = get_logger()
    
    # tkinterルートウィンドウ作成
    root = tk.Tk()
    
    # コントローラー作成
    controller = DesktopController()
    
    # メインウィンドウ作成
    main_window = MainWindow(root, controller)
    
    # UIコールバックを設定
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
    
    logger.info("メインアプリケーション作成完了")
    
    return root, controller, main_window


def main():
    """メイン関数（統合版・検証用）"""
    
    # 統合版使用時の注意事項を表示
    show_deprecation_notice()
    
    logger = None
    
    try:
        # 設定読み込み
        settings = get_settings()
        
        # ログレベル設定
        set_log_level(settings.log_level)
        logger = get_logger()
        
        logger.info("=== クイズアプリケーション起動（統合版・検証用） ===")
        logger.info(f"デバッグモード: {settings.debug}")
        logger.info("注意: このファイルは統合版です。通常は quiz.py または admin.py をご利用ください。")
        
        # 初期セットアップチェック
        setup_ok, issues = check_initial_setup()
        if not setup_ok:
            for issue in issues:
                logger.warning(f"セットアップ問題: {issue}")
        
        # サービス初期化
        logger.info("サービス初期化中...")
        initialize_services(settings.database_url)
        logger.info("サービス初期化完了")
        
        # 初回CSVインポート
        auto_import_csv_files()
        
        # メインアプリケーション作成
        logger.info("UIアプリケーション作成中...")
        root, controller, main_window = create_main_application()
        
        # アプリケーション情報表示
        app_info = controller.get_app_info()
        logger.info(f"利用可能問題数: {app_info.get('question_count', 0)}問")
        
        if not app_info.get('has_questions', False):
            logger.warning("問題データがありません - CSVファイルをdataディレクトリに配置してください")
            print("\n⚠️ 問題データがありません")
            print("📋 対処方法:")
            print("   1. admin.py を使用してCSVファイルをインポート")
            print("   2. または dataディレクトリにCSVファイルを配置して再起動")
        
        # メインウィンドウ表示
        main_window.show_main_menu()
        
        logger.info("アプリケーション開始 - メインループ実行")
        
        # メインループ開始
        root.mainloop()
        
    except KeyboardInterrupt:
        logger.info("ユーザーによる中断")
    except Exception as e:
        if logger:
            logger.error(f"アプリケーションエラー: {e}")
        else:
            print(f"起動エラー: {e}")
        
        if settings and settings.debug:
            import traceback
            traceback.print_exc()
        
        sys.exit(1)
    
    finally:
        # クリーンアップ
        try:
            if logger:
                logger.info("アプリケーション終了処理開始")
            shutdown_services()
            if logger:
                logger.info("アプリケーション終了完了")
        except Exception as e:
            print(f"終了処理エラー: {e}")


if __name__ == "__main__":
    main()