import subprocess
import os
import sys
import json

def run_grype(
    target: str = "alpine:latest"
):
    """
    Run Grype (Vulnerability Scanner for Images/FS).
    
    Args:
        target: Image name or directory path to scan.
    """
    # Grype image: anchore/grype
    image = "anchore/grype:latest"
    job_id = os.environ.get("WM_JOB_ID", "local_test_grype")
    
    cmd = [
        "docker", "run", "--rm", "--name", job_id,
        "-v", "/var/run/docker.sock:/var/run/docker.sock",
        image,
        target, "-o", "json"
    ]
    
    print(f"DEBUG: Running Grype scan on {target}...", file=sys.stderr, flush=True)
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0 and not result.stdout:
             return {"error": "Grype failed", "details": result.stderr}
             
        try:
             return json.loads(result.stdout)
        except:
             return {"raw_output": result.stdout, "details": result.stderr}
             
    except Exception as e:
        return {"error": str(e)}

def main(target: str = "alpine:latest"):
    print(json.dumps(run_grype(target), indent=2), flush=True)

if __name__ == "__main__":
    main()
