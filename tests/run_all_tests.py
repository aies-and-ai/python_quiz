# tests/run_all_tests.py
"""
統合テストランナー
プロジェクト全体の検証を実行するメインテストスクリプト
"""

import os
import sys
import time
import subprocess
from pathlib import Path
from typing import List, Dict, Any
import argparse

# プロジェクトルートを取得
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# テストモジュールのインポート
try:
    from tests.test_file_structure import run_file_structure_tests
    from tests.test_imports import run_import_tests
    from tests.test_api_functionality import run_api_functionality_tests
    from tests.test_integration import run_integration_tests
    from tests.test_docker_configuration import run_docker_configuration_tests, run_comprehensive_docker_tests
except ImportError as e:
    print(f"❌ テストモジュールのインポートエラー: {e}")
    sys.exit(1)


class TestResult:
    """テスト結果クラス"""
    
    def __init__(self, name: str, success: bool, duration: float, details: str = ""):
        self.name = name
        self.success = success
        self.duration = duration
        self.details = details
    
    def __str__(self):
        status = "✅ 成功" if self.success else "❌ 失敗"
        return f"{self.name}: {status} ({self.duration:.2f}秒)"


class TestRunner:
    """統合テストランナー"""
    
    def __init__(self, verbose: bool = False, fast_mode: bool = False):
        self.verbose = verbose
        self.fast_mode = fast_mode
        self.results: List[TestResult] = []
        self.start_time = time.time()
    
    def run_test(self, test_name: str, test_function, *args, **kwargs) -> TestResult:
        """個別テストの実行"""
        print(f"\n{'='*60}")
        print(f"🧪 {test_name} 実行中...")
        print(f"{'='*60}")
        
        start_time = time.time()
        
        try:
            success = test_function(*args, **kwargs)
            duration = time.time() - start_time
            
            result = TestResult(test_name, success, duration)
            
            if success:
                print(f"✅ {test_name} 成功 ({duration:.2f}秒)")
            else:
                print(f"❌ {test_name} 失敗 ({duration:.2f}秒)")
            
        except Exception as e:
            duration = time.time() - start_time
            result = TestResult(test_name, False, duration, str(e))
            print(f"❌ {test_name} 例外発生: {e} ({duration:.2f}秒)")
        
        self.results.append(result)
        return result
    
    def run_all_tests(self, include_slow: bool = False) -> bool:
        """全テストの実行"""
        print("🚀 クイズアプリケーション 全体テスト開始")
        print(f"📅 開始時刻: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📁 プロジェクトルート: {PROJECT_ROOT}")
        
        # 1. ファイル構成テスト
        self.run_test("ファイル構成テスト", run_file_structure_tests)
        
        # 2. インポートテスト
        self.run_test("インポートテスト", run_import_tests)
        
        # ファイル構成またはインポートが失敗した場合は中止
        if not all(r.success for r in self.results[-2:]):
            print("\n❌ 基本テストが失敗しました。以降のテストをスキップします。")
            return False
        
        # 3. API機能テスト
        if not self.fast_mode:
            self.run_test("API機能テスト", run_api_functionality_tests)
        
        # 4. 統合テスト
        if not self.fast_mode:
            self.run_test("統合テスト", run_integration_tests)
        
        # 5. Docker構成テスト
        if include_slow:
            self.run_test("包括的Docker構成テスト", run_comprehensive_docker_tests)
        else:
            self.run_test("Docker構成テスト", run_docker_configuration_tests)
        
        return self.print_summary()
    
    def run_basic_tests(self) -> bool:
        """基本テストのみ実行"""
        print("⚡ 基本テスト実行（高速）")
        
        self.run_test("ファイル構成テスト", run_file_structure_tests)
        self.run_test("インポートテスト", run_import_tests)
        
        return self.print_summary()
    
    def run_ci_tests(self) -> bool:
        """CI用テスト実行"""
        print("🔄 CI用テスト実行")
        
        # CI環境で実行する最小限のテスト
        self.run_test("ファイル構成テスト", run_file_structure_tests)
        self.run_test("インポートテスト", run_import_tests)
        self.run_test("Docker構成テスト", run_docker_configuration_tests)
        
        return self.print_summary()
    
    def print_summary(self) -> bool:
        """テスト結果サマリーの表示"""
        total_duration = time.time() - self.start_time
        
        print(f"\n{'='*80}")
        print("📊 テスト結果サマリー")
        print(f"{'='*80}")
        
        success_count = sum(1 for r in self.results if r.success)
        total_count = len(self.results)
        
        # 個別結果
        for result in self.results:
            print(f"  {result}")
            if result.details and self.verbose:
                print(f"    詳細: {result.details}")
        
        print(f"\n📈 統計:")
        print(f"  総テスト数: {total_count}")
        print(f"  成功: {success_count}")
        print(f"  失敗: {total_count - success_count}")
        print(f"  成功率: {(success_count/total_count*100):.1f}%")
        print(f"  総実行時間: {total_duration:.2f}秒")
        
        # 最終判定
        all_success = success_count == total_count
        
        if all_success:
            print(f"\n🎉 全テスト成功！プロジェクトは正常に動作する準備ができています。")
            print(f"   次のステップ: docker compose up -d")
        else:
            print(f"\n⚠️  {total_count - success_count}個のテストが失敗しました。")
            print(f"   失敗したテストを確認して修正してください。")
            
            # 失敗したテストの詳細
            failed_tests = [r for r in self.results if not r.success]
            print(f"\n🔍 失敗テスト詳細:")
            for test in failed_tests:
                print(f"  - {test.name}")
                if test.details:
                    print(f"    エラー: {test.details}")
        
        print(f"{'='*80}")
        
        return all_success
    
    def generate_report(self, output_file: str = "test_report.txt"):
        """テストレポートの生成"""
        report_path = PROJECT_ROOT / output_file
        
        with open(report_path, 'w', encoding='utf-8') as f:
            f.write("クイズアプリケーション テストレポート\n")
            f.write("="*50 + "\n\n")
            
            f.write(f"実行日時: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"プロジェクトルート: {PROJECT_ROOT}\n\n")
            
            # 結果サマリー
            success_count = sum(1 for r in self.results if r.success)
            total_count = len(self.results)
            
            f.write(f"テスト結果サマリー:\n")
            f.write(f"  総テスト数: {total_count}\n")
            f.write(f"  成功: {success_count}\n")
            f.write(f"  失敗: {total_count - success_count}\n")
            f.write(f"  成功率: {(success_count/total_count*100):.1f}%\n\n")
            
            # 個別結果
            f.write("個別テスト結果:\n")
            for result in self.results:
                status = "成功" if result.success else "失敗"
                f.write(f"  {result.name}: {status} ({result.duration:.2f}秒)\n")
                if result.details:
                    f.write(f"    詳細: {result.details}\n")
            
            # 推奨事項
            f.write(f"\n推奨事項:\n")
            if success_count == total_count:
                f.write("  - 全テストが成功しました。docker compose up -d で起動してください。\n")
            else:
                f.write("  - 失敗したテストを確認して修正してください。\n")
                f.write("  - 基本テストが失敗している場合は、ファイル構成を確認してください。\n")
        
        print(f"📄 テストレポートを生成しました: {report_path}")


def check_prerequisites():
    """前提条件のチェック"""
    print("🔍 前提条件チェック...")
    
    issues = []
    
    # Python バージョンチェック
    if sys.version_info < (3, 8):
        issues.append(f"Python 3.8+ が必要です（現在: {sys.version_info}）")
    
    # プロジェクト構造の基本チェック
    required_dirs = ["backend", "frontend", "tests"]
    for dir_name in required_dirs:
        dir_path = PROJECT_ROOT / dir_name
        if not dir_path.exists():
            issues.append(f"必要なディレクトリが見つかりません: {dir_name}")
    
    # 必要ファイルの基本チェック
    required_files = ["requirements.txt", "docker-compose.yml"]
    for file_name in required_files:
        file_path = PROJECT_ROOT / file_name
        if not file_path.exists():
            issues.append(f"必要なファイルが見つかりません: {file_name}")
    
    if issues:
        print("❌ 前提条件エラー:")
        for issue in issues:
            print(f"  - {issue}")
        return False
    
    print("✅ 前提条件チェック完了")
    return True


def main():
    """メイン関数"""
    parser = argparse.ArgumentParser(
        description="クイズアプリケーション統合テストランナー",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  python tests/run_all_tests.py                    # 全テスト実行
  python tests/run_all_tests.py --basic            # 基本テストのみ
  python tests/run_all_tests.py --ci               # CI用テスト
  python tests/run_all_tests.py --comprehensive    # 包括的テスト（低速）
  python tests/run_all_tests.py --fast             # 高速モード
        """
    )
    
    parser.add_argument('--basic', action='store_true', 
                       help='基本テストのみ実行（ファイル構成・インポート）')
    parser.add_argument('--ci', action='store_true',
                       help='CI用テスト実行（Docker環境チェックなし）')
    parser.add_argument('--comprehensive', action='store_true',
                       help='包括的テスト実行（Dockerビルド含む・低速）')
    parser.add_argument('--fast', action='store_true',
                       help='高速モード（統合テストをスキップ）')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='詳細出力')
    parser.add_argument('--report', metavar='FILE', default='test_report.txt',
                       help='テストレポート出力ファイル')
    parser.add_argument('--no-prerequisites', action='store_true',
                       help='前提条件チェックをスキップ')
    
    args = parser.parse_args()
    
    # 前提条件チェック
    if not args.no_prerequisites:
        if not check_prerequisites():
            print("\n前提条件エラーのため、テストを中止します。")
            print("--no-prerequisites オプションでスキップできます。")
            sys.exit(1)
    
    # テストランナー初期化
    runner = TestRunner(verbose=args.verbose, fast_mode=args.fast)
    
    try:
        # テストタイプに応じて実行
        if args.basic:
            success = runner.run_basic_tests()
        elif args.ci:
            success = runner.run_ci_tests()
        elif args.comprehensive:
            success = runner.run_all_tests(include_slow=True)
        else:
            success = runner.run_all_tests(include_slow=False)
        
        # レポート生成
        if args.report:
            runner.generate_report(args.report)
        
        # 終了コード
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n\n⚠️ ユーザーによる中断")
        sys.exit(130)
    except Exception as e:
        print(f"\n❌ 予期しないエラー: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


# 個別テスト実行用の便利関数

def run_quick_check():
    """クイックチェック（最小限のテスト）"""
    print("⚡ クイックチェック実行...")
    
    runner = TestRunner(fast_mode=True)
    
    # ファイル構成のみチェック
    result = runner.run_test("ファイル構成テスト", run_file_structure_tests)
    
    if result.success:
        print("✅ 基本構成OK - 詳細テストを実行してください")
        return True
    else:
        print("❌ 基本構成NG - ファイル構成を確認してください")
        return False


def run_development_check():
    """開発用チェック（Docker除く）"""
    print("🛠️ 開発用チェック実行...")
    
    runner = TestRunner()
    
    runner.run_test("ファイル構成テスト", run_file_structure_tests)
    runner.run_test("インポートテスト", run_import_tests)
    runner.run_test("API機能テスト", run_api_functionality_tests)
    
    return runner.print_summary()


def run_deployment_check():
    """デプロイメント用チェック（Docker含む）"""
    print("🚀 デプロイメント用チェック実行...")
    
    runner = TestRunner()
    
    runner.run_test("ファイル構成テスト", run_file_structure_tests)
    runner.run_test("Docker構成テスト", run_docker_configuration_tests)
    runner.run_test("統合テスト", run_integration_tests)
    
    return runner.print_summary()


# スタンドアローン実行時の追加オプション

if __name__ == "__main__":
    # 環境変数による設定
    test_mode = os.environ.get('QUIZ_TEST_MODE', '').lower()
    
    if test_mode == 'quick':
        success = run_quick_check()
        sys.exit(0 if success else 1)
    elif test_mode == 'dev':
        success = run_development_check()
        sys.exit(0 if success else 1)
    elif test_mode == 'deploy':
        success = run_deployment_check()
        sys.exit(0 if success else 1)
    else:
        # 通常のコマンドライン引数処理
        main()


# テスト設定とヘルパー

class TestConfig:
    """テスト設定クラス"""
    
    # テストタイムアウト設定
    BASIC_TEST_TIMEOUT = 30  # 秒
    INTEGRATION_TEST_TIMEOUT = 120  # 秒
    DOCKER_TEST_TIMEOUT = 300  # 秒
    
    # 期待値設定
    EXPECTED_FILE_COUNT = 16  # Phase 3 目標値
    EXPECTED_MAIN_SERVICES = ['backend', 'frontend']
    EXPECTED_PORTS = [3000, 8000]
    
    # テスト環境設定
    USE_TEMP_DATABASE = True
    CLEANUP_AFTER_TESTS = True
    VERBOSE_ERROR_OUTPUT = False


def validate_test_environment():
    """テスト環境の検証"""
    issues = []
    
    # 書き込み権限チェック
    try:
        test_file = PROJECT_ROOT / "test_write_check.tmp"
        test_file.write_text("test")
        test_file.unlink()
    except Exception:
        issues.append("プロジェクトディレクトリに書き込み権限がありません")
    
    # Python パッケージチェック
    required_packages = ['pytest', 'pyyaml']
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing_packages.append(package)
    
    if missing_packages:
        issues.append(f"必要なPythonパッケージが不足: {', '.join(missing_packages)}")
    
    return issues


# デバッグ用関数

def debug_test_environment():
    """テスト環境のデバッグ情報出力"""
    print("🔍 テスト環境デバッグ情報")
    print(f"  Python: {sys.version}")
    print(f"  プロジェクトルート: {PROJECT_ROOT}")
    print(f"  現在のディレクトリ: {os.getcwd()}")
    print(f"  PATH: {os.environ.get('PATH', 'N/A')[:100]}...")
    
    # インストール済みパッケージ
    try:
        import pkg_resources
        installed = [d.project_name for d in pkg_resources.working_set]
        relevant_packages = [p for p in installed if any(keyword in p.lower() 
                           for keyword in ['pytest', 'fastapi', 'sqlalchemy', 'pydantic'])]
        print(f"  関連パッケージ: {', '.join(relevant_packages[:10])}")
    except:
        print("  パッケージ情報取得失敗")
    
    # ファイルシステム情報
    try:
        import psutil
        disk_usage = psutil.disk_usage(PROJECT_ROOT)
        print(f"  ディスク使用量: {disk_usage.used // (1024**3)}GB / {disk_usage.total // (1024**3)}GB")
    except:
        print("  ディスク情報取得失敗")
    
    # 環境変数
    relevant_env_vars = {k: v for k, v in os.environ.items() 
                        if any(keyword in k.upper() for keyword in ['PYTHON', 'PATH', 'QUIZ', 'TEST'])}
    if relevant_env_vars:
        print("  関連環境変数:")
        for k, v in list(relevant_env_vars.items())[:5]:
            print(f"    {k}={v[:50]}...")


# プロファイリング機能

def profile_tests():
    """テスト実行時間のプロファイリング"""
    try:
        import cProfile
        import pstats
        
        pr = cProfile.Profile()
        pr.enable()
        
        # 基本テストを実行
        runner = TestRunner()
        runner.run_basic_tests()
        
        pr.disable()
        
        # 結果出力
        stats = pstats.Stats(pr)
        stats.sort_stats('cumulative')
        
        profile_output = PROJECT_ROOT / "test_profile.txt"
        with open(profile_output, 'w') as f:
            stats.print_stats(20, file=f)
        
        print(f"📊 プロファイル結果: {profile_output}")
        
    except ImportError:
        print("⚠️ cProfile未利用可能 - プロファイリングをスキップ")


# CI/CD サポート

def generate_junit_xml():
    """JUnit XML形式のテスト結果出力"""
    try:
        # pytest-xml を使用してJUnit XML形式で出力
        result = subprocess.run([
            sys.executable, '-m', 'pytest', 
            str(PROJECT_ROOT / 'tests'),
            '--junitxml=test_results.xml',
            '--tb=short'
        ], capture_output=True, text=True, timeout=300)
        
        if result.returncode == 0:
            print("✅ JUnit XMLレポート生成完了: test_results.xml")
        else:
            print(f"⚠️ JUnit XMLレポート生成で警告: {result.stderr[:200]}")
            
    except subprocess.TimeoutExpired:
        print("❌ JUnit XMLレポート生成タイムアウト")
    except Exception as e:
        print(f"❌ JUnit XMLレポート生成エラー: {e}")


def setup_ci_environment():
    """CI環境セットアップ"""
    print("🔧 CI環境セットアップ...")
    
    # 必要なパッケージのインストール
    required_packages = ['pytest', 'pytest-asyncio', 'pyyaml']
    
    for package in required_packages:
        try:
            subprocess.run([sys.executable, '-m', 'pip', 'install', package], 
                         check=True, capture_output=True, timeout=60)
        except subprocess.CalledProcessError as e:
            print(f"⚠️ パッケージインストール失敗: {package}")
        except subprocess.TimeoutExpired:
            print(f"⚠️ パッケージインストールタイムアウト: {package}")
    
    print("✅ CI環境セットアップ完了")


# 便利なエイリアス関数

def test():
    """シンプルなテスト実行エイリアス"""
    return run_quick_check()


def test_all():
    """全テスト実行エイリアス"""
    runner = TestRunner()
    return runner.run_all_tests()


def test_docker():
    """Dockerテストのみ実行"""
    runner = TestRunner()
    result = runner.run_test("Docker構成テスト", run_docker_configuration_tests)
    return result.success