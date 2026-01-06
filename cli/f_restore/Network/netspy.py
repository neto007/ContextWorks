import subprocess
import os
import sys
import json

def run_netspy(
    target: str = ""
):
    """
    Run netspy (Network Segment Scanner).
    
    Args:
        target: Target network/IP.
    """
    image = "golang:alpine"
    job_id = os.environ.get("WM_JOB_ID", "local_test_netspy")
    
    setup_and_run = (
        "apk add --no-cache git >/dev/null && "
        "git clone https://github.com/shmilylty/netspy.git /app >/dev/null 2>&1 && "
        "cd /app && "
        "go build -o netspy main.go >/dev/null 2>&1 && "
        f"./netspy {target}"
    )
    
    cmd = [
        "docker", "run", "--rm", "--name", job_id, image, "sh", "-c", setup_and_run
    ]
    
    print(f"DEBUG: Running netspy on {target}...", file=sys.stderr, flush=True)
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "success": result.returncode == 0
        }
    except Exception as e:
        return {"error": str(e)}

def main(target: str = "192.168.0.0/16"):
    print(json.dumps(run_netspy(target), indent=2), flush=True)

if __name__ == "__main__":
    main()
