import subprocess
import os
import sys
import json

def run_trivy(target: str, scan_type: str):
    image = "aquasec/trivy:latest"
    job_id = os.environ.get("WM_JOB_ID", "local_test_trivy")

    # Pull image
    print(f"DEBUG: Pulling image {image}...", file=sys.stderr, flush=True)
    subprocess.run(["docker", "pull", image], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    # Trivy command
    # -f json : Output JSON
    # -o /tmp/trivy.json : Output file
    # --no-progress : partial output stream manually? Trivy prints findings to stdout usually.
    # To stream *and* get JSON, we usually output JSON to file and findings to stdout.
    # But Trivy -f json suppresses table output.
    # Strategy: Run twice? No, too slow.
    # Strategy: Run once with -f json -o file, but what about logs?
    # Trivy doesn't really have "logs" in json mode, just the json.
    # We can print "Scanning..." and then just return the JSON.
    # Or we can run with table output to logs, and json output to file? 
    # Trivy supports multiple outputs? No.
    # Let's keep it simple: -f json -o /tmp/report.json.
    # We can stream stderr for progress (db download etc).
    
    cmd = [
        "docker", "run",
        "--name", job_id,
        image,
        scan_type,
        "--format", "json",
        "--output", "/tmp/trivy.json",
        "--no-progress",
        target
    ]
    
    print(f"DEBUG: Running command: docker run ... trivy {scan_type} {target}", file=sys.stderr, flush=True)
    
    try:
        process = subprocess.Popen(
            cmd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, 
            text=True, 
            bufsize=1
        )
        
        # Stream stderr (Trivy logs go here usually)
        while True:
            line = process.stderr.readline()
            if not line and process.poll() is not None:
                break
            if line:
                print(f"TRIVY: {line.strip()}", file=sys.stderr, flush=True)
                
        process.wait()

        if process.returncode != 0:
             # Look for stdout too in case of error
             stdout_output = process.stdout.read()
             print(f"DEBUG: Process stdout: {stdout_output}", file=sys.stderr, flush=True)
             return {"error": "Trivy failed", "details": "Check logs"}

        # Copy output
        local_output = f"/tmp/{job_id}_trivy.json"
        
        cp_cmd = ["docker", "cp", f"{job_id}:/tmp/trivy.json", local_output]
        cp_result = subprocess.run(cp_cmd, capture_output=True, text=True)
        
        result_data = {}
        
        if cp_result.returncode == 0:
            try:
                with open(local_output, "r") as f:
                    result_data = json.load(f)
                os.remove(local_output)
            except Exception as e:
                return {"error": f"Failed to parse JSON: {e}"}
        else:
             return {"error": "Could not copy output file", "details": cp_result.stderr}

        return result_data

    except Exception as e:
        print(f"Error running trivy: {e}", file=sys.stderr, flush=True)
        return {"error": str(e)}
    finally:
        # Cleanup container
        subprocess.run(["docker", "rm", "-f", job_id], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def main(target: str = "python:3.9-alpine", scan_type: str = "image"):
    print(f"DEBUG: Starting Trivy scan on {target}", file=sys.stderr, flush=True)
    result = run_trivy(target, scan_type)
    return result

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "python:3.9-alpine"
    main(target)
