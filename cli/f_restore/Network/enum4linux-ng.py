import subprocess
import os
import sys
import json
import urllib.parse

def run_enum4linux(target: str):
    image = "python:alpine"
    job_id = os.environ.get("WM_JOB_ID", "local_test_enum4linux")

    target = target.replace("http://", "").replace("https://", "").split("/")[0]

    # Pull image
    print(f"DEBUG: Pulling image {image}...", file=sys.stderr, flush=True)
    subprocess.run(["docker", "pull", image], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    # Enum4linux-ng setup in Alpine
    # Dependencies: 
    # - samba-client (smbclient, nmblookup)
    # - samba-common-tools (net) -> CRITICAL for enum4linux-ng
    # - git, build-base (pip deps)
    install_and_run = (
        "apk add --no-cache git samba-client samba-common-tools >/dev/null && "
        "git clone --depth 1 https://github.com/cddmp/enum4linux-ng.git >/dev/null && "
        "pip install --root-user-action=ignore -r enum4linux-ng/requirements.txt >/dev/null && "
        f"python enum4linux-ng/enum4linux-ng.py -A {target} -oJ /tmp/enum.json"
    )
    
    cmd = [
        "docker", "run",
        "--name", job_id,
        image,
        "sh", "-c",
        install_and_run
    ]
    
    print(f"DEBUG: Running command: {' '.join(cmd)}", file=sys.stderr, flush=True)
    
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
                print(f"ENUM4LINUX: {line}", file=sys.stderr, flush=True)
                
        process.wait()

        if process.returncode != 0:
             _, stderr_output = process.communicate()
             print(f"DEBUG: Process stderr: {stderr_output}", file=sys.stderr, flush=True)
             
        # Read output
        local_json_path = f"/tmp/{job_id}_enum.json"
        cp_cmd = ["docker", "cp", f"{job_id}:/tmp/enum.json", local_json_path]
        cp_result = subprocess.run(cp_cmd, capture_output=True, text=True)
        
        if cp_result.returncode != 0:
             # Tool might have aborted (e.g. no SMB reachable)
             return {
                 "status": "No results or Connection Failed",
                 "details": "JSON report not generated. Check logs.", 
                 "raw_output": "See Windmill Logs for 'ENUM4LINUX:' lines."
             }
             
        try:
            with open(local_json_path, "r") as f:
                content = f.read()
            os.remove(local_json_path)
            
            return json.loads(content)
        except Exception as e:
            return {"error": f"Failed to parse JSON: {str(e)}"}

    except Exception as e:
        return {"error": str(e)}

def main(target: str = "scanme.nmap.org"):
    print(f"DEBUG: Scanning target: {target}", file=sys.stderr, flush=True)
    result = run_enum4linux(target)
    return result

if __name__ == "__main__":
    target_arg = sys.argv[1] if len(sys.argv) > 1 else "scanme.nmap.org"
    main(target_arg)
