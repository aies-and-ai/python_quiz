"""
ファイル構成・内容検証スクリプト
新アーキテクチャのファイルが正しく配置され、内容が正しいかを検証
"""

import os
import sys
from pathlib import Path


def check_file_structure():
    """ファイル構成を確認"""
    print("=== ファイル構成検証 ===")
    
    project_root = Path.cwd()
    print(f"プロジェクトルート: {project_root}")
    
    # 期待されるファイル構成
    expected_files = {
        # 新アーキテクチャのファイル
        "main.py": "メインエントリーポイント",
        "app/config.py": "設定管理",
        "app/core/models.py": "データクラスモデル",
        "app/core/database.py": "データベースサービス",
        "app/core/csv_import.py": "CSVインポーター",
        "app/core/quiz.py": "クイズサービス",
        "app/core/service_factory.py": "サービスファクトリー",
        "app/core/exceptions.py": "例外クラス",
        "desktop/controller.py": "デスクトップコントローラー",
        "desktop/ui/main_window.py": "メインウィンドウ",
        "database/connection.py": "データベース接続",
        "database/models.py": "SQLAlchemyモデル",
        "database/__init__.py": "データベースパッケージ初期化",
        "utils/logger.py": "ログ機能",
        
        # テスト・検証ファイル
        "test_integration.py": "統合テスト",
        "requirements.txt": "依存関係"
    }
    
    missing_files = []
    existing_files = []
    
    for file_path, description in expected_files.items():
        full_path = project_root / file_path
        if full_path.exists():
            existing_files.append((file_path, description))
            print(f"✅ {file_path} - {description}")
        else:
            missing_files.append((file_path, description))
            print(f"❌ {file_path} - {description} (見つかりません)")
    
    print(f"\n📊 ファイル構成結果:")
    print(f"存在: {len(existing_files)}, 不足: {len(missing_files)}")
    
    return len(missing_files) == 0


def check_directory_structure():
    """ディレクトリ構成を確認"""
    print("\n=== ディレクトリ構成検証 ===")
    
    project_root = Path.cwd()
    
    expected_dirs = [
        "app",
        "app/core",
        "desktop",
        "desktop/ui", 
        "database",
        "utils"
    ]
    
    missing_dirs = []
    existing_dirs = []
    
    for dir_path in expected_dirs:
        full_path = project_root / dir_path
        if full_path.exists() and full_path.is_dir():
            existing_dirs.append(dir_path)
            print(f"✅ {dir_path}/")
        else:
            missing_dirs.append(dir_path)
            print(f"❌ {dir_path}/ (見つかりません)")
    
    print(f"\n📊 ディレクトリ構成結果:")
    print(f"存在: {len(existing_dirs)}, 不足: {len(missing_dirs)}")
    
    return len(missing_dirs) == 0


def check_python_syntax():
    """Pythonファイルの構文チェック"""
    print("\n=== Python構文検証 ===")
    
    project_root = Path.cwd()
    
    python_files = [
        "main.py",
        "app/config.py",
        "app/core/models.py",
        "app/core/database.py",
        "app/core/csv_import.py",
        "app/core/quiz.py",
        "app/core/service_factory.py",
        "app/core/exceptions.py",
        "desktop/controller.py",
        "desktop/ui/main_window.py",
        "database/connection.py",
        "database/models.py",
        "utils/logger.py"
    ]
    
    syntax_errors = []
    valid_files = []
    
    for file_path in python_files:
        full_path = project_root / file_path
        
        if not full_path.exists():
            print(f"⚠️ {file_path} - ファイルが存在しません")
            continue
        
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # 構文チェック
            compile(content, str(full_path), 'exec')
            valid_files.append(file_path)
            print(f"✅ {file_path} - 構文OK")
            
        except SyntaxError as e:
            syntax_errors.append((file_path, str(e)))
            print(f"❌ {file_path} - 構文エラー: {e}")
        except UnicodeDecodeError as e:
            syntax_errors.append((file_path, f"エンコーディングエラー: {e}"))
            print(f"❌ {file_path} - エンコーディングエラー: {e}")
        except Exception as e:
            syntax_errors.append((file_path, str(e)))
            print(f"❌ {file_path} - その他エラー: {e}")
    
    print(f"\n📊 構文検証結果:")
    print(f"有効: {len(valid_files)}, エラー: {len(syntax_errors)}")
    
    return len(syntax_errors) == 0


def check_import_dependencies():
    """インポート依存関係をチェック"""
    print("\n=== インポート依存関係検証 ===")
    
    project_root = Path.cwd()
    
    # プロジェクトルートをパスに追加
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
    
    import_tests = [
        ("utils.logger", "ログ機能"),
        ("app.config", "設定管理"),
        ("app.core.exceptions", "例外クラス"),
        ("app.core.models", "データモデル"),
        ("database.connection", "データベース接続"),
        ("database.models", "SQLAlchemyモデル")
    ]
    
    import_errors = []
    successful_imports = []
    
    for module_name, description in import_tests:
        try:
            __import__(module_name)
            successful_imports.append((module_name, description))
            print(f"✅ {module_name} - {description}")
        except ImportError as e:
            import_errors.append((module_name, description, str(e)))
            print(f"❌ {module_name} - {description}: {e}")
        except Exception as e:
            import_errors.append((module_name, description, str(e)))
            print(f"💥 {module_name} - {description}: {e}")
    
    print(f"\n📊 インポート検証結果:")
    print(f"成功: {len(successful_imports)}, 失敗: {len(import_errors)}")
    
    if import_errors:
        print("\n詳細なインポートエラー:")
        for module, desc, error in import_errors:
            print(f"  {module}: {error}")
    
    return len(import_errors) == 0


def check_file_contents():
    """重要ファイルの内容をチェック"""
    print("\n=== ファイル内容検証 ===")
    
    project_root = Path.cwd()
    
    content_checks = [
        ("app/core/models.py", "dataclass", "dataclassベースのモデル"),
        ("app/core/database.py", "DatabaseService", "データベースサービスクラス"),
        ("app/core/quiz.py", "QuizService", "クイズサービスクラス"),
        ("app/core/service_factory.py", "ServiceFactory", "サービスファクトリークラス"),
        ("database/connection.py", "DatabaseConnection", "データベース接続クラス"),
        ("main.py", "def main", "メイン関数")
    ]
    
    content_issues = []
    content_ok = []
    
    for file_path, search_term, description in content_checks:
        full_path = project_root / file_path
        
        if not full_path.exists():
            content_issues.append((file_path, f"ファイルが存在しません"))
            print(f"❌ {file_path} - ファイルが存在しません")
            continue
        
        try:
            with open(full_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            if search_term in content:
                content_ok.append((file_path, description))
                print(f"✅ {file_path} - {description}が含まれています")
            else:
                content_issues.append((file_path, f"{search_term}が見つかりません"))
                print(f"❌ {file_path} - {search_term}が見つかりません")
                
        except Exception as e:
            content_issues.append((file_path, str(e)))
            print(f"💥 {file_path} - 読み込みエラー: {e}")
    
    print(f"\n📊 内容検証結果:")
    print(f"OK: {len(content_ok)}, 問題: {len(content_issues)}")
    
    return len(content_issues) == 0


def check_old_files():
    """旧ファイルの残存チェック"""
    print("\n=== 旧ファイル残存チェック ===")
    
    project_root = Path.cwd()
    
    # 削除すべき旧ファイル
    old_files = [
        "enhanced_exceptions.py",
        "quiz_controller.py",
        "quiz_data.py",
        "ui_manager.py",  # 旧版
        "csv_reader.py",  # 複雑版
        "models.py",  # ルートディレクトリのpydantic版
        "settings.py"  # 複雑版
    ]
    
    remaining_old_files = []
    
    for old_file in old_files:
        full_path = project_root / old_file
        if full_path.exists():
            remaining_old_files.append(old_file)
            print(f"⚠️ {old_file} - 旧ファイルが残存しています")
        else:
            print(f"✅ {old_file} - 削除済み")
    
    print(f"\n📊 旧ファイルチェック結果:")
    print(f"削除済み: {len(old_files) - len(remaining_old_files)}, 残存: {len(remaining_old_files)}")
    
    if remaining_old_files:
        print("\n削除推奨ファイル:")
        for old_file in remaining_old_files:
            print(f"  - {old_file}")
    
    return len(remaining_old_files) == 0


def main():
    """メイン検証関数"""
    print("🔍 新アーキテクチャ構成検証開始")
    print("=" * 60)
    
    checks = [
        ("ディレクトリ構成", check_directory_structure),
        ("ファイル構成", check_file_structure),
        ("Python構文", check_python_syntax),
        ("ファイル内容", check_file_contents),
        ("インポート依存関係", check_import_dependencies),
        ("旧ファイル残存", check_old_files)
    ]
    
    passed = 0
    failed = 0
    
    for check_name, check_func in checks:
        print(f"\n{'='*60}")
        print(f"検証: {check_name}")
        print(f"{'='*60}")
        
        try:
            result = check_func()
            if result:
                print(f"\n✅ {check_name}: 合格")
                passed += 1
            else:
                print(f"\n❌ {check_name}: 不合格")
                failed += 1
        except Exception as e:
            print(f"\n💥 {check_name}: 検証エラー - {e}")
            failed += 1
    
    print(f"\n{'='*60}")
    print(f"📊 最終検証結果")
    print(f"{'='*60}")
    print(f"合格: {passed}, 不合格: {failed}")
    
    if failed == 0:
        print("🎉 すべての検証に合格しました！")
        print("統合テストを実行できます: python test_integration.py")
    else:
        print("💥 検証に失敗した項目があります。")
        print("上記の問題を修正してから統合テストを実行してください。")
    
    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)