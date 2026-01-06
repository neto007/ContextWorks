import subprocess
import os
import sys
import json

def run_nacs(
    target: str = ""
):
    """
    Run nacs (Internal Network Scanner).
    
    Args:
        target: Target IP/Network.
    """
    image = "golang:alpine"
    job_id = os.environ.get("WM_JOB_ID", "local_test_nacs")
    
    setup_and_run = (
        "apk add --no-cache git >/dev/null && "
        "git clone https://github.com/u21h2/nacs.git /app >/dev/null 2>&1 && "
        "cd /app && "
        "go build -o nacs main.go >/dev/null 2>&1 && "
        f"./nacs -h {target}"
    )
    
    cmd = [
        "docker", "run", "--rm", "--name", job_id, image, "sh", "-c", setup_and_run
    ]
    
    print(f"DEBUG: Running nacs on {target}...", file=sys.stderr, flush=True)
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "success": result.returncode == 0
        }
    except Exception as e:
        return {"error": str(e)}

def main(target: str = "127.0.0.1"):
    print(json.dumps(run_nacs(target), indent=2), flush=True)

if __name__ == "__main__":
    main()
