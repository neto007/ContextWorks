import subprocess
import os
import sys
import json
import urllib.parse
import re

def run_masscan(target: str):
    image = "adguard/masscan:edge" # Often lighter/more updated
    job_id = os.environ.get("WM_JOB_ID", "local_test_masscan")

    # Sanitize target (Masscan wants IP or range)
    # If domain, we might need to resolve it first? 
    # Masscan handles IPs best. If domain given, it resolves locally? 
    # Let's try to resolve in python to be safe or rely on masscan.
    # Usually "masscan google.com" works.
    target = target.replace("http://", "").replace("https://", "").split("/")[0]

    # Pull image
    print(f"DEBUG: Pulling image {image}...", file=sys.stderr, flush=True)
    subprocess.run(["docker", "pull", image], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    # Masscan -oJ /tmp/result.json --rate 1000 -p 0-65535 or specific
    # We'll do top ports or user spec?
    # Defaulting to -p1-1000 for speed in demo.
    
    cmd = [
        "docker", "run",
        "--name", job_id,
        "--cap-add=NET_ADMIN", # Critical for raw sockets
        "--cap-add=NET_RAW",
        image,
        target,
        "-p1-1000",
        "--rate=1000",
        "-oJ", "/tmp/masscan.json"
    ]
    
    print(f"DEBUG: Running command: {' '.join(cmd)}", file=sys.stderr, flush=True)
    
    try:
        process = subprocess.Popen(
            cmd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, 
            text=True, 
            bufsize=1
        )
        
        while True:
            line = process.stdout.readline()
            if not line and process.poll() is not None:
                break
            if line:
                line = line.strip()
                print(f"MASSCAN: {line}", file=sys.stderr, flush=True)
                
        process.wait()

        if process.returncode != 0:
             _, stderr_output = process.communicate()
             print(f"DEBUG: Process stderr: {stderr_output}", file=sys.stderr, flush=True)
             
        # Read output
        local_json_path = f"/tmp/{job_id}_masscan.json"
        cp_cmd = ["docker", "cp", f"{job_id}:/tmp/masscan.json", local_json_path]
        cp_result = subprocess.run(cp_cmd, capture_output=True, text=True)
        
        if cp_result.returncode != 0:
             return {"error": "Could not copy output file", "details": cp_result.stderr}
             
        try:
            with open(local_json_path, "r") as f:
                content = f.read()
            os.remove(local_json_path)
            
            # Masscan JSON is usually a list of objects or single object?
            # It usually appends to file? 
            # If standard JSON array, good. If NDJSON, parse lines.
            # Masscan usually outputs a valid JSON Array if finished correctly?
            # Actually masscan -oJ creates an array.
            
            # Note: Masscan output might have trailing comma issue sometimes.
            if content.strip().endswith(",]"):
                 content = content.replace(",]", "]")
            
            return json.loads(content)
        except Exception as e:
            return {"error": f"Failed to parse JSON: {str(e)}", "raw": content if 'content' in locals() else "N/A"}

    except Exception as e:
        return {"error": str(e)}

def main(target: str = "scanme.nmap.org"):
    print(f"DEBUG: Scanning target: {target}", file=sys.stderr, flush=True)
    result = run_masscan(target)
    return result

if __name__ == "__main__":
    target_arg = sys.argv[1] if len(sys.argv) > 1 else "scanme.nmap.org"
    main(target_arg)
