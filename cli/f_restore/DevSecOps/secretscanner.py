import subprocess
import os
import sys
import json

def run_secretscanner(
    image_name: str = "alpine:latest"
):
    """
    Run Deepfence SecretScanner.
    
    Args:
        image_name: Docker image to scan for secrets.
    """
    # SecretScanner image: deepfence/secret_scanner
    image = "deepfence/secret_scanner:latest"
    job_id = os.environ.get("WM_JOB_ID", "local_test_secretscanner")
    
    cmd = [
        "docker", "run", "--rm", "--name", job_id,
        "-v", "/var/run/docker.sock:/var/run/docker.sock",
        image,
        "-image-name", image_name
    ]
    
    print(f"DEBUG: Running SecretScanner on {image_name}...", file=sys.stderr, flush=True)
    
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
    print(json.dumps(run_secretscanner(image_name), indent=2), flush=True)

if __name__ == "__main__":
    main()
