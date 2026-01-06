import subprocess
import os
import sys
import json
import urllib.parse

def run_subfinder(target: str):
    image = "projectdiscovery/subfinder:latest"
    job_id = os.environ.get("WM_JOB_ID", "local_test_subfinder")

    # Sanitize target (Subfinder wants domain, not url, usually)
    # Remove protocol
    target = target.replace("http://", "").replace("https://", "").split("/")[0]

    # Pull image
    print(f"DEBUG: Pulling image {image}...", file=sys.stderr, flush=True)
    subprocess.run(["docker", "pull", image], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    # Subfinder usage: -d domain -json -o file
    cmd = [
        "docker", "run",
        "--name", job_id,
        image,
        "-d", target,
        "-json",
        "-oJ", # or just -o but ensure json format
        "-o", "/tmp/subfinder.json"
    ]
    # Check flags: projectdiscovery usually has -json to stdout OR -o file.
    # If -json is used with -o, does it write json to file? Yes suitable for PD tools.
    
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
                # PD tools stream JSON lines to stdout if -json is set? 
                # Or just hostnames? 
                # If we use -o, stdout usually minimal or same.
                # Let's stream it.
                print(f"SUBFINDER: {line}", file=sys.stderr, flush=True)
                
        process.wait()

        if process.returncode != 0:
             _, stderr_output = process.communicate()
             print(f"DEBUG: Process stderr: {stderr_output}", file=sys.stderr, flush=True)
             
        # Read output
        local_json_path = f"/tmp/{job_id}_subfinder.json"
        cp_cmd = ["docker", "cp", f"{job_id}:/tmp/subfinder.json", local_json_path]
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
            # PD tools format: {"host":"...", "ip":"..."} etc
            return {"target": target, "subdomains": results}
        except Exception as e:
            return {"error": f"Failed to parse JSON: {str(e)}"}

    except Exception as e:
        return {"error": str(e)}

def main(target: str = "scanme.nmap.org"):
    print(f"DEBUG: Scanning target: {target}", file=sys.stderr, flush=True)
    result = run_subfinder(target)
    return result

if __name__ == "__main__":
    target_arg = sys.argv[1] if len(sys.argv) > 1 else "scanme.nmap.org"
    main(target_arg)
