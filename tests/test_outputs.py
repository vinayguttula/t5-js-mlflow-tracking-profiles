import os
import json
import subprocess
import time
import pytest
import urllib.request
from datetime import datetime

TARGET_DIR_DEV = "/tmp/mlflow-output-dev"
TARGET_DIR_PROD = "/tmp/mlflow-output-prod"
TARGET_DIR_RETENTION = "/tmp/mlflow-output-retention"
TARGET_DIR_DYNAMIC = "/tmp/mlflow-output-dynamic"

ALL_DIRS = [TARGET_DIR_DEV, TARGET_DIR_PROD, TARGET_DIR_RETENTION, TARGET_DIR_DYNAMIC]

API_DIR = "/app/api" if os.path.exists("/app/api") else "/app/environment/api"
CLI_PATH = "/app/cli/index.js" if os.path.exists("/app/cli/index.js") else "/app/environment/cli/index.js"

API_URL = "http://127.0.0.1:3000"

@pytest.fixture(scope="session", autouse=True)
def setup_api_and_run_cli():
    """Start the Express API and run the CLI tool before testing."""
    for d in ALL_DIRS:
        os.makedirs(d, exist_ok=True)
    
    # Kill any existing processes on port 3000 to prevent conflicts
    subprocess.run("kill $(lsof -t -i :3000) 2>/dev/null || true", shell=True)
    
    env = os.environ.copy()
    env["VERIFIER_MODE"] = "1"

    api_process = subprocess.Popen(
        ["npm", "start"], 
        cwd=API_DIR, 
        stdout=subprocess.DEVNULL, 
        stderr=subprocess.DEVNULL,
        env=env
    )
    
    time.sleep(2)
    
    # Inject a dynamic profile
    dynamic_payload = json.dumps({
        "policy": {
            "profileId": "dynamic-test-123",
            "maxRetentionDays": 45,
            "allowSqlite": True,
            "requireAuth": True,
            "environmentVars": {
                "MLFLOW_TEST_VAR_1": "123",
                "MLFLOW_TEST_VAR_2": "abc"
            }
        },
        "portAssignment": {
            "assignedPort": 5100,
            "portRange": [5000, 5200]
        }
    }).encode('utf-8')
    req = urllib.request.Request(f"{API_URL}/api/__test/inject", data=dynamic_payload, headers={'Content-Type': 'application/json'})
    urllib.request.urlopen(req)

    # Run the CLI for different profiles
    subprocess.run([CLI_PATH, "-p", "dev-local", "-d", TARGET_DIR_DEV, "-u", API_URL], capture_output=True)
    subprocess.run([CLI_PATH, "-p", "prod-secure", "-d", TARGET_DIR_PROD, "-u", API_URL], capture_output=True)
    subprocess.run([CLI_PATH, "-p", "test-max-retention", "-d", TARGET_DIR_RETENTION, "-u", API_URL], capture_output=True)
    subprocess.run([CLI_PATH, "-p", "dynamic-test-123", "-d", TARGET_DIR_DYNAMIC, "-u", API_URL], capture_output=True)
    
    yield
    
    api_process.terminate()

def test_directories_created():
    """Verify that the artifacts directory is created for all profiles."""
    for d in ALL_DIRS:
        assert os.path.isdir(os.path.join(d, "artifacts")), f"Artifacts directory not found in {d}"

def test_mlflow_env_sh_sqlite():
    """Verify the mlflow-env.sh file contains the correct exports for sqlite."""
    env_file = os.path.join(TARGET_DIR_DEV, "mlflow-env.sh")
    assert os.path.isfile(env_file), "mlflow-env.sh not found"
    
    with open(env_file, 'r') as f:
        content = f.read()
        
    assert 'export MLFLOW_TRACKING_INSECURE_TLS="true"' in content
    expected_uri = f'export MLFLOW_TRACKING_URI="sqlite://{TARGET_DIR_DEV}/mlflow.db"'
    assert expected_uri in content

def test_mlflow_env_sh_http():
    """Verify the mlflow-env.sh file contains the correct exports for HTTP URIs."""
    env_file = os.path.join(TARGET_DIR_PROD, "mlflow-env.sh")
    assert os.path.isfile(env_file), "mlflow-env.sh not found"
    
    with open(env_file, 'r') as f:
        content = f.read()
        
    assert 'export MLFLOW_TRACKING_INSECURE_TLS="false"' in content
    assert 'export MLFLOW_TRACKING_URI="http://127.0.0.1:5443"' in content

def test_dynamic_profile_export_all_vars():
    """Verify that an arbitrary set of multiple environment vars and SQLite URI are exported from API injection."""
    env_file = os.path.join(TARGET_DIR_DYNAMIC, "mlflow-env.sh")
    assert os.path.isfile(env_file), "Dynamic profile mlflow-env.sh not found (this fails if the CLI hardcoded the profile instead of fetching the API)"

    with open(env_file, 'r') as f:
        content = f.read()
    
    assert 'export MLFLOW_TEST_VAR_1="123"' in content
    assert 'export MLFLOW_TEST_VAR_2="abc"' in content
    expected_uri = f'export MLFLOW_TRACKING_URI="sqlite://{TARGET_DIR_DYNAMIC}/mlflow.db"'
    assert expected_uri in content

def test_systemd_unit():
    """Verify the mlflow-tracker.service file has correct systemd configuration for dev-local."""
    service_file = os.path.join(TARGET_DIR_DEV, "mlflow-tracker.service")
    assert os.path.isfile(service_file), "mlflow-tracker.service not found"
    
    with open(service_file, 'r') as f:
        content = f.read()
        
    assert f"--default-artifact-root {TARGET_DIR_DEV}/artifacts" in content
    assert f"EnvironmentFile={TARGET_DIR_DEV}/mlflow-env.sh" in content
    assert "ExecStart=/usr/local/bin/mlflow server" in content
    assert "--port 5000" in content

def test_systemd_unit_prod():
    """Verify the prod-secure systemd unit uses port 5443."""
    service_file = os.path.join(TARGET_DIR_PROD, "mlflow-tracker.service")
    assert os.path.isfile(service_file), "prod-secure mlflow-tracker.service not found"
    
    with open(service_file, 'r') as f:
        content = f.read()
        
    assert "--port 5443" in content
    assert f"--default-artifact-root {TARGET_DIR_PROD}/artifacts" in content
    assert f"EnvironmentFile={TARGET_DIR_PROD}/mlflow-env.sh" in content

def test_systemd_unit_dynamic():
    """Verify the dynamically injected profile systemd unit uses port 5100."""
    service_file = os.path.join(TARGET_DIR_DYNAMIC, "mlflow-tracker.service")
    assert os.path.isfile(service_file), "dynamic profile mlflow-tracker.service not found"
    
    with open(service_file, 'r') as f:
        content = f.read()
        
    assert "--port 5100" in content
    assert f"--default-artifact-root {TARGET_DIR_DYNAMIC}/artifacts" in content
    assert f"EnvironmentFile={TARGET_DIR_DYNAMIC}/mlflow-env.sh" in content

def test_audit_manifest():
    """Verify the audit-manifest.json contains required fields and correct data."""
    manifest_file = os.path.join(TARGET_DIR_DEV, "audit-manifest.json")
    assert os.path.isfile(manifest_file), "audit-manifest.json not found"
    
    with open(manifest_file, 'r') as f:
        data = json.load(f)
        
    assert data.get("profileId") == "dev-local"
    assert data.get("port") == 5000
    assert data.get("retentionDays") == 30
    
    ts = data.get("timestamp")
    assert ts is not None
    datetime.fromisoformat(ts.replace("Z", "+00:00"))  # validates ISO string format

def test_max_retention_cap():
    """Verify the CLI caps retention days at 3650."""
    manifest_file = os.path.join(TARGET_DIR_RETENTION, "audit-manifest.json")
    assert os.path.isfile(manifest_file), "audit-manifest.json not found"
    
    with open(manifest_file, 'r') as f:
        data = json.load(f)
        
    assert data.get("profileId") == "test-max-retention"
    assert data.get("retentionDays") == 3650, "Retention days exceeded the maximum global cap"

def test_cli_handles_invalid_profile():
    """Verify the CLI handles invalid profiles gracefully."""
    cli_process = subprocess.run(
        [CLI_PATH, "-p", "invalid-profile", "-d", "/tmp/invalid", "-u", API_URL],
        capture_output=True,
        text=True
    )
    assert cli_process.returncode != 0, "CLI should fail on invalid profile"
    output = cli_process.stdout + cli_process.stderr
    assert len(output.strip()) > 0, "CLI should print an error message on invalid profile"

def test_cli_handles_invalid_port():
    """Verify the CLI errors out when the assigned port is not in the port range."""
    cli_process = subprocess.run(
        [CLI_PATH, "-p", "test-invalid-port", "-d", "/tmp/invalid-port-dir", "-u", API_URL],
        capture_output=True,
        text=True
    )
    assert cli_process.returncode != 0, "CLI should fail when port is outside allowed range"
    output = cli_process.stdout + cli_process.stderr
    assert len(output.strip()) > 0, "CLI should print an error message on invalid port"
