import subprocess
import os
import sys
import json
import urllib.parse
import re

def run_netexec(target: str):
    image = "python:slim" # NetExec needs python 3.10+ and compiling (crypto deps).
    # Official image is safer? Pennyw0rth/NetExec usually.
    # But let's try dynamically install in python:3.11-alpine (might leverage apk) or python:slim.
    # Pip installing netexec is huge (200MB+ of deps).
    # Let's try finding a solid docker image. 
    # 'porchetta/netexec' is commonly cited? Or the repo's ghcr.io.
    # Let's try 'ghcr.io/pennyw0rth/netexec:latest' 
    # If fails, we fallback to python:latest + pip install.
    image = "ghcr.io/pennyw0rth/netexec:latest"
    # Wait, 'pennyw0rth' repo is correct for NetExec (nxc).
    
    job_id = os.environ.get("WM_JOB_ID", "local_test_netexec")

    target = target.replace("http://", "").replace("https://", "").split("/")[0]

    # Pull image
    print(f"DEBUG: Pulling image {image}...", file=sys.stderr, flush=True)
    try:
        subprocess.run(["docker", "pull", image], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except:
        # If pull fails, maybe image name changed.
        print("DEBUG: Image pull failed. Trying python pip install fallback...", file=sys.stderr, flush=True)
        image = "python:3.11" # Debian based easier for crypto
    
    if "python" in image:
         install_and_run = (
             "pip install netexec >/dev/null && "
             f"nxc smb {target}" # Defaulting to smb? User might want other protocol.
             # NetExec needs protocol. "nxc smb target".
             # We should probably default to smb or sniff?
             # For a general tool, we default to smb.
         )
         cmd_base = ["sh", "-c", install_and_run]
    else:
         # Official image entrypoint usually "nxc"
         cmd_base = ["smb", target]

    cmd = [
        "docker", "run",
        "--name", job_id,
        image
    ]
    if "python" in image:
        cmd.extend(cmd_base)
    else:
        cmd.extend(cmd_base)
        
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
        
        # Parse output: 
        # SMB 1.2.3.4 445 PCNAME [*] Windows 10.0 Build 19041 x64 (name:PCNAME) (domain:Workgroup) (signing:False) (SMBv1:False)
        # [+] ...
        # [-] ...
        
        while True:
            line = process.stdout.readline()
            if not line and process.poll() is not None:
                break
            if line:
                line = line.strip()
                print(f"NETEXEC: {line}", file=sys.stderr, flush=True)
                
                if "[+]" in line or "[*]" in line:
                    findings.append(line)
        
        process.wait()
        
        return {
            "target": target, 
            "protocol": "smb", # Hardcoded for this simplified script
            "findings": findings
        }

    except Exception as e:
        return {"error": str(e)}

def main(target: str = "scanme.nmap.org"):
    print(f"DEBUG: Scanning target: {target}", file=sys.stderr, flush=True)
    result = run_netexec(target)
    return result

if __name__ == "__main__":
    target_arg = sys.argv[1] if len(sys.argv) > 1 else "scanme.nmap.org"
    main(target_arg)
