import subprocess
import os
import sys
import json
import urllib.parse
import re

def run_fierce(target: str):
    image = "python:alpine"
    job_id = os.environ.get("WM_JOB_ID", "local_test_fierce")

    target = target.replace("http://", "").replace("https://", "").split("/")[0]

    # Pull image
    print(f"DEBUG: Pulling image {image}...", file=sys.stderr, flush=True)
    subprocess.run(["docker", "pull", image], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    install_and_run = (
        "pip install fierce >/dev/null && "
        f"fierce --domain {target} --connect"
    )
    # Fierce output is text. "Found: sub.example.com (1.2.3.4)"
    
    cmd = [
        "docker", "run",
        "--name", job_id,
        image,
        "sh", "-c",
        install_and_run
    ]
    
    print(f"DEBUG: Running command: {' '.join(cmd)}", file=sys.stderr, flush=True)
    
    subdomains = []
    
    try:
        process = subprocess.Popen(
            cmd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, 
            text=True, 
            bufsize=1
        )
        
        # Regex: Found: sub.domain.com (IP)
        found_pattern = re.compile(r"Found:\s+([a-zA-Z0-9.-]+)\s+\((.+)\)")
        
        while True:
            line = process.stdout.readline()
            if not line and process.poll() is not None:
                break
            if line:
                line = line.strip()
                print(f"FIERCE: {line}", file=sys.stderr, flush=True)
                
                m = found_pattern.search(line)
                if m:
                    subdomains.append({"host": m.group(1), "ip": m.group(2)})
                
        process.wait()

        if process.returncode != 0:
             _, stderr_output = process.communicate()
             print(f"DEBUG: Process stderr: {stderr_output}", file=sys.stderr, flush=True)
        
        return {
            "target": target, 
            "subdomains": subdomains
        }

    except Exception as e:
        return {"error": str(e)}

def main(target: str = "scanme.nmap.org"):
    print(f"DEBUG: Scanning target: {target}", file=sys.stderr, flush=True)
    result = run_fierce(target)
    return result

if __name__ == "__main__":
    target_arg = sys.argv[1] if len(sys.argv) > 1 else "scanme.nmap.org"
    main(target_arg)
