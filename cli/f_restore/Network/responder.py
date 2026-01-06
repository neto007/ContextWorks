import subprocess
import os
import sys
import json
import time
import signal

def run_responder(interface: str, duration: int):
    # Responder needs python.
    image = "python:3.11-alpine" 
    job_id = os.environ.get("WM_JOB_ID", "local_test_responder")
    
    # Needs root and net=host usually.
    # docker run --net=host --cap-add=NET_ADMIN ...
    
    # We install dependencies and run.
    # Responder needs net-tools, git.
    install_and_run = (
        "apk add --no-cache git net-tools >/dev/null && "
        "git clone --depth 1 https://github.com/lgandx/Responder.git >/dev/null && "
        "pip install -r Responder/requirements.txt >/dev/null && "
        f"python Responder/Responder.py -I {interface} -A" # -A = Analyze mode (passive)? Or active? 
        # User usually wants poisoning (-I eth0). 
        # But for automation, maybe we run it for X seconds?
    )
    
    cmd = [
        "docker", "run",
        "--name", job_id,
        "--net=host",     # Critical
        "--cap-add=NET_ADMIN",
        image,
        "sh", "-c",
        install_and_run
    ]
    
    print(f"DEBUG: Running command: {' '.join(cmd)}", file=sys.stderr, flush=True)
    
    findings = []
    
    try:
        process = subprocess.Popen(
            cmd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, 
            text=True, 
            bufsize=1
        )
        
        start_time = time.time()
        
        while True:
            # Check timeout
            if time.time() - start_time > duration:
                print("DEBUG: Timeout reached, stopping Responder...", file=sys.stderr, flush=True)
                process.terminate()
                subprocess.run(["docker", "stop", job_id], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                break

            line = process.stdout.readline()
            if not line and process.poll() is not None:
                break
            if line:
                line = line.strip()
                print(f"RESPONDER: {line}", file=sys.stderr, flush=True)
                # Parse: "[+] Poisoned answer sent to 1.2.3.4"
                if "[+]" in line or "Poisoned" in line:
                    findings.append(line)
                    
        process.wait()
        
        return {
            "interface": interface, 
            "duration": duration,
            "findings": findings
        }

    except Exception as e:
        return {"error": str(e)}

def main(interface: str = "eth0", duration: int = 30):
    print(f"DEBUG: Starting Responder on {interface} for {duration}s...", file=sys.stderr, flush=True)
    result = run_responder(interface, int(duration))
    return result

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # crude arg parsing
        iface = sys.argv[1]
        dur = sys.argv[2] if len(sys.argv) > 2 else 30
        main(iface, int(dur))
    else:
        main()
