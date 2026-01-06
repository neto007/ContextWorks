import subprocess
import os
import sys
import json

def run_threatmapper(
    image_name: str = "alpine:latest"
):
    """
    Run ThreatMapper (Deepfence) Vulnerability Scan.
    
    Args:
        image_name: Docker image to scan.
    """
    # ThreatMapper has various components. The scanner image is deepfence/vulnerability_scanner
    image = "deepfence/vulnerability_scanner:latest"
    job_id = os.environ.get("WM_JOB_ID", "local_test_threatmapper")
    
    # Needs to be able to talk to docker daemon
    cmd = [
        "docker", "run", "--rm", "--name", job_id,
        "-v", "/var/run/docker.sock:/var/run/docker.sock",
        image,
        "-image-name", image_name
    ]
    
    print(f"DEBUG: Running ThreatMapper scan on {image_name}...", file=sys.stderr, flush=True)
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "success": result.returncode == 0
        }
    except Exception as e:
        return {"error": str(e)}

def main(image_name: str = "alpine:latest"):
    print(json.dumps(run_threatmapper(image_name), indent=2), flush=True)

if __name__ == "__main__":
    main()
