import subprocess
import os
import sys
import json

def run_ladongo(
    target: str = "",
    scan_type: str = "OnlinePC"
):
    """
    Run LadonGo (Intranet Scan Tool).
    
    Args:
        target: Target IP/Network.
        scan_type: Type of scan (OnlinePC, PortScan, etc.).
    """
    image = "golang:alpine"
    job_id = os.environ.get("WM_JOB_ID", "local_test_ladongo")
    
    setup_and_run = (
        "apk add --no-cache git >/dev/null && "
        "git clone https://github.com/k8gege/LadonGo.git /app >/dev/null 2>&1 && "
        "cd /app && "
        "go build -o LadonGo main.go >/dev/null 2>&1 && "
        f"./LadonGo {target} {scan_type}"
    )
    
    cmd = [
        "docker", "run", "--rm", "--name", job_id, image, "sh", "-c", setup_and_run
    ]
    
    print(f"DEBUG: Running LadonGo {scan_type} on {target}...", file=sys.stderr, flush=True)
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "success": result.returncode == 0
        }
    except Exception as e:
        return {"error": str(e)}

def main(target: str = "192.168.1.1", scan_type: str = "OnlinePC"):
    print(json.dumps(run_ladongo(target, scan_type), indent=2), flush=True)

if __name__ == "__main__":
    main()
