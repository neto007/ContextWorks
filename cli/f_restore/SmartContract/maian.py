import subprocess
import os
import sys
import json

def run_maian(
    sol_file_content: str = "",
    check_type: str = "greedy"
):
    """
    Run MAIAN Smart Contract Security Tool.
    
    Args:
        sol_file_content: Solidity contract code.
        check_type: Type of vulnerability to check (greedy, prodigal, suicidal).
    """
    # MAIAN is a legacy tool (Python 2). 
    # We use a python:2-alpine image and clone the repo.
    image = "python:2-alpine"
    job_id = os.environ.get("WM_JOB_ID", "local_test_maian")
    
    # Write to temp file
    temp_file = "contract.sol"
    with open(temp_file, "w") as f:
        f.write(sol_file_content)
        
    # MAIAN requires solc. We'll need to install it in the container.
    # Since it's complex, we'll try a minimal setup.
    
    setup_and_run = (
        "apk add --no-cache git curl >/dev/null && "
        "git clone https://github.com/ivicanikolicsg/MAIAN.git /app >/dev/null && "
        "cd /app/tool && "
        f"python maian.py -s /contract.sol -c {check_type}"
    )
    
    cmd = [
        "docker", "run", "--rm", "--name", job_id,
        "-v", f"{os.getcwd()}/contract.sol:/contract.sol",
        image,
        "sh", "-c", setup_and_run
    ]
    
    print(f"DEBUG: Running MAIAN {check_type} check...", file=sys.stderr, flush=True)
    
    try:
        process = subprocess.Popen(
            cmd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, 
            text=True, 
            bufsize=1
        )
        
        logs = []
        while True:
            line = process.stdout.readline()
            if not line and process.poll() is not None:
                break
            if line:
                line = line.strip()
                if line:
                    print(f"MAIAN: {line}", file=sys.stderr, flush=True)
                    logs.append(line)
        
        process.wait()
        
        return {
            "check_type": check_type,
            "logs": logs,
            "success": process.returncode == 0
        }
             
    except Exception as e:
        return {"error": str(e)}
    finally:
        if os.path.exists(temp_file):
            os.remove(temp_file)

def main(sol_file_content: str = "pragma solidity ^0.4.19; contract Test { function f() public { uint x = 1; } }"):
    print(json.dumps(run_maian(sol_file_content), indent=2), flush=True)

if __name__ == "__main__":
    main()
