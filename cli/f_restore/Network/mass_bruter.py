import subprocess
import os
import sys
import json

def run_mass_bruter(
    target: str = "",
    wordlist: str = ""
):
    """
    Run mass-bruter.
    
    Args:
        target: Target IP/Host.
        wordlist: Wordlist content (optional).
    """
    image = "python:3-alpine"
    job_id = os.environ.get("WM_JOB_ID", "local_test_mass_bruter")
    
    setup_and_run = (
        "apk add --no-cache git >/dev/null && "
        "git clone https://github.com/opabravo/mass-bruter.git /app >/dev/null && "
        "cd /app && "
        "pip install -r requirements.txt >/dev/null 2>&1 && "
        f"python mass-bruter.py -t {target}"
    )
    
    cmd = [
        "docker", "run", "--rm", "--name", job_id, image, "sh", "-c", setup_and_run
    ]
    
    print(f"DEBUG: Running mass-bruter on {target}...", file=sys.stderr, flush=True)
    
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
    print(json.dumps(run_mass_bruter(target), indent=2), flush=True)

if __name__ == "__main__":
    main()
