import subprocess
import os
import sys
import json

def run_proxy_scanner(
    target: str = ""
):
    """
    Run MisConfig_HTTP_Proxy_Scanner.
    
    Args:
        target: Target IP/Host to scan for proxy misconfigs.
    """
    image = "python:3-alpine"
    job_id = os.environ.get("WM_JOB_ID", "local_test_proxy_scanner")
    
    setup_and_run = (
        "apk add --no-cache git >/dev/null && "
        "git clone https://github.com/lijiejie/MisConfig_HTTP_Proxy_Scanner.git /app >/dev/null && "
        "cd /app && "
        f"python ProxyScanner.py --scan {target}"
    )
    
    cmd = [
        "docker", "run", "--rm", "--name", job_id, image, "sh", "-c", setup_and_run
    ]
    
    print(f"DEBUG: Running ProxyScanner on {target}...", file=sys.stderr, flush=True)
    
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
    print(json.dumps(run_proxy_scanner(target), indent=2), flush=True)

if __name__ == "__main__":
    main()
