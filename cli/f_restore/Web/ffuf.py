import subprocess
import os
import sys
import json
import urllib.parse
import re

def run_ffuf(target: str):
    image = "alpine:latest"
    job_id = os.environ.get("WM_JOB_ID", "local_test_ffuf")

    # Sanitize target
    if "://" not in target:
         target = f"https://{target}"
    
    # Needs FUZZ keyword if not present, but user might just give url.
    # We will assume directory fuzzing if no FUZZ keyword
    if "FUZZ" not in target:
        if not target.endswith("/"):
            target += "/"
        target += "FUZZ"

    # Pull image
    print(f"DEBUG: Pulling image {image}...", file=sys.stderr, flush=True)
    subprocess.run(["docker", "pull", image], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    # We need a wordlist. FFUF image DOES NOT include large wordlists usually.
    # We will use the same trick as Gobuster: use an image that has wget/curl OR
    # use a multi-stage approach?
    # ffuf/ffuf is scratch/alpine based? 
    # Let's inspect ffuf/ffuf. It usually has valid shell.
    # We will try to download common.txt inside the container if wget exists,
    # or mount it, or pipe it.
    # Piping is powerful: curl list | docker run -i ...
    # But FFUF needs a file path or stdin.
    
    # Better approach for Windmill: 
    # Use `alpine` or `python:alpine` to fetch list + bind mount? 
    # Or just use `ghcr.io/ffuf/ffuf`?
    # Simple robust way similar to Gobuster: 
    # Use a base image (alpine), install ffuf (from release or package), fetch wordlist.
    # Alpine 'ffuf' package exists in Edge/Community? Maybe.
    # SAFEST: Use `golang:alpine` or `alpine` and download binary + wordlist.
    # FFUF binary is static.
    
    # Let's try downloading binary + wordlist in alpine.
    wordlist_url = "https://raw.githubusercontent.com/danielmiessler/SecLists/master/Discovery/Web-Content/common.txt"
    ffuf_url = "https://github.com/ffuf/ffuf/releases/download/v2.1.0/ffuf_2.1.0_linux_amd64.tar.gz"
    
    setup_and_run = (
        "apk add --no-cache curl tar >/dev/null && "
        f"curl -sL -o ffuf.tar.gz {ffuf_url} && "
        "tar xf ffuf.tar.gz && "
        "mv ffuf /usr/bin/ffuf && " 
        f"curl -sL -o wordlist.txt {wordlist_url} && "
        f"ffuf -u {target} -w wordlist.txt -o /tmp/ffuf_out.json -of json -v"
    )
    
    cmd = [
        "docker", "run",
        "--name", job_id,
        "alpine:latest",
        "sh", "-c",
        setup_and_run
    ]
    
    print(f"DEBUG: Running command: {' '.join(cmd)}", file=sys.stderr, flush=True)
    
    try:
        # Popen to stream output
        process = subprocess.Popen(
            cmd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, 
            text=True, 
            bufsize=1
        )
        
        # Stream stdout
        while True:
            line = process.stdout.readline()
            if not line and process.poll() is not None:
                break
            if line:
                line = line.strip()
                print(f"FFUF: {line}", file=sys.stderr, flush=True)
                
        process.wait()

        # Check stderr
        if process.returncode != 0:
             _, stderr_output = process.communicate()
             print(f"DEBUG: Process stderr: {stderr_output}", file=sys.stderr, flush=True)

        # Read output file
        local_json_path = f"/tmp/{job_id}_ffuf.json"
        cp_cmd = ["docker", "cp", f"{job_id}:/tmp/ffuf_out.json", local_json_path]
        cp_result = subprocess.run(cp_cmd, capture_output=True, text=True)
        
        if cp_result.returncode != 0:
             return {"error": "Could not copy output file", "details": cp_result.stderr}
             
        try:
            with open(local_json_path, "r") as f:
                json_content = f.read()
            os.remove(local_json_path)
            
            data = json.loads(json_content)
            # FFUF json structure: { "commandline": "...", "results": [ ... ] }
            return {"target": target, "results": data.get("results", [])}
        except Exception as e:
            return {"error": f"Failed to parse JSON: {str(e)}", "raw": json_content if 'json_content' in locals() else "N/A"}

    except Exception as e:
        return {"error": str(e)}

def main(target: str = "https://scanme.nmap.org/"):
    print(f"DEBUG: Scanning target: {target}", file=sys.stderr, flush=True)
    result = run_ffuf(target)
    return result

if __name__ == "__main__":
    target_arg = sys.argv[1] if len(sys.argv) > 1 else "https://scanme.nmap.org/"
    main(target_arg)
