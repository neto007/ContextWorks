import subprocess
import os
import sys
import json

def run_evil_winrm(target: str, username: str, password: str):
    image = "oscarako/evil-winrm:latest"
    job_id = os.environ.get("WM_JOB_ID", "local_test_winrm")

    print(f"DEBUG: Pulling image {image}...", file=sys.stderr, flush=True)
    subprocess.run(["docker", "pull", image], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    cmd = [
        "docker", "run",
        "--name", job_id,
        image,
        "-i", target,
        "-u", username,
        "-p", password,
        # Default to echo check/exit
        "-e", "ipconfig"
    ]
    
    print(f"DEBUG: Running command: docker run ... evil-winrm", file=sys.stderr, flush=True)
    
    try:
        process = subprocess.Popen(
            cmd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, 
            text=True, 
            bufsize=1
        )
        
        output_buffer = []
        while True:
            line = process.stdout.readline()
            if not line and process.poll() is not None:
                break
            if line:
                print(f"EVIL-WINRM: {line.strip()}", file=sys.stderr, flush=True)
                output_buffer.append(line.strip())
                
        process.wait()
        
        return {"target": target, "status": "Finished", "details": "See logs"}

    except Exception as e:
        print(f"Error running evil-winrm: {e}", file=sys.stderr, flush=True)
        return {"error": str(e)}
    finally:
        subprocess.run(["docker", "rm", "-f", job_id], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def main(target: str = "127.0.0.1", username: str = "Admin", password: str = "pass"):
    print(f"DEBUG: Starting Evil-WinRM on {target}", file=sys.stderr, flush=True)
    result = run_evil_winrm(target, username, password)
    return result

if __name__ == "__main__":
    main()
