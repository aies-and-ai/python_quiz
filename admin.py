# admin.py
"""
データ管理専用アプリケーション（管理者向け）
Web化時は admin_app/ に移行予定

このファイルの配置場所: プロジェクトルート/admin.py
"""

import sys
import os
import argparse
import tkinter as tk
from tkinter import filedialog, messagebox, scrolledtext
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
                for error in result['errors'][:5]:  # 最初の5つのエラーを表示
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


class AdminGUI:
    """管理者向けGUI機能"""
    
    def __init__(self):
        self.logger = get_logger()
        self.csv_importer = get_csv_importer()
        self.db_service = get_database_service()
        
        self.root = tk.Tk()
        self.root.title("クイズアプリ - 管理者パネル")
        self.root.geometry("700x500")
        self.root.configure(bg="#f0f0f0")
        
        # ウィンドウを中央に配置
        self.root.update_idletasks()
        x = (self.root.winfo_screenwidth() // 2) - (700 // 2)
        y = (self.root.winfo_screenheight() // 2) - (500 // 2)
        self.root.geometry(f"700x500+{x}+{y}")
        
        self.create_gui()
    
    def create_gui(self):
        """GUI作成"""
        # タイトル
        title = tk.Label(
            self.root,
            text="🛠️ クイズアプリ管理者パネル",
            font=("Arial", 18, "bold"),
            bg="#f0f0f0",
            fg="#2C3E50"
        )
        title.pack(pady=20)
        
        # データベース情報表示
        info_frame = tk.LabelFrame(
            self.root, 
            text="📊 データベース情報", 
            font=("Arial", 12, "bold"),
            bg="#f0f0f0",
            fg="#34495E"
        )
        info_frame.pack(fill=tk.X, padx=20, pady=10)
        
        self.info_text = scrolledtext.ScrolledText(
            info_frame, 
            height=8, 
            width=80,
            font=("Consolas", 10),
            wrap=tk.WORD
        )
        self.info_text.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        
        # ボタンフレーム
        button_frame = tk.Frame(self.root, bg="#f0f0f0")
        button_frame.pack(pady=20)
        
        # 上段ボタン
        top_buttons = tk.Frame(button_frame, bg="#f0f0f0")
        top_buttons.pack(pady=5)
        
        # CSVインポートボタン
        import_btn = tk.Button(
            top_buttons,
            text="📂 CSVファイルをインポート",
            font=("Arial", 11, "bold"),
            command=self.import_csv_file,
            bg="#27AE60",
            fg="white",
            width=25,
            height=2,
            relief=tk.RAISED,
            bd=2
        )
        import_btn.pack(side=tk.LEFT, padx=5)
        
        # 一括インポートボタン
        batch_btn = tk.Button(
            top_buttons,
            text="📁 フォルダ一括インポート",
            font=("Arial", 11, "bold"),
            command=self.batch_import_folder,
            bg="#3498DB",
            fg="white",
            width=25,
            height=2,
            relief=tk.RAISED,
            bd=2
        )
        batch_btn.pack(side=tk.LEFT, padx=5)
        
        # 下段ボタン
        bottom_buttons = tk.Frame(button_frame, bg="#f0f0f0")
        bottom_buttons.pack(pady=5)
        
        # 情報更新ボタン
        refresh_btn = tk.Button(
            bottom_buttons,
            text="🔄 情報更新",
            font=("Arial", 11, "bold"),
            command=self.refresh_info,
            bg="#F39C12",
            fg="white",
            width=25,
            height=2,
            relief=tk.RAISED,
            bd=2
        )
        refresh_btn.pack(side=tk.LEFT, padx=5)
        
        # ユーザーアプリ起動ボタン
        launch_btn = tk.Button(
            bottom_buttons,
            text="🎯 ユーザーアプリ起動",
            font=("Arial", 11, "bold"),
            command=self.launch_user_app,
            bg="#9B59B6",
            fg="white",
            width=25,
            height=2,
            relief=tk.RAISED,
            bd=2
        )
        launch_btn.pack(side=tk.LEFT, padx=5)
        
        # 初期情報表示
        self.refresh_info()
    
    def refresh_info(self):
        """データベース情報を更新"""
        try:
            info = self.db_service.get_database_info()
            
            info_text = f"""📊 データベース統計情報
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📝 問題データ
   問題数: {info['question_count']}問
   カテゴリ: {', '.join(info['categories']) if info['categories'] else 'なし'}
   難易度: {', '.join(info['difficulties']) if info['difficulties'] else 'なし'}

📈 利用状況
   セッション数: {info['session_count']}件
   履歴数: {info['history_count']}件

💾 データベース情報
   場所: {get_settings().database_url}
   
🎯 利用状況
   - 問題データが存在します: {'はい' if info['question_count'] > 0 else 'いいえ'}
   - ユーザーアプリ起動可能: {'はい' if info['question_count'] > 0 else 'いいえ'}

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"""
            
            self.info_text.delete(1.0, tk.END)
            self.info_text.insert(1.0, info_text)
            
        except Exception as e:
            error_msg = f"❌ 情報取得エラー: {str(e)}"
            self.info_text.delete(1.0, tk.END)  
            self.info_text.insert(1.0, error_msg)
            self.logger.error(f"情報取得エラー: {e}")
    
    def import_csv_file(self):
        """CSVファイルを選択してインポート"""
        file_path = filedialog.askopenfilename(
            title="インポートするCSVファイルを選択",
            filetypes=[("CSV files", "*.csv"), ("All files", "*.*")],
            initialdir=str(Path.cwd())
        )
        
        if file_path:
            try:
                self.info_text.insert(tk.END, f"\n\n📂 インポート開始: {Path(file_path).name}")
                self.info_text.see(tk.END)
                self.root.update()
                
                result = self.csv_importer.import_from_csv(file_path, overwrite=False)
                
                if result['success']:
                    message = f"✅ インポート完了!\n\n成功: {result['imported_count']}問"
                    if result['skipped_count'] > 0:
                        message += f"\nスキップ: {result['skipped_count']}問（重複）"
                    if result['error_count'] > 0:
                        message += f"\nエラー: {result['error_count']}問"
                    
                    messagebox.showinfo("インポート成功", message)
                    self.refresh_info()
                else:
                    error_msg = "\n".join(result['errors'][:3])  # 最初の3つのエラーを表示
                    if len(result['errors']) > 3:
                        error_msg += f"\n... 他{len(result['errors']) - 3}個のエラー"
                    messagebox.showerror("インポート失敗", f"インポートに失敗しました:\n\n{error_msg}")
                    
            except Exception as e:
                messagebox.showerror("エラー", f"インポート処理でエラーが発生しました:\n{str(e)}")
                self.logger.error(f"CSVインポートエラー: {e}")
    
    def batch_import_folder(self):
        """フォルダを選択して一括インポート"""
        folder_path = filedialog.askdirectory(
            title="CSVファイルが含まれるフォルダを選択",
            initialdir=str(Path.cwd())
        )
        
        if folder_path:
            try:
                csv_files = list(Path(folder_path).glob("*.csv"))
                
                if not csv_files:
                    messagebox.showwarning("警告", "選択したフォルダにCSVファイルが見つかりません")
                    return
                
                # 確認ダイアログ
                confirm = messagebox.askyesno(
                    "一括インポート確認", 
                    f"フォルダ内の{len(csv_files)}個のCSVファイルをインポートします。\n実行しますか？"
                )
                
                if not confirm:
                    return
                
                self.info_text.insert(tk.END, f"\n\n📁 一括インポート開始: {len(csv_files)}ファイル")
                self.info_text.see(tk.END)
                self.root.update()
                
                success_count = 0
                total_imported = 0
                
                for csv_file in csv_files:
                    self.info_text.insert(tk.END, f"\n処理中: {csv_file.name}")
                    self.info_text.see(tk.END)
                    self.root.update()
                    
                    result = self.csv_importer.import_from_csv(str(csv_file), overwrite=False)
                    if result['success']:
                        success_count += 1
                        total_imported += result['imported_count']
                        self.info_text.insert(tk.END, f" ✅ {result['imported_count']}問")
                    else:
                        self.info_text.insert(tk.END, f" ❌ 失敗")
                
                message = f"一括インポート完了!\n\n成功ファイル: {success_count}/{len(csv_files)}\n総インポート数: {total_imported}問"
                messagebox.showinfo("一括インポート完了", message)
                self.refresh_info()
                
            except Exception as e:
                messagebox.showerror("エラー", f"一括インポート処理でエラーが発生しました:\n{str(e)}")
                self.logger.error(f"一括インポートエラー: {e}")
    
    def launch_user_app(self):
        """ユーザーアプリを起動"""
        try:
            import subprocess
            
            # 問題データの存在確認
            question_count = self.db_service.get_question_count()
            if question_count == 0:
                messagebox.showwarning(
                    "警告", 
                    "問題データがありません。\n先にCSVファイルをインポートしてください。"
                )
                return
            
            # ユーザーアプリ起動
            subprocess.Popen([sys.executable, "quiz.py"], cwd=Path.cwd())
            messagebox.showinfo("起動", "ユーザーアプリを起動しました。")
            
        except Exception as e:
            messagebox.showerror("エラー", f"ユーザーアプリの起動に失敗しました:\n{str(e)}")
            self.logger.error(f"ユーザーアプリ起動エラー: {e}")
    
    def run(self):
        """GUI実行"""
        try:
            self.root.mainloop()
        except Exception as e:
            self.logger.error(f"GUI実行エラー: {e}")
            messagebox.showerror("エラー", f"アプリケーションエラー:\n{str(e)}")


def main():
    """管理者向けメイン関数"""
    parser = argparse.ArgumentParser(
        description="クイズアプリ管理者ツール",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  python admin.py                          # GUI版を起動
  python admin.py --gui                    # GUI版を起動
  python admin.py --import file.csv        # CSVファイルをインポート
  python admin.py --batch ./data/          # フォルダを一括インポート
  python admin.py --info                   # データベース情報を表示
        """
    )
    
    parser.add_argument("--import", dest="import_file", help="CSVファイルをインポート")
    parser.add_argument("--batch", dest="batch_dir", help="ディレクトリ内の全CSVファイルを一括インポート")
    parser.add_argument("--info", action="store_true", help="データベース情報を表示")
    parser.add_argument("--gui", action="store_true", help="GUI版を起動（デフォルト）")
    parser.add_argument("--overwrite", action="store_true", help="既存データを上書き")
    
    args = parser.parse_args()
    
    try:
        # 設定読み込み
        settings = get_settings()
        set_log_level(settings.log_level)
        logger = get_logger()
        
        logger.info("=== クイズアプリケーション管理者ツール起動 ===")
        
        # サービス初期化
        logger.info("サービス初期化中...")
        initialize_services(settings.database_url)
        logger.info("サービス初期化完了")
        
        # CLI機能の実行
        if args.import_file or args.batch_dir or args.info:
            cli = AdminCLI()
            
            if args.import_file:
                success = cli.import_csv(args.import_file, args.overwrite)
                sys.exit(0 if success else 1)
            
            if args.batch_dir:
                success = cli.batch_import(args.batch_dir, args.overwrite)
                sys.exit(0 if success else 1)
            
            if args.info:
                cli.show_database_info()
                sys.exit(0)
        
        # GUI版の起動（デフォルト、または明示的に指定）
        else:
            logger.info("管理者GUI起動中...")
            gui = AdminGUI()
            gui.run()
    
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
        logger.info("管理者ツール終了処理開始")
        shutdown_services()
        logger.info("管理者ツール終了完了")


if __name__ == "__main__":
    main()