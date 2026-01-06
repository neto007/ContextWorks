import subprocess
import os
import sys
import json

def run_kube_bench(targets: str):
    image = "aquasec/kube-bench:latest"
    job_id = os.environ.get("WM_JOB_ID", "local_test_bench")

    # Pull image
    print(f"DEBUG: Pulling image {image}...", file=sys.stderr, flush=True)
    subprocess.run(["docker", "pull", image], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    # kube-bench needs access to host config files
    # We are running docker inside docker (sibling).
    # We mount the HOST paths to the container.
    # Standard kube-bench mounts: /etc, /var
    
    cmd = [
        "docker", "run",
        "--name", job_id,
        "--pid", "host",
        "-v", "/etc:/etc:ro",
        "-v", "/var:/var:ro",
        "-v", "/usr/bin:/usr/local/mount-from-host/bin:ro",
        image,
        "--json",
        "--targets", targets
    ]
    
    print(f"DEBUG: Running command: docker run ... kube-bench --targets {targets}", file=sys.stderr, flush=True)
    
    try:
        # Capture stdout for JSON
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
             print(f"DEBUG: Stderr: {result.stderr}", file=sys.stderr, flush=True)
             # Kube-bench might return non-zero if checks fail? No, usually 0 if ran.
             # If it fails, likely config missing.
             return {"error": "Kube-bench failed", "details": result.stderr}

        try:
            # kube-bench outputs a list of JSON objects (one per target?) or a single object.
            return json.loads(result.stdout)
        except Exception as e:
            return {"error": f"Failed to parse JSON: {e}", "raw": result.stdout}

    except Exception as e:
        print(f"Error running kube-bench: {e}", file=sys.stderr, flush=True)
        return {"error": str(e)}
    finally:
        subprocess.run(["docker", "rm", "-f", job_id], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def main(targets: str = "node"):
    print(f"DEBUG: Starting Kube-Bench on targets: {targets}", file=sys.stderr, flush=True)
    result = run_kube_bench(targets)
    return result

if __name__ == "__main__":
    targets = sys.argv[1] if len(sys.argv) > 1 else "node"
    main(targets)
