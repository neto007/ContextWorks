import subprocess
import os
import sys
import json
import re

def run_cloudpeler(target: str):
    image = "alpine:latest"
    job_id = os.environ.get("WM_JOB_ID", "local_test_cloudpeler")

    # Sanitize target logic (remove protocol)
    target = target.strip()
    target_clean = target.replace("http://", "").replace("https://", "").split("/")[0]

    # Pull image
    print(f"DEBUG: Pulling image {image}...", file=sys.stderr, flush=True)
    subprocess.run(["docker", "pull", image], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    # Construct command
    # Install php, php-curl, git
    # Clone CloudPeler
    # Run
    setup_and_run = (
        "apk add --no-cache php php-curl git >/dev/null && "
        "git clone https://github.com/zidansec/CloudPeler.git /app >/dev/null 2>&1 && "
        "cd /app && "
        f"php crimeflare.php {target_clean}"
    )
    
    cmd = [
        "docker", "run",
        "--rm",
        "--name", job_id,
        "--dns", "8.8.8.8",
        image,
        "sh", "-c",
        setup_and_run
    ]
    
    print(f"DEBUG: Running command: docker run ... php crimeflare.php {target_clean}", file=sys.stderr, flush=True)
    
    try:
        # Use Popen to stream output
        process = subprocess.Popen(
            cmd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, 
            text=True, 
            bufsize=1
        )
        
        logs = []
        real_ip = None
        
        while True:
            line = process.stdout.readline()
            if not line and process.poll() is not None:
                break
            if line:
                line = line.strip()
                if line:
                    # Print raw line to stderr for realtime feedback
                    print(f"CLOUDPELER: {line}", file=sys.stderr, flush=True)
                    logs.append(line)
                    
                    # Try to capture Real IP if printed
                    # Example output format needs to be observed. 
                    # Usually: "Real IP Address: 1.2.3.4" or similar
                    if "Real IP" in line or "IP Address" in line:
                         # Simple extraction heuristic
                         ips = re.findall(r'[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}', line)
                         if ips:
                             real_ip = ips[0]
        
        process.wait()

        if process.returncode != 0:
             stderr_output = process.stderr.read()
             print(f"DEBUG: Process stderr: {stderr_output}", file=sys.stderr, flush=True)
             # CloudPeler might fail or not find anything
        
        if real_ip:
            return {"target": target_clean, "real_ip": real_ip, "success": True}
        else:
            return {"target": target_clean, "success": False, "note": "No IP bypass found or tool failed"}

    except Exception as e:
        return {"error": str(e)}

def main(target: str = "example.com"):
    print(f"DEBUG: Scanning target: {target}", file=sys.stderr, flush=True)
    result = run_cloudpeler(target)
    print(json.dumps(result, indent=2), flush=True)
    return result

if __name__ == "__main__":
    if len(sys.argv) > 1:
        target_arg = sys.argv[1]
        main(target_arg)
    else:
        main()
