#!/usr/bin/env python3
"""
Kubiscan Tool
A tool for scanning Kubernetes clusters for risky permissions.
"""
import sys
import json
import subprocess
import shutil
import shlex
import os

def main(**args):
    """
    Execute Kubiscan.
    """
    # Kubiscan usually runs as a python script
    kb_path = "python3 /opt/kubiscan/KubiScan.py"
    
    command = shlex.split(kb_path)
    
    # Extra arguments (e.g., -rs for risky subjects)
    extra_args = args.get('arguments')
    if extra_args:
        command.extend(shlex.split(extra_args))
    else:
        command.append("-rs") # Default: show risky subjects

    try:
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )

        output_lines = []
        for line in process.stdout:
            line = line.strip()
            if line:
                print(f"KUBISCAN: {line}", file=sys.stderr, flush=True)
                output_lines.append(line)

        process.wait()
        
        status = "success" if process.returncode == 0 else "error"

        return {
            "status": status,
            "message": "Kubiscan complete.",
            "data": {
                "raw_output": "\n".join(output_lines)
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
