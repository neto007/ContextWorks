import subprocess
import os
import sys
import json

def run_ehole(
    target: str = ""
):
    """
    Run EHole (Fingerprint Scanner).
    
    Args:
        target: Target URL or file.
    """
    image = "golang:alpine"
    job_id = os.environ.get("WM_JOB_ID", "local_test_ehole")
    
    setup_and_run = (
        "apk add --no-cache git >/dev/null && "
        "git clone https://github.com/EdgeSecurityTeam/EHole.git /app >/dev/null 2>&1 && "
        "cd /app && "
        "go build -o ehole main.go >/dev/null 2>&1 && "
        f"./ehole finger -u {target}"
    )
    
    cmd = [
        "docker", "run", "--rm", "--name", job_id, image, "sh", "-c", setup_and_run
    ]
    
    print(f"DEBUG: Running EHole finger scan on {target}...", file=sys.stderr, flush=True)
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "success": result.returncode == 0
        }
    except Exception as e:
        return {"error": str(e)}

def main(target: str = "http://example.com"):
    print(json.dumps(run_ehole(target), indent=2), flush=True)

if __name__ == "__main__":
    main()
