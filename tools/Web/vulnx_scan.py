#!/usr/bin/env python3
"""
VulnX Tool
CMS Vulnerability Scanner and Exploiter.
"""
import sys
import json
import subprocess
import shutil
import shlex
import os
import re

def main(**args):
    """
    Execute VulnX.
    """
    target = args.get('target')
    if not target:
        return {"status": "error", "message": "Target is required"}

    # Check for vulnx binary/script
    # Assuming vulnx is installed in the container
    vulnx_path = shutil.which("vulnx")
    if not vulnx_path:
        # Check common locations
        if os.path.exists("/usr/local/bin/vulnx"):
            vulnx_path = "/usr/local/bin/vulnx"
        elif os.path.exists("/vulnx/vulnx.py"):
            vulnx_path = "python3 /vulnx/vulnx.py"
        else:
            return {"status": "error", "message": "vulnx not found."}

    # Construct command
    # -u : Target
    # --cms : Search CMS info
    command = shlex.split(vulnx_path) + ["-u", target, "--cms"]

    # Extra arguments
    extra_args = args.get('arguments')
    if extra_args:
        command.extend(shlex.split(extra_args))

    try:
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )

        results = []
        for line in process.stdout:
            line = line.strip()
            if not line: continue
            
            print(f"VULNX: {line}", file=sys.stderr, flush=True)
            
            # Strip ANSI codes for parsing
            clean_line = re.sub(r'\x1B(?:[@-Z\\-_]|\[[0-?]*[ -/]*[@-~])', '', line)
            
            if clean_line.startswith("[+]") or clean_line.startswith("[-]"):
                parts = clean_line.split(":", 1)
                if len(parts) == 2:
                    key = parts[0].replace("[+]", "").replace("[-]", "").strip()
                    value = parts[1].strip()
                    results.append({"key": key, "value": value})

        process.wait()
        
        status = "success" if process.returncode == 0 else "error"

        return {
            "status": status,
            "message": f"VulnX scan complete. Found {len(results)} metadata items.",
            "data": {
                "findings": results
            }
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    params = {}
    if len(sys.argv) > 1:
        try:
            params = json.loads(sys.argv[1])
        except:
            params = {}
    print(json.dumps(main(**params), indent=2))
