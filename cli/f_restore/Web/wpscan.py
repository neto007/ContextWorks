import subprocess
import os
import sys
import json

def run_wpscan(target: str, api_token: str):
    image = "wpscanteam/wpscan:latest"
    job_id = os.environ.get("WM_JOB_ID", "local_test_wpscan")

    print(f"DEBUG: Pulling image {image}...", file=sys.stderr, flush=True)
    subprocess.run(["docker", "pull", image], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    cmd = [
        "docker", "run",
        "--name", job_id,
        image,
        "--url", target,
        "--format", "json",
    ]
    
    if api_token:
        cmd.extend(["--api-token", api_token])
    else:
        # random user agent often helps
        cmd.extend(["--random-user-agent"])
        
    print(f"DEBUG: Running wpscan...", file=sys.stderr, flush=True)
    
    # We want to capture stdout (JSON) but also stream minimal logs.
    # WPScan sends banner/logs to stderr usually if format is json?
    # Or strict json on stdout.
    
    try:
        process = subprocess.Popen(
            cmd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, 
            text=True, 
            bufsize=1
        )
        
        # Stream stderr (logs)
        # Capture stdout (JSON)
        
        json_buffer = []
        
        while True:
            # Poll both? Or assume stderr usage?
            # readline might block.
            # Simple approach: let it run, capture stdout at end?
            # But we want logs.
            # Read stderr line by line.
            err_line = process.stderr.readline()
            if err_line:
                print(f"WPSCAN: {err_line.strip()}", file=sys.stderr, flush=True)
            
            if not err_line and process.poll() is not None:
                break
                
        # Get rest of output
        stdout, stderr = process.communicate()
        if stderr:
             print(f"WPSCAN: {stderr}", file=sys.stderr, flush=True)
        
        try:
            return json.loads(stdout)
        except:
             return {"error": "Failed to parse JSON", "raw": stdout[:500]}

    except Exception as e:
        print(f"Error running wpscan: {e}", file=sys.stderr, flush=True)
        return {"error": str(e)}
    finally:
        subprocess.run(["docker", "rm", "-f", job_id], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def main(target: str = "https://scanme.nmap.org", api_token: str = ""):
    print(f"DEBUG: Starting WPScan on {target}", file=sys.stderr, flush=True)
    result = run_wpscan(target, api_token)
    return result

if __name__ == "__main__":
    if len(sys.argv) > 1:
        main(sys.argv[1])
    else:
        main()
