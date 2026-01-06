import subprocess
import os
import sys
import json

def run_murphysec(
    path: str = ".",
    token: str = ""
):
    """
    Run murphysec Supply Chain Security Scanner.
    
    Args:
        path: Path to the project to scan (mounted into container).
        token: Murphysec API Token (optional, for cloud features).
    """
    # Murphysec image: murphysec/murphysec
    image = "murphysec/murphysec:latest"
    job_id = os.environ.get("WM_JOB_ID", "local_test_murphysec")
    
    # We'll map the current dir (or a child) to /proj
    abs_path = os.path.abspath(path)
    
    cmd = [
        "docker", "run", "--rm", "--name", job_id,
        "-v", f"{abs_path}:/proj",
        "-e", f"MURPHYSEC_TOKEN={token}",
        image,
        "scan", "/proj", "--format", "json"
    ]
    
    print(f"DEBUG: Running murphysec scan on {path}...", file=sys.stderr, flush=True)
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0 and not result.stdout:
             return {"error": "Murphysec failed", "details": result.stderr}
             
        try:
             json_out = json.loads(result.stdout)
             return json_out
        except:
             return {"raw_output": result.stdout, "details": result.stderr}
             
    except Exception as e:
        return {"error": str(e)}

def main(path: str = "."):
    print(json.dumps(run_murphysec(path), indent=2), flush=True)

if __name__ == "__main__":
    main()
