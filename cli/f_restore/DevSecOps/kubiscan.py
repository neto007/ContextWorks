import subprocess
import os
import sys
import json

def run_kubiscan(
    kubeconfig_path: str = "~/.kube/config"
):
    """
    Run KubiScan (Kubernetes Permission Scanner).
    
    Args:
        kubeconfig_path: Path to kubeconfig for the target cluster.
    """
    image = "python:3-alpine"
    job_id = os.environ.get("WM_JOB_ID", "local_test_kubiscan")
    
    # Kubiscan needs to be cloned and installed.
    # It also needs access to the cluster.
    
    setup_and_run = (
        "apk add --no-cache git >/dev/null && "
        "git clone https://github.com/cyberark/KubiScan.git /app >/dev/null 2>&1 && "
        "cd /app && "
        "pip install -r requirements.txt >/dev/null 2>&1 && "
        "python KubiScan.py -h" # Just help for now as it needs a live cluster
    )
    
    cmd = [
        "docker", "run", "--rm", "--name", job_id,
        "-v", f"{os.path.expanduser(kubeconfig_path)}:/root/.kube/config",
        image, "sh", "-c", setup_and_run
    ]
    
    print(f"DEBUG: Running KubiScan setup and test...", file=sys.stderr, flush=True)
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "success": result.returncode == 0
        }
    except Exception as e:
        return {"error": str(e)}

def main(kubeconfig_path: str = "~/.kube/config"):
    print(json.dumps(run_kubiscan(kubeconfig_path), indent=2), flush=True)

if __name__ == "__main__":
    main()
