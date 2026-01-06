import subprocess
import os
import sys
import json

def run_cdk(
    cmd_args: str = "run --help"
):
    """
    Run CDK (Container Penetration Toolkit).
    
    Args:
        cmd_args: Arguments for CDK (e.g. 'run ship', 'evaluate').
    """
    # CDK image: cdkteam/cdk
    image = "cdkteam/cdk"
    job_id = os.environ.get("WM_JOB_ID", "local_test_cdk")
    
    # CDK needs various privileges/mounts for full escape testing, 
    # but we'll run it in a standard restricted way for basic checks.
    
    cmd = [
        "docker", "run", "--rm", "--name", job_id,
        image
    ] + cmd_args.split()
    
    print(f"DEBUG: Running CDK {cmd_args}...", file=sys.stderr, flush=True)
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "success": result.returncode == 0
        }
    except Exception as e:
        return {"error": str(e)}

def main(cmd_args: str = "evaluate"):
    print(json.dumps(run_cdk(cmd_args), indent=2), flush=True)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        main(" ".join(sys.argv[1:]))
    else:
        main()
