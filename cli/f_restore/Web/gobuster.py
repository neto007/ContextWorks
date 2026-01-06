import subprocess
import os
import sys
import json
import urllib.parse
import re

def run_gobuster(target: str):
    image = "golang:alpine"
    job_id = os.environ.get("WM_JOB_ID", "local_test_gobuster")

    # Sanitize target logic
    target = target.strip()
    
    # Pull image
    print(f"DEBUG: Pulling image {image}...", file=sys.stderr, flush=True)
    subprocess.run(["docker", "pull", image], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    # Construct command
    # Build from source using Go.
    wordlist_url = "https://raw.githubusercontent.com/danielmiessler/SecLists/master/Discovery/Web-Content/common.txt"
    
    setup_and_run = (
        "apk add --no-cache git wget >/dev/null && "
        "go install github.com/OJ/gobuster/v3@latest >/dev/null && "
        f"wget -qO wordlist.txt {wordlist_url} && "
        f"gobuster dir -u {target} -w wordlist.txt --no-color --no-error"
    )
    
    cmd = [
        "docker", "run",
        "--name", job_id,
        image,
        "sh", "-c",
        setup_and_run
    ]
    
    
    print(f"DEBUG: Running command: {' '.join(cmd)}", file=sys.stderr, flush=True)
    
    try:
        # Use Popen to stream output
        process = subprocess.Popen(
            cmd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, 
            text=True, 
            bufsize=1
        )
        
        results = []
        pattern = re.compile(r"(\S+)\s+\(Status:\s+(\d+)\)\s+\[Size:\s+(\d+)\]")
        
        # Stream stdout
        # Note: streaming regex matching on raw lines
        # We need to read lines as they come
        while True:
            line = process.stdout.readline()
            if not line and process.poll() is not None:
                break
            if line:
                line = line.strip()
                # Print to logs so user sees progress
                print(f"GOBUSTER: {line}", file=sys.stderr, flush=True)
                
                match = pattern.search(line)
                if match:
                    results.append({
                        "path": match.group(1),
                        "status": int(match.group(2)),
                        "size": int(match.group(3)),
                        "raw": line
                    })
        
        # Capture stderr after loop if needed (or in parallel, but stdout loop is main blocker)
        _, stderr_output = process.communicate()
        
        if process.returncode != 0:
             print(f"DEBUG: Process stderr: {stderr_output}", file=sys.stderr, flush=True)
             # Gobuster might return non-zero on some errors, but we might still have results.
             # If completely failed (no findings and error):
             if not results and stderr_output:
                 return {"error": "Gobuster failed", "details": stderr_output}
        
        return {"results": results}

    except Exception as e:
        return {"error": str(e)}

def main(target: str = "https://scanme.nmap.org"):
    print(f"DEBUG: Scanning target: {target}", file=sys.stderr, flush=True)
    result = run_gobuster(target)
    return result

if __name__ == "__main__":
    target_arg = sys.argv[1] if len(sys.argv) > 1 else "https://scanme.nmap.org"
    main(target_arg)
