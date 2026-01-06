import subprocess
import os
import sys
import json
import urllib.parse

def run_nikto(target: str):
    image = "secsi/nikto:latest"
    job_id = os.environ.get("WM_JOB_ID", "local_test_nikto")

    # Sanitize target
    target = target.strip()
    
    # Pull image
    print(f"DEBUG: Pulling image {image}...", file=sys.stderr, flush=True)
    subprocess.run(["docker", "pull", image], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    # Ensure cleanup of previous container with same name if exists
    subprocess.run(["docker", "rm", "-f", job_id], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # Run Nikto as root to allow installing SSL dependency (perl-net-ssleay)
    # Then run nikto.pl directly to avoid path issues
    install_and_run = (
        "apk add --no-cache perl-net-ssleay >/dev/null && "
        f"/nikto/program/nikto.pl -h {target} -Format json -o /tmp/nikto_out.json"
    )
    
    cmd = [
        "docker", "run",
        "--name", job_id,
        "--user", "root",
        image,
        "sh", "-c",
        install_and_run
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
                print(f"NIKTO: {line}", file=sys.stderr, flush=True)
                
        # Wait for finish
        process.wait()
        
        # Check stderr/result
        if process.returncode != 0:
             _, stderr_output = process.communicate()
             print(f"DEBUG: Process stderr: {stderr_output}", file=sys.stderr, flush=True)
             # Nikto might return non-zero on vulns, so we proceed to check for file
             # But if "Command not found", it's a real error
             if "Command not found" in stderr_output or "Can't locate" in stderr_output:
                 return {"error": "Nikto execution failed", "details": stderr_output}

        # Read the JSON file from the container
        local_json_path = f"/tmp/{job_id}_nikto.json"
        cp_cmd = ["docker", "cp", f"{job_id}:/tmp/nikto_out.json", local_json_path]
        cp_result = subprocess.run(cp_cmd, capture_output=True, text=True)
        
        if cp_result.returncode != 0:
             return {"error": "Could not copy output file (maybe scan failed or no vulnerabilities found?)", "details": cp_result.stderr}
             
        try:
            with open(local_json_path, "r") as f:
                json_content = f.read()
            os.remove(local_json_path)
            return json.loads(json_content)
        except Exception as e:
            return {"error": f"Failed to parse JSON: {str(e)}", "raw_content": json_content if 'json_content' in locals() else "N/A"}

    except Exception as e:
        return {"error": str(e)}
    finally:
         # Cleanup container
         subprocess.run(["docker", "rm", "-f", job_id], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def main(target: str = "scanme.nmap.org"):
    print(f"DEBUG: Scanning target: {target}", file=sys.stderr, flush=True)
    result = run_nikto(target)
    return result

if __name__ == "__main__":
    target_arg = sys.argv[1] if len(sys.argv) > 1 else "scanme.nmap.org"
    main(target_arg)
