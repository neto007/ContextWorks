import subprocess
import os
import sys
import json

def run_oyente(
    sol_file_content: str = "",
):
    """
    Run Oyente Smart Contract Security Tool.
    
    Args:
        sol_file_content: Solidity contract code.
    """
    # Oyente has a docker image: luongnguyen/oyente
    image = "luongnguyen/oyente"
    job_id = os.environ.get("WM_JOB_ID", "local_test_oyente")
    
    # Write to temp file
    temp_file = "contract.sol"
    with open(temp_file, "w") as f:
        f.write(sol_file_content)
        
    cmd = [
        "docker", "run", "--rm", "--name", job_id,
        "-v", f"{os.getcwd()}/contract.sol:/oyente/oyente/contract.sol",
        image,
        "python", "oyente.py", "-s", "contract.sol"
    ]
    
    print(f"DEBUG: Running Oyente scan...", file=sys.stderr, flush=True)
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # Oyente output is usually text with "Vulnerability" mentions.
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

def main(sol_file_content: str = "pragma solidity ^0.4.19; contract Test { function f() public { uint x = 1; } }"):
    print(json.dumps(run_oyente(sol_file_content), indent=2), flush=True)

if __name__ == "__main__":
    main()
