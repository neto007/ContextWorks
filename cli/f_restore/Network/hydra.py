import subprocess
import os
import sys
import json
import re

def run_hydra(target: str, service: str, username: str, password: str):
    image = "alpine:latest"
    job_id = os.environ.get("WM_JOB_ID", "local_test_hydra")

    # Pull image
    print(f"DEBUG: Pulling image {image}...", file=sys.stderr, flush=True)
    subprocess.run(["docker", "pull", image], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    # Hydra needs `hydra` package from community repo
    # Also we need wordlists mostly, but for now we assume single user/pass input or paths?
    # If user provides a path, we assume it's one of the common wordlists we might download?
    # For simplicity, this script supports single user/pass testing OR user-provided lists if we mount them.
    # Windmill usually uploads files. Since we can't easily upload per-job without more logic, 
    # we'll stick to basic single credential check or download a common list.
    
    # For now: basic usage.
    
    install_and_run = (
        "apk add --no-cache hydra >/dev/null && "
        f"hydra -l {username} -p {password} {target} {service} -vV"
    )

    cmd = [
        "docker", "run",
        "--name", job_id,
        image,
        "sh", "-c",
        install_and_run
    ]
    
    print(f"DEBUG: Running command: docker run ... hydra ...", file=sys.stderr, flush=True)
    
    scan_result = {"target": target, "service": service, "findings": []}
    
    try:
        process = subprocess.Popen(
            cmd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, 
            text=True, 
            bufsize=1
        )
        
        # Stream stdout (Hydra prints to stdout)
        # We also want to parse findings.
        # Format: "[22][ssh] host: 1.1.1.1   login: admin   password: password"
        
        output_buffer = []
        
        while True:
            line = process.stdout.readline()
            if not line and process.poll() is not None:
                break
            if line:
                line_stripped = line.strip()
                output_buffer.append(line_stripped)
                print(f"HYDRA: {line_stripped}", file=sys.stderr, flush=True)
                
                # Check for success
                # Hydra usually prints green text or specific pattern.
                # Pattern: "[PORT][SERVICE] host: IP   login: USER   password: PASS"
                if "login:" in line_stripped and "password:" in line_stripped and "host:" in line_stripped:
                    # Parse it
                    try:
                        # Regex to capture content
                        match = re.search(r"login:\s+(.+?)\s+password:\s+(.+)", line_stripped)
                        if match:
                           scan_result["findings"].append({
                               "username": match.group(1),
                               "password": match.group(2)
                           })
                    except:
                        pass
                
        process.wait()

        # Hydra exit code: 0 normally. 
        # If it finds something vs nothing? exit code is 0 usually.
        
        return scan_result

    except Exception as e:
        print(f"Error running hydra: {e}", file=sys.stderr, flush=True)
        return {"error": str(e)}
    finally:
        subprocess.run(["docker", "rm", "-f", job_id], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def main(target: str = "scanme.nmap.org", service: str = "ssh", username: str = "admin", password: str = "password"):
    print(f"DEBUG: Starting Hydra against {target} ({service})", file=sys.stderr, flush=True)
    result = run_hydra(target, service, username, password)
    return result

if __name__ == "__main__":
    if len(sys.argv) > 4:
        main(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])
    else:
        main()
