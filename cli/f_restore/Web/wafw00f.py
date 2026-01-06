import subprocess
import os
import sys
import json
import urllib.parse

def run_wafw00f(target: str):
    image = "python:alpine"
    job_id = os.environ.get("WM_JOB_ID", "local_test_wafw00f")

    # Sanitize target
    if "://" not in target:
         target = f"https://{target}"

    # Pull image
    print(f"DEBUG: Pulling image {image}...", file=sys.stderr, flush=True)
    subprocess.run(["docker", "pull", image], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    # wafw00f supports JSON output via -f json -o file
    install_and_run = (
        "pip install wafw00f >/dev/null && "
        f"wafw00f {target} -f json -o /tmp/waf.json"
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
                print(f"WAFW00F: {line}", file=sys.stderr, flush=True)
                
        process.wait()

        if process.returncode != 0:
             _, stderr_output = process.communicate()
             print(f"DEBUG: Process stderr: {stderr_output}", file=sys.stderr, flush=True)
             
        # Read output
        local_json_path = f"/tmp/{job_id}_waf.json"
        cp_cmd = ["docker", "cp", f"{job_id}:/tmp/waf.json", local_json_path]
        cp_result = subprocess.run(cp_cmd, capture_output=True, text=True)
        
        if cp_result.returncode != 0:
            # Wafw00f might not produce json if fails?
            return {"error": "Could not copy output file", "details": cp_result.stderr}
            
        try:
            with open(local_json_path, "r") as f:
                content = f.read()
            os.remove(local_json_path)
            # Wafw00f JSON is usually a list of dicts
            return json.loads(content)
        except Exception as e:
            return {"error": f"Failed to parse JSON: {str(e)}", "raw": content if 'content' in locals() else "N/A"}

    except Exception as e:
        return {"error": str(e)}

def main(target: str = "https://scanme.nmap.org"):
    print(f"DEBUG: Scanning target: {target}", file=sys.stderr, flush=True)
    result = run_wafw00f(target)
    return result

if __name__ == "__main__":
    target_arg = sys.argv[1] if len(sys.argv) > 1 else "https://scanme.nmap.org"
    main(target_arg)
