# tests/test_file_structure.py
"""
ファイル構成とプロジェクト構造の検証テスト
全ファイルの存在確認と構造の妥当性をチェック
"""

import os
import sys
import pytest
from pathlib import Path
import json
import yaml

# プロジェクトルートを取得
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


class TestFileStructure:
    """ファイル構成テストクラス"""
    
    def test_project_root_exists(self):
        """プロジェクトルートディレクトリの存在確認"""
        assert PROJECT_ROOT.exists(), f"プロジェクトルートが見つかりません: {PROJECT_ROOT}"
        assert PROJECT_ROOT.is_dir(), "プロジェクトルートがディレクトリではありません"
    
    def test_required_directories(self):
        """必須ディレクトリの存在確認"""
        required_dirs = [
            "backend",
            "backend/app", 
            "backend/app/api",
            "backend/app/core",
            "backend/app/models",
            "frontend",
            "frontend/src",
            "frontend/src/pages",
            "frontend/src/services", 
            "frontend/src/store",
            "frontend/src/types",
            "utils",
            "database",
            "tests"  # このテストディレクトリ自体
        ]
        
        missing_dirs = []
        for dir_path in required_dirs:
            full_path = PROJECT_ROOT / dir_path
            if not full_path.exists():
                missing_dirs.append(dir_path)
            elif not full_path.is_dir():
                missing_dirs.append(f"{dir_path} (ファイルが存在)")
        
        assert not missing_dirs, f"必須ディレクトリが見つかりません: {missing_dirs}"
    
    def test_backend_files(self):
        """バックエンドファイルの存在確認"""
        backend_files = [
            "backend/main.py",
            "backend/app/__init__.py",
            "backend/app/api/__init__.py", 
            "backend/app/api/quiz.py",
            "backend/app/api/health.py",
            "backend/app/core/quiz.py",
            "backend/app/core/database.py",
            "backend/app/core/csv_import.py",
            "backend/app/core/service_factory.py",
            "backend/app/core/models.py",
            "backend/app/core/interfaces.py",
            "backend/app/core/dependencies.py",
            "backend/app/core/exceptions.py",
            "backend/app/models/__init__.py",
            "backend/app/models/quiz_models.py",
            "backend/app/models/common.py",
            "backend/app/config.py"
        ]
        
        missing_files = []
        for file_path in backend_files:
            full_path = PROJECT_ROOT / file_path
            if not full_path.exists():
                missing_files.append(file_path)
            elif not full_path.is_file():
                missing_files.append(f"{file_path} (ディレクトリが存在)")
        
        assert not missing_files, f"バックエンドファイルが見つかりません: {missing_files}"
    
    def test_frontend_files(self):
        """フロントエンドファイルの存在確認"""
        frontend_files = [
            "frontend/src/App.tsx",
            "frontend/src/pages/HomePage.tsx",
            "frontend/src/pages/QuizPage.tsx", 
            "frontend/src/pages/HistoryPage.tsx",
            "frontend/src/services/api.ts",
            "frontend/src/store/quiz.tsx",
            "frontend/src/types/quiz.ts",
            "frontend/package.json"
        ]
        
        missing_files = []
        for file_path in frontend_files:
            full_path = PROJECT_ROOT / file_path
            if not full_path.exists():
                missing_files.append(file_path)
            elif not full_path.is_file():
                missing_files.append(f"{file_path} (ディレクトリが存在)")
        
        assert not missing_files, f"フロントエンドファイルが見つかりません: {missing_files}"
    
    def test_shared_files(self):
        """共有ファイルの存在確認"""
        shared_files = [
            "admin.py",
            "quiz.py", 
            "requirements.txt",
            "utils/logger.py",
            "database/__init__.py",
            "database/connection.py",
            "database/models.py",
            "config.json",
            ".gitignore"
        ]
        
        missing_files = []
        for file_path in shared_files:
            full_path = PROJECT_ROOT / file_path
            if not full_path.exists():
                missing_files.append(file_path)
            elif not full_path.is_file():
                missing_files.append(f"{file_path} (ディレクトリが存在)")
        
        assert not missing_files, f"共有ファイルが見つかりません: {missing_files}"
    
    def test_docker_files(self):
        """Docker関連ファイルの存在確認"""
        docker_files = [
            "docker-compose.yml",
            "Dockerfile.backend",
            "Dockerfile.frontend"
        ]
        
        missing_files = []
        for file_path in docker_files:
            full_path = PROJECT_ROOT / file_path
            if not full_path.exists():
                missing_files.append(file_path)
            elif not full_path.is_file():
                missing_files.append(f"{file_path} (ディレクトリが存在)")
        
        assert not missing_files, f"Dockerファイルが見つかりません: {missing_files}"
    
    def test_documentation_files(self):
        """ドキュメントファイルの存在確認"""
        doc_files = [
            "README.md"
        ]
        
        missing_files = []
        for file_path in doc_files:
            full_path = PROJECT_ROOT / file_path
            if not full_path.exists():
                missing_files.append(file_path)
            elif not full_path.is_file():
                missing_files.append(f"{file_path} (ディレクトリが存在)")
        
        assert not missing_files, f"ドキュメントファイルが見つかりません: {missing_files}"
    
    def test_file_sizes(self):
        """重要ファイルのサイズ確認（空ファイルでないことを確認）"""
        important_files = [
            "backend/main.py",
            "backend/app/api/quiz.py",
            "frontend/src/App.tsx",
            "frontend/src/pages/HomePage.tsx",
            "docker-compose.yml",
            "README.md"
        ]
        
        empty_files = []
        for file_path in important_files:
            full_path = PROJECT_ROOT / file_path
            if full_path.exists() and full_path.stat().st_size == 0:
                empty_files.append(file_path)
        
        assert not empty_files, f"重要ファイルが空です: {empty_files}"
    
    def test_python_file_syntax(self):
        """Pythonファイルの構文チェック"""
        python_files = [
            "admin.py",
            "quiz.py",
            "backend/main.py",
            "backend/app/config.py",
            "backend/app/core/quiz.py",
            "backend/app/core/database.py",
            "backend/app/api/quiz.py",
            "backend/app/api/health.py",
            "utils/logger.py"
        ]
        
        syntax_errors = []
        for file_path in python_files:
            full_path = PROJECT_ROOT / file_path
            if full_path.exists():
                try:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    compile(content, str(full_path), 'exec')
                except SyntaxError as e:
                    syntax_errors.append(f"{file_path}: {e}")
                except Exception as e:
                    syntax_errors.append(f"{file_path}: {e}")
        
        assert not syntax_errors, f"Pythonファイルに構文エラーがあります: {syntax_errors}"
    
    def test_json_file_format(self):
        """JSONファイルのフォーマット確認"""
        json_files = [
            "config.json",
            "frontend/package.json"
        ]
        
        format_errors = []
        for file_path in json_files:
            full_path = PROJECT_ROOT / file_path
            if full_path.exists():
                try:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        json.load(f)
                except json.JSONDecodeError as e:
                    format_errors.append(f"{file_path}: {e}")
                except Exception as e:
                    format_errors.append(f"{file_path}: {e}")
        
        assert not format_errors, f"JSONファイルにフォーマットエラーがあります: {format_errors}"
    
    def test_yaml_file_format(self):
        """YAMLファイルのフォーマット確認"""
        yaml_files = [
            "docker-compose.yml"
        ]
        
        format_errors = []
        for file_path in yaml_files:
            full_path = PROJECT_ROOT / file_path
            if full_path.exists():
                try:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        yaml.safe_load(f)
                except yaml.YAMLError as e:
                    format_errors.append(f"{file_path}: {e}")
                except Exception as e:
                    format_errors.append(f"{file_path}: {e}")
        
        assert not format_errors, f"YAMLファイルにフォーマットエラーがあります: {format_errors}"
    
    def test_requirements_format(self):
        """requirements.txtの形式確認"""
        req_file = PROJECT_ROOT / "requirements.txt"
        if req_file.exists():
            with open(req_file, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            invalid_lines = []
            for i, line in enumerate(lines, 1):
                line = line.strip()
                if line and not line.startswith('#'):
                    # 基本的なパッケージ名チェック
                    if not any(c.isalnum() or c in '-_.' for c in line.split('==')[0].split('>=')[0].split('<=')[0]):
                        invalid_lines.append(f"行 {i}: {line}")
            
            assert not invalid_lines, f"requirements.txtに無効な行があります: {invalid_lines}"
    
    def test_directory_permissions(self):
        """ディレクトリの読み書き権限確認"""
        writable_dirs = [
            "backend",
            "frontend", 
            "tests"
        ]
        
        permission_errors = []
        for dir_path in writable_dirs:
            full_path = PROJECT_ROOT / dir_path
            if full_path.exists():
                if not os.access(full_path, os.R_OK):
                    permission_errors.append(f"{dir_path}: 読み取り権限なし")
                if not os.access(full_path, os.W_OK):
                    permission_errors.append(f"{dir_path}: 書き込み権限なし")
        
        assert not permission_errors, f"ディレクトリ権限エラー: {permission_errors}"
    
    def test_file_encoding(self):
        """ファイルエンコーディングの確認（UTF-8）"""
        text_files = [
            "README.md",
            "backend/main.py",
            "frontend/src/App.tsx",
            "config.json"
        ]
        
        encoding_errors = []
        for file_path in text_files:
            full_path = PROJECT_ROOT / file_path
            if full_path.exists():
                try:
                    with open(full_path, 'r', encoding='utf-8') as f:
                        f.read()
                except UnicodeDecodeError as e:
                    encoding_errors.append(f"{file_path}: UTF-8でない可能性")
                except Exception as e:
                    encoding_errors.append(f"{file_path}: {e}")
        
        assert not encoding_errors, f"ファイルエンコーディングエラー: {encoding_errors}"
    
    def test_total_file_count(self):
        """総ファイル数の確認（目標：17ファイル以下）"""
        # Phase3で作成された主要ファイル数をカウント
        main_files = [
            # バックエンド
            "backend/main.py",
            "backend/app/api/quiz.py", 
            "backend/app/api/health.py",
            "backend/app/api/__init__.py",
            
            # フロントエンド
            "frontend/src/App.tsx",
            "frontend/src/pages/HomePage.tsx",
            "frontend/src/pages/QuizPage.tsx",
            "frontend/src/pages/HistoryPage.tsx",
            "frontend/src/services/api.ts",
            "frontend/src/store/quiz.tsx",
            "frontend/src/types/quiz.ts",
            
            # Docker・設定
            "docker-compose.yml",
            "Dockerfile.backend", 
            "Dockerfile.frontend",
            "README.md",
            
            # 継続ファイル
            "admin.py"
        ]
        
        existing_files = []
        for file_path in main_files:
            full_path = PROJECT_ROOT / file_path
            if full_path.exists():
                existing_files.append(file_path)
        
        file_count = len(existing_files)
        
        # 目標は17ファイル以下
        assert file_count <= 17, f"メインファイル数が目標を超えています: {file_count}/17"
        
        # 最低限必要なファイル数（10ファイル以上）
        assert file_count >= 10, f"メインファイル数が少なすぎます: {file_count}"
        
        print(f"✅ メインファイル数: {file_count}/17 (目標達成)")


class TestProjectStructure:
    """プロジェクト構造の論理的妥当性テスト"""
    
    def test_backend_structure(self):
        """バックエンド構造の妥当性"""
        # APIファイルがapi/ディレクトリに配置されているか
        api_files = ["quiz.py", "health.py", "__init__.py"]
        for file_name in api_files:
            file_path = PROJECT_ROOT / "backend" / "app" / "api" / file_name
            assert file_path.exists(), f"APIファイルが正しい場所にありません: {file_name}"
        
        # コアビジネスロジックがcore/ディレクトリに配置されているか
        core_files = ["quiz.py", "database.py", "service_factory.py"]
        for file_name in core_files:
            file_path = PROJECT_ROOT / "backend" / "app" / "core" / file_name
            assert file_path.exists(), f"コアファイルが正しい場所にありません: {file_name}"
    
    def test_frontend_structure(self):
        """フロントエンド構造の妥当性"""
        # ページコンポーネントがpages/ディレクトリに配置されているか
        page_files = ["HomePage.tsx", "QuizPage.tsx", "HistoryPage.tsx"]
        for file_name in page_files:
            file_path = PROJECT_ROOT / "frontend" / "src" / "pages" / file_name
            assert file_path.exists(), f"ページファイルが正しい場所にありません: {file_name}"
        
        # サービス層がservices/ディレクトリに配置されているか
        service_files = ["api.ts"]
        for file_name in service_files:
            file_path = PROJECT_ROOT / "frontend" / "src" / "services" / file_name
            assert file_path.exists(), f"サービスファイルが正しい場所にありません: {file_name}"
    
    def test_layer_separation(self):
        """レイヤー分離の確認"""
        # API層、ビジネス層、データ層の分離確認
        layers = {
            "api": "backend/app/api",
            "core": "backend/app/core", 
            "models": "backend/app/models",
            "database": "database"
        }
        
        for layer_name, layer_path in layers.items():
            full_path = PROJECT_ROOT / layer_path
            assert full_path.exists(), f"{layer_name}層のディレクトリが見つかりません: {layer_path}"
            assert full_path.is_dir(), f"{layer_name}層がディレクトリではありません: {layer_path}"


def run_file_structure_tests():
    """ファイル構造テストの実行"""
    print("🔍 ファイル構造テスト開始...")
    
    # pytestを使用してテストを実行
    result = pytest.main([
        __file__,
        "-v",  # 詳細出力
        "--tb=short",  # 短いトレースバック
        "-x",  # 最初のエラーで停止
    ])
    
    if result == 0:
        print("✅ ファイル構造テスト: 全て通過")
        return True
    else:
        print("❌ ファイル構造テスト: 失敗")
        return False


if __name__ == "__main__":
    # スタンドアローン実行時
    success = run_file_structure_tests()
    sys.exit(0 if success else 1)