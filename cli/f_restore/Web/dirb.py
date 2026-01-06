import subprocess
import os
import sys
import json
import re

def run_dirb(target: str):
    image = "kalilinux/kali-rolling"
    job_id = os.environ.get("WM_JOB_ID", "local_test_dirb")

    print(f"DEBUG: Pulling image {image}...", file=sys.stderr, flush=True)
    subprocess.run(["docker", "pull", image], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    install_and_run = (
        "apt-get update >/dev/null && "
        "apt-get install -y dirb >/dev/null && "
        f"dirb {target}"
    )

    cmd = [
        "docker", "run",
        "--name", job_id,
        image,
        "sh", "-c",
        install_and_run
    ]
    
    print(f"DEBUG: Running dirb...", file=sys.stderr, flush=True)
    
    findings = []
    
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
                print(f"DIRB: {line_stripped}", file=sys.stderr, flush=True)
                # Parse: "+ http://... (CODE:200|SIZE:123)"
                if line_stripped.startswith("+"):
                    findings.append(line_stripped)
                
        process.wait()

        return {"target": target, "findings": findings}

    except Exception as e:
        print(f"Error running dirb: {e}", file=sys.stderr, flush=True)
        return {"error": str(e)}
    finally:
        subprocess.run(["docker", "rm", "-f", job_id], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def main(target: str = "https://scanme.nmap.org"):
    print(f"DEBUG: Starting Dirb on {target}", file=sys.stderr, flush=True)
    result = run_dirb(target)
    return result

if __name__ == "__main__":
    if len(sys.argv) > 1:
        main(sys.argv[1])
    else:
        main()
