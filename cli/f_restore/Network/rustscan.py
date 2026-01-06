import subprocess
import os
import sys
import json
import urllib.parse

def run_rustscan(target: str):
    image = "rustscan/rustscan:latest"
    job_id = os.environ.get("WM_JOB_ID", "local_test_rustscan")

    target = target.replace("http://", "").replace("https://", "").split("/")[0]

    # Pull image
    print(f"DEBUG: Pulling image {image}...", file=sys.stderr, flush=True)
    subprocess.run(["docker", "pull", image], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    # Rustscan: rustscan -a target -- ...nmap args...
    # We want JSON output. Rustscan doesn't output JSON natively except via parsing Nmap xml?
    # Wait, Rustscan is a wrapper. It prints ports found then RUNS nmap.
    # We can use `-n` to prevent nmap and just get ports?
    # Or strict: `rustscan -a <target> --scripts None`
    # Output is text.
    # Ex: "Open 127.0.0.1:80"
    
    # Let's run basic rustscan and parse output.
    
    cmd = [
        "docker", "run",
        "--name", job_id,
        "--ulimit", "nofile=5000:5000", # Increase limits for speed
        image,
        "-a", target,
        "--scripts", "None" # Only scan ports, don't run nmap scripts
    ]
    
    print(f"DEBUG: Running command: {' '.join(cmd)}", file=sys.stderr, flush=True)
    
    ports = []
    
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
                print(f"RUSTSCAN: {line}", file=sys.stderr, flush=True)
                # Parse: "Open 1.2.3.4:80"
                if line.startswith("Open"):
                    parts = line.split(":")
                    if len(parts) > 1:
                        try:
                            port = int(parts[1])
                            ports.append(port)
                        except:
                            pass

        process.wait()

        if process.returncode != 0:
             _, stderr_output = process.communicate()
             print(f"DEBUG: Process stderr: {stderr_output}", file=sys.stderr, flush=True)
        
        return {
            "target": target, 
            "ports": sorted(ports)
        }

    except Exception as e:
        return {"error": str(e)}

def main(target: str = "scanme.nmap.org"):
    print(f"DEBUG: Scanning target: {target}", file=sys.stderr, flush=True)
    result = run_rustscan(target)
    return result

if __name__ == "__main__":
    target_arg = sys.argv[1] if len(sys.argv) > 1 else "scanme.nmap.org"
    main(target_arg)
