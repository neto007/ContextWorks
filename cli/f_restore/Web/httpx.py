import subprocess
import os
import sys
import json
import urllib.parse

def run_httpx(target: str):
    image = "projectdiscovery/httpx:latest"
    job_id = os.environ.get("WM_JOB_ID", "local_test_httpx")

    # Sanitize target logic
    if "://" not in target:
         target = f"https://{target}"

    # Pull image
    print(f"DEBUG: Pulling image {image}...", file=sys.stderr, flush=True)
    subprocess.run(["docker", "pull", image], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    # Construct command
    # -u target : Target URL
    # -json : JSON output to stdout/file
    # -o /tmp/httpx_out.json : Output file
    # -verbose : Show more info on stdout? 
    # httpx usually prints found hosts to stdout.
    
    cmd = [
        "docker", "run",
        "--name", job_id,
        image,
        "-u", target,
        "-json", 
        "-o", "/tmp/httpx_out.json",
        "-verbose" 
    ]
    
    print(f"DEBUG: Running command: {' '.join(cmd)}", file=sys.stderr, flush=True)
    
    try:
        # Popen to stream output
        process = subprocess.Popen(
            cmd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, 
            text=True, 
            bufsize=1
        )
        
        # Stream stdout
        while True:
            line = process.stdout.readline()
            if not line and process.poll() is not None:
                break
            if line:
                line = line.strip()
                print(f"HTTPX: {line}", file=sys.stderr, flush=True)
                
        # Wait for finish
        process.wait()
        
        if process.returncode != 0:
             _, stderr_output = process.communicate()
             print(f"DEBUG: Process stderr: {stderr_output}", file=sys.stderr, flush=True)

        # Read the JSON file from the container
        # httpx outputs JSON lines (NDJSON)
        local_json_path = f"/tmp/{job_id}_httpx.json"
        
        cp_cmd = ["docker", "cp", f"{job_id}:/tmp/httpx_out.json", local_json_path]
        cp_result = subprocess.run(cp_cmd, capture_output=True, text=True)
        
        if cp_result.returncode != 0:
             return {"error": "Could not copy output file", "details": cp_result.stderr}
             
        results = []
        try:
            with open(local_json_path, "r") as f:
                for line in f:
                    if line.strip():
                        try:
                            results.append(json.loads(line))
                        except:
                            pass
            os.remove(local_json_path)
            
            return {"target": target, "findings": results}
        except Exception as e:
            return {"error": f"Failed to read/parse output: {str(e)}"}

    except Exception as e:
        return {"error": str(e)}

def main(target: str = "https://scanme.nmap.org"):
    print(f"DEBUG: Scanning target: {target}", file=sys.stderr, flush=True)
    result = run_httpx(target)
    return result

if __name__ == "__main__":
    target_arg = sys.argv[1] if len(sys.argv) > 1 else "https://scanme.nmap.org"
    main(target_arg)
