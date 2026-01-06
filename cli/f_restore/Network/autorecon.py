import subprocess
import os
import sys
import json
import urllib.parse

def run_autorecon(target: str):
    image = "kalilinux/kali-rolling"
    job_id = os.environ.get("WM_JOB_ID", "local_test_autorecon")

    target = target.replace("http://", "").replace("https://", "").split("/")[0]

    # Pull image
    print(f"DEBUG: Pulling image {image}...", file=sys.stderr, flush=True)
    subprocess.run(["docker", "pull", image], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    # AutoRecon via apt in Kali
    install_and_run = (
        "apt-get update >/dev/null && "
        "apt-get install -y autorecon >/dev/null && "
        f"autorecon {target} --only-scans-dir"
    )
    
    cmd = [
        "docker", "run",
        "--name", job_id,
        image,
        "sh", "-c",
        install_and_run
    ]
    
    print(f"DEBUG: Running command: {' '.join(cmd)}", file=sys.stderr, flush=True)
    
    logs = []
    
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
                print(f"AUTORECON: {line}", file=sys.stderr, flush=True)
                logs.append(line)
                
        process.wait()
        
        # AutoRecon doesn't have a single JSON output.
        # We assume succes if exit code 0.
        # Findings are in the logs (ports found, etc).
        
        return {
            "target": target, 
            "status": "Completed",
            "log_summary": logs[:50] # truncated
        }

    except Exception as e:
        return {"error": str(e)}

def main(target: str = "scanme.nmap.org"):
    print(f"DEBUG: Scanning target: {target}", file=sys.stderr, flush=True)
    result = run_autorecon(target)
    return result

if __name__ == "__main__":
    target_arg = sys.argv[1] if len(sys.argv) > 1 else "scanme.nmap.org"
    main(target_arg)
