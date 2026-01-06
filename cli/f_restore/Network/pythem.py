import subprocess
import os
import sys
import json

def run_pythem(
    cmd_args: str = "--help"
):
    """
    Run PytheM Pentest Framework.
    
    Args:
        cmd_args: Arguments for PytheM.
    """
    image = "python:3-alpine"
    job_id = os.environ.get("WM_JOB_ID", "local_test_pythem")
    
    setup_and_run = (
        "apk add --no-cache git build-base >/dev/null && "
        "git clone https://github.com/m4n3dw0lf/PytheM.git /app >/dev/null && "
        "cd /app && "
        "pip install -r requirements.txt >/dev/null 2>&1 && "
        f"python pythem.py {cmd_args}"
    )
    
    cmd = [
        "docker", "run", "--rm", "--name", job_id, image, "sh", "-c", setup_and_run
    ]
    
    print(f"DEBUG: Running PytheM {cmd_args}...", file=sys.stderr, flush=True)
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "success": result.returncode == 0
        }
    except Exception as e:
        return {"error": str(e)}

def main(cmd_args: str = "--help"):
    print(json.dumps(run_pythem(cmd_args), indent=2), flush=True)

if __name__ == "__main__":
    main()
