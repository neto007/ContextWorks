import subprocess
import os
import sys
import json

def run_kubescape(
    scan_target: str = "framework nsa",
    extra_args: str = ""
):
    """
    Run Kubescape Kubernetes Security Scanner.
    
    Args:
        scan_target: Scan target (e.g. 'framework nsa', 'framework mitre').
        extra_args: Additional arguments for kubescape.
    """
    # Kubescape image: armosec/kubescape
    image = "armosec/kubescape"
    job_id = os.environ.get("WM_JOB_ID", "local_test_kubescape")
    
    cmd = [
        "docker", "run", "--rm", "--name", job_id,
        "-v", "/var/run/docker.sock:/var/run/docker.sock", # If scanning local cluster
        image,
        "scan"
    ] + scan_target.split() + extra_args.split() + ["--format", "json"]
    
    print(f"DEBUG: Running kubescape scan {scan_target}...", file=sys.stderr, flush=True)
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0 and not result.stdout:
             return {"error": "Kubescape failed", "details": result.stderr}
             
        try:
             return json.loads(result.stdout)
        except:
             return {"raw_output": result.stdout, "details": result.stderr}
             
    except Exception as e:
        return {"error": str(e)}

def main(scan_target="framework nsa"):
    print(json.dumps(run_kubescape(scan_target), indent=2), flush=True)

if __name__ == "__main__":
    main()
