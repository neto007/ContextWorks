import subprocess
import os
import sys
import json

def run_dockerscan(
    scan_type: str = "image",
    target: str = ""
):
    """
    Run dockerscan.
    
    Args:
        scan_type: Type of scan (image, scan).
        target: Target image/info.
    """
    image = "python:3-alpine"
    job_id = os.environ.get("WM_JOB_ID", "local_test_dockerscan")
    
    # Install dockerscan via pip
    setup_and_run = (
        "pip install dockerscan >/dev/null 2>&1 && "
        f"dockerscan {scan_type} {target}"
    )
    
    cmd = [
        "docker", "run", "--rm", "--name", job_id,
        image, "sh", "-c", setup_and_run
    ]
    
    print(f"DEBUG: Running dockerscan {scan_type} {target}...", file=sys.stderr, flush=True)
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "success": result.returncode == 0
        }
    except Exception as e:
        return {"error": str(e)}

def main(scan_type="--help", target=""):
    print(json.dumps(run_dockerscan(scan_type, target), indent=2), flush=True)

if __name__ == "__main__":
    main()
