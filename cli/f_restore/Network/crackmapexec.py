import subprocess
import os
import sys
import json

def run_crackmapexec(
    protocol: str = "smb",
    target: str = "",
    cmd_args: str = ""
):
    """
    Run CrackMapExec (CME).
    
    Args:
        protocol: Protocol to use (smb, winrm, ssh, ldap, etc.).
        target: Target IP/Network/File.
        cmd_args: Additional arguments for CME.
    """
    image = "byt3bl33d3r/crackmapexec"
    job_id = os.environ.get("WM_JOB_ID", "local_test_cme")
    
    cmd = [
        "docker", "run", "--rm", "--name", job_id,
        image,
        protocol, target
    ] + cmd_args.split()
    
    print(f"DEBUG: Running CrackMapExec {protocol} on {target}...", file=sys.stderr, flush=True)
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "success": result.returncode == 0
        }
    except Exception as e:
        return {"error": str(e)}

def main(protocol: str = "smb", target: str = "127.0.0.1"):
    print(json.dumps(run_crackmapexec(protocol, target), indent=2), flush=True)

if __name__ == "__main__":
    main()
