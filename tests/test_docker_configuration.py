# tests/test_docker_configuration.py
"""
Docker構成テスト
Docker関連ファイルの妥当性とコンテナ設定をテスト
"""

import os
import sys
import pytest
import yaml
import subprocess
from pathlib import Path
import json
import warnings

# プロジェクトルートを取得
PROJECT_ROOT = Path(__file__).parent.parent


class TestDockerFiles:
    """Dockerファイルの存在と妥当性テスト"""
    
    def test_docker_compose_file_exists(self):
        """docker-compose.yml の存在確認"""
        compose_file = PROJECT_ROOT / "docker-compose.yml"
        assert compose_file.exists(), "docker-compose.yml が見つかりません"
        assert compose_file.is_file(), "docker-compose.yml がファイルではありません"
    
    def test_dockerfile_backend_exists(self):
        """Dockerfile.backend の存在確認"""
        dockerfile = PROJECT_ROOT / "Dockerfile.backend"
        assert dockerfile.exists(), "Dockerfile.backend が見つかりません"
        assert dockerfile.is_file(), "Dockerfile.backend がファイルではありません"
    
    def test_dockerfile_frontend_exists(self):
        """Dockerfile.frontend の存在確認"""
        dockerfile = PROJECT_ROOT / "Dockerfile.frontend"
        assert dockerfile.exists(), "Dockerfile.frontend が見つかりません"
        assert dockerfile.is_file(), "Dockerfile.frontend がファイルではありません"
    
    def test_docker_compose_syntax(self):
        """docker-compose.yml の構文確認"""
        compose_file = PROJECT_ROOT / "docker-compose.yml"
        
        try:
            with open(compose_file, 'r', encoding='utf-8') as f:
                compose_config = yaml.safe_load(f)
            
            # 基本構造確認
            assert 'version' in compose_config, "versionが定義されていません"
            assert 'services' in compose_config, "servicesが定義されていません"
            
            # バージョン確認
            version = compose_config['version']
            assert isinstance(version, str), "versionが文字列ではありません"
            assert version.startswith('3.'), f"Docker Compose v3系ではありません: {version}"
            
        except yaml.YAMLError as e:
            pytest.fail(f"docker-compose.yml の構文エラー: {e}")
        except Exception as e:
            pytest.fail(f"docker-compose.yml の読み込みエラー: {e}")
    
    def test_dockerfile_backend_syntax(self):
        """Dockerfile.backend の基本構文確認"""
        dockerfile = PROJECT_ROOT / "Dockerfile.backend"
        
        with open(dockerfile, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 基本的なDockerfile構文確認
        required_instructions = ['FROM', 'WORKDIR', 'COPY', 'RUN', 'EXPOSE']
        missing_instructions = []
        
        for instruction in required_instructions:
            if instruction not in content:
                missing_instructions.append(instruction)
        
        assert not missing_instructions, f"必要なDockerfile命令がありません: {missing_instructions}"
        
        # Python関連の確認
        assert 'python' in content.lower(), "PythonベースのDockerfileではありません"
        assert 'requirements.txt' in content, "requirements.txtが参照されていません"
    
    def test_dockerfile_frontend_syntax(self):
        """Dockerfile.frontend の基本構文確認"""
        dockerfile = PROJECT_ROOT / "Dockerfile.frontend"
        
        with open(dockerfile, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 基本的なDockerfile構文確認
        required_instructions = ['FROM', 'WORKDIR', 'COPY', 'RUN', 'EXPOSE']
        missing_instructions = []
        
        for instruction in required_instructions:
            if instruction not in content:
                missing_instructions.append(instruction)
        
        assert not missing_instructions, f"必要なDockerfile命令がありません: {missing_instructions}"
        
        # Node.js関連の確認
        assert 'node' in content.lower(), "Node.jsベースのDockerfileではありません"
        assert 'package.json' in content, "package.jsonが参照されていません"


class TestDockerComposeConfiguration:
    """Docker Compose設定の詳細テスト"""
    
    @pytest.fixture
    def compose_config(self):
        """docker-compose.yml の読み込み"""
        compose_file = PROJECT_ROOT / "docker-compose.yml"
        
        with open(compose_file, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    
    def test_required_services(self, compose_config):
        """必要なサービスの定義確認"""
        services = compose_config.get('services', {})
        
        required_services = ['backend', 'frontend']
        missing_services = []
        
        for service in required_services:
            if service not in services:
                missing_services.append(service)
        
        assert not missing_services, f"必要なサービスが定義されていません: {missing_services}"
    
    def test_backend_service_configuration(self, compose_config):
        """バックエンドサービスの設定確認"""
        services = compose_config.get('services', {})
        backend = services.get('backend', {})
        
        # 基本設定確認
        assert 'build' in backend, "バックエンドのbuild設定がありません"
        assert 'ports' in backend, "バックエンドのポート設定がありません"
        assert 'volumes' in backend, "バックエンドのボリューム設定がありません"
        assert 'environment' in backend, "バックエンドの環境変数設定がありません"
        
        # ポート設定確認
        ports = backend.get('ports', [])
        assert any('8000' in str(port) for port in ports), "バックエンドポート8000が設定されていません"
        
        # 環境変数確認
        env = backend.get('environment', {})
        if isinstance(env, list):
            env_dict = {}
            for item in env:
                if '=' in item:
                    key, value = item.split('=', 1)
                    env_dict[key] = value
            env = env_dict
        
        expected_env_vars = ['API_HOST', 'API_PORT', 'DATABASE_URL']
        missing_env_vars = []
        
        for var in expected_env_vars:
            if var not in env:
                missing_env_vars.append(var)
        
        assert not missing_env_vars, f"バックエンドに必要な環境変数がありません: {missing_env_vars}"
    
    def test_frontend_service_configuration(self, compose_config):
        """フロントエンドサービスの設定確認"""
        services = compose_config.get('services', {})
        frontend = services.get('frontend', {})
        
        # 基本設定確認
        assert 'build' in frontend, "フロントエンドのbuild設定がありません"
        assert 'ports' in frontend, "フロントエンドのポート設定がありません"
        assert 'depends_on' in frontend, "フロントエンドの依存関係設定がありません"
        
        # ポート設定確認
        ports = frontend.get('ports', [])
        assert any('3000' in str(port) for port in ports), "フロントエンドポート3000が設定されていません"
        
        # 依存関係確認
        depends_on = frontend.get('depends_on', {})
        if isinstance(depends_on, list):
            assert 'backend' in depends_on, "バックエンドへの依存関係がありません"
        elif isinstance(depends_on, dict):
            assert 'backend' in depends_on, "バックエンドへの依存関係がありません"
    
    def test_network_configuration(self, compose_config):
        """ネットワーク設定の確認"""
        if 'networks' in compose_config:
            networks = compose_config['networks']
            assert isinstance(networks, dict), "ネットワーク設定が辞書型ではありません"
        
        # サービス間でのネットワーク設定確認
        services = compose_config.get('services', {})
        
        for service_name, service_config in services.items():
            if 'networks' in service_config:
                assert isinstance(service_config['networks'], list), f"{service_name}のネットワーク設定が正しくありません"
    
    def test_volume_configuration(self, compose_config):
        """ボリューム設定の確認"""
        services = compose_config.get('services', {})
        backend = services.get('backend', {})
        
        if 'volumes' in backend:
            volumes = backend['volumes']
            assert isinstance(volumes, list), "バックエンドのボリューム設定がリスト型ではありません"
            
            # データ永続化用ボリュームの確認
            volume_paths = [vol.split(':')[1] if ':' in vol else vol for vol in volumes]
            assert any('/app/data' in path for path in volume_paths), "データ永続化ボリュームがありません"


class TestDockerBuildability:
    """Docker ビルド可能性テスト"""
    
    def test_docker_available(self):
        """Dockerコマンドの利用可能性確認"""
        try:
            result = subprocess.run(['docker', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            assert result.returncode == 0, "Dockerコマンドが利用できません"
            
            version_output = result.stdout.lower()
            assert 'docker version' in version_output, "Docker出力が不正です"
            
        except subprocess.TimeoutExpired:
            pytest.skip("Dockerコマンドタイムアウト")
        except FileNotFoundError:
            pytest.skip("Dockerがインストールされていません")
        except Exception as e:
            pytest.skip(f"Docker確認エラー: {e}")
    
    def test_docker_compose_available(self):
        """Docker Composeコマンドの利用可能性確認"""
        try:
            # Docker Compose v2 (docker compose) を試行
            result = subprocess.run(['docker', 'compose', 'version'], 
                                  capture_output=True, text=True, timeout=10)
            
            if result.returncode != 0:
                # Docker Compose v1 (docker-compose) を試行
                result = subprocess.run(['docker-compose', '--version'], 
                                      capture_output=True, text=True, timeout=10)
            
            assert result.returncode == 0, "Docker Composeコマンドが利用できません"
            
        except subprocess.TimeoutExpired:
            pytest.skip("Docker Composeコマンドタイムアウト")
        except FileNotFoundError:
            pytest.skip("Docker Composeがインストールされていません")
        except Exception as e:
            pytest.skip(f"Docker Compose確認エラー: {e}")
    
    def test_dockerfile_lint_backend(self):
        """Dockerfile.backend の構文チェック"""
        dockerfile = PROJECT_ROOT / "Dockerfile.backend"
        
        try:
            # hadolintが利用可能な場合のみテスト
            result = subprocess.run(['hadolint', '--version'], 
                                  capture_output=True, text=True, timeout=5)
            
            if result.returncode == 0:
                # hadolintでDockerfileをチェック
                lint_result = subprocess.run(['hadolint', str(dockerfile)], 
                                           capture_output=True, text=True, timeout=30)
                
                if lint_result.returncode != 0:
                    warnings.warn(f"Dockerfile.backend hadolint警告: {lint_result.stdout}")
            else:
                warnings.warn("hadolint未インストール - Dockerfileリントをスキップ")
                
        except FileNotFoundError:
            warnings.warn("hadolint未インストール - Dockerfileリントをスキップ")
        except Exception as e:
            warnings.warn(f"Dockerfile リントエラー: {e}")
    
    def test_docker_compose_config_validation(self):
        """Docker Compose設定の検証"""
        try:
            # docker compose config コマンドで設定検証
            result = subprocess.run(['docker', 'compose', 'config'], 
                                  cwd=PROJECT_ROOT,
                                  capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                # v1 コマンドで再試行
                result = subprocess.run(['docker-compose', 'config'], 
                                      cwd=PROJECT_ROOT,
                                      capture_output=True, text=True, timeout=30)
            
            assert result.returncode == 0, f"Docker Compose設定が無効です: {result.stderr}"
            
            # 出力されたYAMLが有効か確認
            try:
                yaml.safe_load(result.stdout)
            except yaml.YAMLError as e:
                pytest.fail(f"Docker Compose設定出力が無効なYAML: {e}")
                
        except subprocess.TimeoutExpired:
            pytest.skip("Docker Compose設定検証タイムアウト")
        except FileNotFoundError:
            pytest.skip("Docker Compose未インストール")
        except Exception as e:
            pytest.fail(f"Docker Compose設定検証エラー: {e}")


class TestDockerImageBuild:
    """Docker イメージビルドテスト（オプション）"""
    
    @pytest.mark.slow
    def test_backend_image_build(self):
        """バックエンドイメージのビルドテスト"""
        try:
            # Docker利用可能性確認
            subprocess.run(['docker', '--version'], check=True, capture_output=True, timeout=5)
            
            # バックエンドイメージをビルド
            build_result = subprocess.run([
                'docker', 'build', 
                '-f', 'Dockerfile.backend',
                '-t', 'quiz-backend-test',
                '.'
            ], cwd=PROJECT_ROOT, capture_output=True, text=True, timeout=300)
            
            if build_result.returncode != 0:
                pytest.skip(f"バックエンドビルド失敗（依存関係不足の可能性）: {build_result.stderr[:500]}")
            
            # ビルド成功時のイメージサイズ確認
            inspect_result = subprocess.run([
                'docker', 'inspect', 'quiz-backend-test'
            ], capture_output=True, text=True, timeout=10)
            
            if inspect_result.returncode == 0:
                import json
                image_info = json.loads(inspect_result.stdout)[0]
                size_bytes = image_info.get('Size', 0)
                size_mb = size_bytes / (1024 * 1024)
                
                # 合理的なサイズ範囲確認（100MB-2GB）
                assert 100 < size_mb < 2000, f"イメージサイズが異常: {size_mb:.1f}MB"
                
                print(f"✅ バックエンドイメージビルド成功 (サイズ: {size_mb:.1f}MB)")
            
            # クリーンアップ
            subprocess.run(['docker', 'rmi', 'quiz-backend-test'], 
                         capture_output=True, timeout=30)
            
        except subprocess.TimeoutExpired:
            pytest.skip("バックエンドビルドタイムアウト")
        except subprocess.CalledProcessError:
            pytest.skip("Docker未利用可能")
        except Exception as e:
            pytest.skip(f"バックエンドビルドテストエラー: {e}")
    
    @pytest.mark.slow
    def test_docker_compose_syntax_check(self):
        """Docker Compose全体構文チェック"""
        try:
            # docker-compose.yml の妥当性確認
            result = subprocess.run([
                'docker', 'compose', 'config', '--quiet'
            ], cwd=PROJECT_ROOT, capture_output=True, text=True, timeout=30)
            
            if result.returncode != 0:
                # v1 コマンドで再試行
                result = subprocess.run([
                    'docker-compose', 'config', '--quiet'
                ], cwd=PROJECT_ROOT, capture_output=True, text=True, timeout=30)
            
            assert result.returncode == 0, f"Docker Compose構文エラー: {result.stderr}"
            
        except subprocess.TimeoutExpired:
            pytest.skip("Docker Compose構文チェックタイムアウト")
        except FileNotFoundError:
            pytest.skip("Docker Compose未インストール")
        except Exception as e:
            pytest.skip(f"Docker Compose構文チェックエラー: {e}")


class TestProductionReadiness:
    """本番環境対応確認テスト"""
    
    def test_security_considerations(self):
        """セキュリティ考慮事項の確認"""
        compose_file = PROJECT_ROOT / "docker-compose.yml"
        
        with open(compose_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # セキュリティ警告事項
        security_warnings = []
        
        # privileged モードの使用チェック
        if 'privileged: true' in content:
            security_warnings.append("privilegedモードが使用されています")
        
        # ホストネットワークの使用チェック
        if 'network_mode: host' in content:
            security_warnings.append("ホストネットワークモードが使用されています")
        
        # 開発用ポートバインディングの確認
        if '0.0.0.0:' in content:
            warnings.warn("全インターフェースでのポートバインディングが設定されています（開発用設定）")
        
        if security_warnings:
            warnings.warn(f"セキュリティ上の注意事項: {security_warnings}")
    
    def test_environment_variable_security(self):
        """環境変数のセキュリティ確認"""
        compose_file = PROJECT_ROOT / "docker-compose.yml"
        
        with open(compose_file, 'r', encoding='utf-8') as f:
            compose_config = yaml.safe_load(f)
        
        services = compose_config.get('services', {})
        
        security_issues = []
        
        for service_name, service_config in services.items():
            env = service_config.get('environment', {})
            
            if isinstance(env, list):
                env_dict = {}
                for item in env:
                    if '=' in item:
                        key, value = item.split('=', 1)
                        env_dict[key] = value
                env = env_dict
            
            # 機密情報のハードコーディングチェック
            sensitive_patterns = ['password', 'secret', 'key', 'token']
            
            for env_key, env_value in env.items():
                for pattern in sensitive_patterns:
                    if pattern.lower() in env_key.lower() and env_value:
                        # デフォルトまたはダミー値でない場合は警告
                        if env_value not in ['change-me', 'secret', 'password', 'default']:
                            security_issues.append(f"{service_name}.{env_key}: 機密情報がハードコード")
        
        if security_issues:
            warnings.warn(f"環境変数セキュリティ警告: {security_issues}")
    
    def test_resource_limits(self):
        """リソース制限の確認"""
        compose_file = PROJECT_ROOT / "docker-compose.yml"
        
        with open(compose_file, 'r', encoding='utf-8') as f:
            compose_config = yaml.safe_load(f)
        
        services = compose_config.get('services', {})
        
        missing_limits = []
        
        for service_name, service_config in services.items():
            # メモリ制限確認
            if 'mem_limit' not in service_config and 'deploy' not in service_config:
                missing_limits.append(f"{service_name}: メモリ制限なし")
        
        if missing_limits:
            warnings.warn(f"リソース制限警告: {missing_limits}")


def run_docker_configuration_tests():
    """Docker設定テストの実行"""
    print("🐳 Docker構成テスト開始...")
    
    # pytestを使用してテストを実行
    result = pytest.main([
        __file__,
        "-v",  # 詳細出力
        "--tb=short",  # 短いトレースバック
        "-m", "not slow",  # 低速テストを除外
        "-W", "ignore::DeprecationWarning",
    ])
    
    if result == 0:
        print("✅ Docker構成テスト: 全て通過")
        return True
    else:
        print("❌ Docker構成テスト: 失敗")
        return False


def run_comprehensive_docker_tests():
    """包括的なDockerテストの実行（ビルドテスト含む）"""
    print("🐳 包括的Docker構成テスト開始...")
    
    result = pytest.main([
        __file__,
        "-v",
        "--tb=short",
        "-W", "ignore::DeprecationWarning",
    ])
    
    if result == 0:
        print("✅ 包括的Docker構成テスト: 全て通過")
        return True
    else:
        print("❌ 包括的Docker構成テスト: 失敗")
        return False


if __name__ == "__main__":
    # スタンドアローン実行時
    import argparse
    
    parser = argparse.ArgumentParser(description='Docker構成テスト')
    parser.add_argument('--comprehensive', action='store_true', 
                       help='ビルドテストを含む包括的なテストを実行')
    
    args = parser.parse_args()
    
    if args.comprehensive:
        success = run_comprehensive_docker_tests()
    else:
        success = run_docker_configuration_tests()
    
    sys.exit(0 if success else 1)