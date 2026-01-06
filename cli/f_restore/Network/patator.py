import subprocess
import os
import sys
import json

def run_patator(target: str, module: str):
    image = "python:alpine"
    job_id = os.environ.get("WM_JOB_ID", "local_test_patator")

    print(f"DEBUG: Pulling image {image}...", file=sys.stderr, flush=True)
    subprocess.run(["docker", "pull", image], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    # Patator install: git clone + pip install pycurl/paramiko usually.
    # Alpine needs build-base for pycurl/paramiko.
    install_and_run = (
        "apk add --no-cache git build-base libffi-dev openssl-dev python3-dev >/dev/null && "
        "pip install paramiko pycurl >/dev/null && "
        "git clone https://github.com/lanjelot/patator.git >/dev/null && "
        f"python patator/patator.py {module} host={target} user=admin password=password 0=1"
    )

    cmd = [
        "docker", "run",
        "--name", job_id,
        image,
        "sh", "-c",
        install_and_run
    ]
    
    print(f"DEBUG: Running command: docker run ... patator", file=sys.stderr, flush=True)
    
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
                print(f"PATATOR: {line.strip()}", file=sys.stderr, flush=True)
                
        process.wait()
        
        return {"target": target, "module": module, "status": "Completed (check logs for findings)"}

    except Exception as e:
        print(f"Error running patator: {e}", file=sys.stderr, flush=True)
        return {"error": str(e)}
    finally:
        subprocess.run(["docker", "rm", "-f", job_id], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def main(target: str = "scanme.nmap.org", module: str = "ssh_login"):
    print(f"DEBUG: Starting Patator against {target}", file=sys.stderr, flush=True)
    result = run_patator(target, module)
    return result

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "scanme.nmap.org"
    main(target)
