import subprocess
import os
import sys
import json

def run_mythril(
    contract_address: str = None,
    sol_file_content: str = None,
    level: str = "low"
):
    """
    Run Mythril Security Scanner for Ethereum Smart Contracts.
    
    Args:
        contract_address: Address of a contract on the blockchain (requires RPC).
        sol_file_content: Content of a Solidity file to scan.
        level: Scanning level (low, medium, high).
    """
    # Mythril has an official docker image: mythril/myth
    image = "mythril/myth"
    job_id = os.environ.get("WM_JOB_ID", "local_test_mythril")
    
    cmd_base = ["docker", "run", "--rm", "--name", job_id, image]
    
    if sol_file_content:
        # Write to temp file and mount it
        temp_file = "contract.sol"
        with open(temp_file, "w") as f:
            f.write(sol_file_content)
        
        # Mythril command: analyze <file>
        cmd = cmd_base + ["analyze", "/contract.sol", "-o", "json"]
        # Need to mount current dir to /
        cmd.insert(3, "-v")
        cmd.insert(4, f"{os.getcwd()}/contract.sol:/contract.sol")
    elif contract_address:
         # analyze -a <address>
         cmd = cmd_base + ["analyze", "-a", contract_address, "-o", "json"]
    else:
        return {"error": "Please provide either contract_address or sol_file_content."}

    print(f"DEBUG: Running Mythril analyze...", file=sys.stderr, flush=True)
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0 and not result.stdout:
             return {"error": "Mythril failed", "details": result.stderr}
             
        # Parse JSON output
        try:
             json_out = json.loads(result.stdout)
             return json_out
        except:
             return {"raw_output": result.stdout, "details": result.stderr}
             
    except Exception as e:
        return {"error": str(e)}
    finally:
        if sol_file_content and os.path.exists("contract.sol"):
            os.remove("contract.sol")

def main(sol_file_content: str = "pragma solidity ^0.5.0; contract Test { function f() public { uint x = 1; } }"):
    print(json.dumps(run_mythril(sol_file_content=sol_file_content), indent=2), flush=True)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # If arg is address-like, treat as address, else as file content?
        # For simplicity, default main.
        main()
    else:
        main()
