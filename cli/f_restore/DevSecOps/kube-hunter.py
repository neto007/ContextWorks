import subprocess
import os
import sys
import json

def run_kube_hunter(target: str):
    image = "aquasec/kube-hunter:latest"
    job_id = os.environ.get("WM_JOB_ID", "local_test_hunter")

    # Pull image
    print(f"DEBUG: Pulling image {image}...", file=sys.stderr, flush=True)
    subprocess.run(["docker", "pull", image], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    # kube-hunter command
    # --report json : Output JSON to stdout? Or file?
    # Kube-hunter prints to stdout.
    # We should capture stdout. 
    # But usually it prints logs too.
    # Let's try --log none --report json.
    # Note: Kube-hunter inside a container might need --network host to scan the host cluster.
    
    cmd = [
        "docker", "run",
        "--name", job_id,
        "--rm", # We will handle cleanup, but --rm is fine if we capture stdout
        image,
        "--log", "none",
        "--report", "json"
    ]
    
    # Add target arguments
    # If target is remote IP: --remote <ip>
    # If inside cluster: --pod
    # We let user pass the flag string directly for flexibility
    cmd.extend(target.split())
    
    print(f"DEBUG: Running command: {' '.join(cmd)}", file=sys.stderr, flush=True)
    
    try:
        # We need to capture stdout for the JSON
        # But we also want streaming logs if we weren't suppressing them.
        # Since we want machine readable output as primary result, we suppress logs.
        # Windmill user sees nothing? That's bad.
        # Better strategy: Output JSON to a file inside container, stream logs to stdout.
        # kube-hunter doesn't seem to support -o file easily with --report json mixed with logs.
        # It has --dispatch file --dispatch-file-path <path>??
        # Official docs say: --report json prints to stdout.
        # Let's use the standard "wrapper" trick: 
        # Run command, pipe output to file, but also print to stderr? 
        # No, simpler: Kube-hunter only outputs JSON if requested. 
        # We can run it, capture stdout as result. Prints "Scanning..." to stderr manually? 
        # Let's rely on standard stdout capture.
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
             print(f"DEBUG: Stderr: {result.stderr}", file=sys.stderr, flush=True)
             return {"error": "Kube-hunter failed", "details": result.stderr}

        try:
            return json.loads(result.stdout)
        except Exception as e:
            return {"error": f"Failed to parse JSON: {e}", "raw": result.stdout}

    except Exception as e:
        print(f"Error running kube-hunter: {e}", file=sys.stderr, flush=True)
        return {"error": str(e)}

def main(target: str = "--pod"):
    print(f"DEBUG: Starting Kube-Hunter on {target}", file=sys.stderr, flush=True)
    result = run_kube_hunter(target)
    return result

if __name__ == "__main__":
    target = sys.argv[1] if len(sys.argv) > 1 else "--pod"
    main(target)
