#!/usr/bin/env python3
"""
Dockerscan Tool
Analysis tool for Docker images and containers.
"""
import sys
import json
import subprocess
import shutil
import shlex
import os

def main(**args):
    """
    Execute Dockerscan.
    """
    scan_type = args.get('scan_type', 'image') or 'image'
    target = args.get('target')
    
    if not target:
        return {"status": "error", "message": "Target is required"}

    # Check for dockerscan binary
    ds_path = shutil.which("dockerscan")
    if not ds_path:
        return {"status": "error", "message": "dockerscan binary not found."}

    # Construct command
    command = [ds_path, scan_type, target]

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

        output_lines = []
        for line in process.stdout:
            line = line.strip()
            if line:
                print(f"DOCKERSCAN: {line}", file=sys.stderr, flush=True)
                output_lines.append(line)

        process.wait()
        
        status = "success" if process.returncode == 0 else "error"

        return {
            "status": status,
            "message": "Dockerscan complete.",
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
