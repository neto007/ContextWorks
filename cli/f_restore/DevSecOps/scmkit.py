import subprocess
import os
import sys
import json

def run_scmkit(
    cmd_args: str = "--help"
):
    """
    Run SCMKit (Software Configuration Management Toolkit).
    
    Args:
        cmd_args: Arguments for SCMKit.
    """
    # SCMKit is a .NET Core tool. 
    image = "mcr.microsoft.com/dotnet/sdk:6.0"
    job_id = os.environ.get("WM_JOB_ID", "local_test_scmkit")
    
    setup_and_run = (
        "git clone https://github.com/h4wkst3r/SCMKit.git /app >/dev/null && "
        "cd /app/SCMKit && "
        "dotnet build -c Release >/dev/null 2>&1 && "
        f"dotnet bin/Release/net6.0/SCMKit.dll {cmd_args}"
    )
    
    cmd = [
        "docker", "run", "--rm", "--name", job_id, image, "sh", "-c", setup_and_run
    ]
    
    print(f"DEBUG: Running SCMKit {cmd_args}...", file=sys.stderr, flush=True)
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "success": result.returncode == 0
        }
    except Exception as e:
        return {"error": str(e)}

def main(cmd_args: str = "--help"):
    print(json.dumps(run_scmkit(cmd_args), indent=2), flush=True)

if __name__ == "__main__":
    main()
