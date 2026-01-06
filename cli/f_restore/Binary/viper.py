import subprocess
import os
import sys
import json

def run_viper(
    cmd_args: str = "help"
):
    """
    Run Viper (Intranet Penetration Framework).
    
    Args:
        cmd_args: Arguments for Viper CLI.
    """
    # Viper is a complex framework. The official image is funnywolf/viper.
    # It's usually run as a web platform, but we can try to interact with its CLI or help.
    image = "funnywolf/viper:latest"
    job_id = os.environ.get("WM_JOB_ID", "local_test_viper")
    
    cmd = [
        "docker", "run", "--rm", "--name", job_id,
        image,
        "viper", cmd_args
    ]
    
    print(f"DEBUG: Running Viper {cmd_args}...", file=sys.stderr, flush=True)
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "success": result.returncode == 0
        }
    except Exception as e:
        return {"error": str(e)}

def main(cmd_args: str = "help"):
    print(json.dumps(run_viper(cmd_args), indent=2), flush=True)

if __name__ == "__main__":
    main()
