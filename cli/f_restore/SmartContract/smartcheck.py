import subprocess
import os
import sys
import json

def run_smartcheck(
    sol_file_content: str = "",
):
    """
    Run SmartCheck Smart Contract Security Tool.
    
    Args:
        sol_file_content: Solidity contract code.
    """
    # SmartCheck image: smartdec/smartcheck
    image = "smartdec/smartcheck"
    job_id = os.environ.get("WM_JOB_ID", "local_test_smartcheck")
    
    # Write to temp file
    temp_file = "contract.sol"
    with open(temp_file, "w") as f:
        f.write(sol_file_content)
        
    cmd = [
        "docker", "run", "--rm", "--name", job_id,
        "-v", f"{os.getcwd()}/contract.sol:/contract.sol",
        image,
        "smartcheck", "-p", "/contract.sol"
    ]
    
    print(f"DEBUG: Running SmartCheck scan...", file=sys.stderr, flush=True)
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "success": result.returncode == 0
        }
             
    except Exception as e:
        return {"error": str(e)}
    finally:
        if os.path.exists(temp_file):
            os.remove(temp_file)

def main(sol_file_content: str = "pragma solidity ^0.5.0; contract Test { function f() public { uint x = 1; } }"):
    print(json.dumps(run_smartcheck(sol_file_content), indent=2), flush=True)

if __name__ == "__main__":
    main()
