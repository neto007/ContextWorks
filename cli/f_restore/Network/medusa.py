import subprocess
import os
import sys
import json
import re

def run_medusa(target: str, module: str, username: str, password: str):
    image = "kalilinux/kali-rolling"
    job_id = os.environ.get("WM_JOB_ID", "local_test_medusa")

    # Pull image
    print(f"DEBUG: Pulling image {image}...", file=sys.stderr, flush=True)
    subprocess.run(["docker", "pull", image], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    install_and_run = (
        "apt-get update >/dev/null && "
        "apt-get install -y medusa >/dev/null && "
        f"medusa -h {target} -u {username} -p {password} -M {module} -v 5"
    )

    cmd = [
        "docker", "run",
        "--name", job_id,
        image,
        "sh", "-c",
        install_and_run
    ]
    
    print(f"DEBUG: Running command: docker run ... medusa", file=sys.stderr, flush=True)
    
    scan_result = {"target": target, "module": module, "findings": []}
    
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
                line_stripped = line.strip()
                print(f"MEDUSA: {line_stripped}", file=sys.stderr, flush=True)
                
                # Check for success
                # ACCOUNT FOUND: [ssh] Host: 1.1.1.1 User: admin Password: password [SUCCESS]
                if "ACCOUNT FOUND" in line_stripped:
                     scan_result["findings"].append(line_stripped)
                
        process.wait()

        return scan_result

    except Exception as e:
        print(f"Error running medusa: {e}", file=sys.stderr, flush=True)
        return {"error": str(e)}
    finally:
        subprocess.run(["docker", "rm", "-f", job_id], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def main(target: str = "scanme.nmap.org", module: str = "ssh", username: str = "admin", password: str = "password"):
    print(f"DEBUG: Starting Medusa against {target}", file=sys.stderr, flush=True)
    result = run_medusa(target, module, username, password)
    return result

if __name__ == "__main__":
     if len(sys.argv) > 4:
        main(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
     else:
        main()
