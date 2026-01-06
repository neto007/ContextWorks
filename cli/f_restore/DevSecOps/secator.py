import subprocess
import os
import sys
import json

def run_secator(
    cmd_args: str = "--help"
):
    """
    Run secator (Pentest Task Runner).
    
    Args:
        cmd_args: Arguments for secator.
    """
    image = "python:3-alpine"
    job_id = os.environ.get("WM_JOB_ID", "local_test_secator")
    
    setup_and_run = (
        "pip install secator >/dev/null 2>&1 && "
        f"secator {cmd_args}"
    )
    
    cmd = [
        "docker", "run", "--rm", "--name", job_id, image, "sh", "-c", setup_and_run
    ]
    
    print(f"DEBUG: Running secator {cmd_args}...", file=sys.stderr, flush=True)
    
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
    print(json.dumps(run_secator(cmd_args), indent=2), flush=True)

if __name__ == "__main__":
    main()
