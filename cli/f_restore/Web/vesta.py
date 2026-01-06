import subprocess
import os
import sys
import json

def run_vesta(
    target: str = ""
):
    """
    Run Vesta (Cloud/Container Scanner).
    
    Args:
        target: Target to scan.
    """
    image = "python:3-alpine"
    job_id = os.environ.get("WM_JOB_ID", "local_test_vesta")
    
    setup_and_run = (
        "apk add --no-cache git >/dev/null && "
        "git clone https://github.com/kvesta/vesta.git /app >/dev/null && "
        "cd /app && "
        "pip install -r requirements.txt >/dev/null 2>&1 && "
        "python vesta.py --help"
    )
    
    cmd = [
        "docker", "run", "--rm", "--name", job_id, image, "sh", "-c", setup_and_run
    ]
    
    print(f"DEBUG: Running Vesta setup and test...", file=sys.stderr, flush=True)
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "success": result.returncode == 0
        }
    except Exception as e:
        return {"error": str(e)}

def main(target: str = ""):
    print(json.dumps(run_vesta(target), indent=2), flush=True)

if __name__ == "__main__":
    main()
