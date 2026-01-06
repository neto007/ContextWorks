import subprocess
import os
import sys
import json

def run_veinmind(
    target: str = "image",
    image_name: str = ""
):
    """
    Run veinmind-tools (Container Security).
    
    Args:
        target: Target type (image, container, iac).
        image_name: Name of the image to scan.
    """
    # veinmind-tools has a runner image: chaitin/veinmind-runner
    image = "chaitin/veinmind-runner"
    job_id = os.environ.get("WM_JOB_ID", "local_test_veinmind")
    
    cmd = [
        "docker", "run", "--rm", "--name", job_id,
        "-v", "/var/run/docker.sock:/var/run/docker.sock",
        image,
        "scan", target, image_name
    ]
    
    print(f"DEBUG: Running veinmind scan {target} {image_name}...", file=sys.stderr, flush=True)
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "success": result.returncode == 0
        }
    except Exception as e:
        return {"error": str(e)}

def main(target: str = "image", image_name: str = "alpine:latest"):
    print(json.dumps(run_veinmind(target, image_name), indent=2), flush=True)

if __name__ == "__main__":
    main()
