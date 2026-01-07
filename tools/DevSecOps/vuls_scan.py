#!/usr/bin/env python3
"""
Vuls Tool
Agentless vulnerability scanner for Linux/FreeBSD.
"""
import sys
import json
import subprocess
import shutil
import shlex
import os

def main(**args):
    """
    Execute Vuls.
    """
    # Vuls needs a set of steps: config, prepare, scan, report
    vuls_path = shutil.which("vuls")
    if not vuls_path:
        return {"status": "error", "message": "vuls binary not found."}

    # Construct command
    # e.g., vuls scan
    command = [vuls_path, "scan"]

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
                print(f"VULS: {line}", file=sys.stderr, flush=True)
                output_lines.append(line)

        process.wait()
        
        status = "success" if process.returncode == 0 else "error"

        return {
            "status": status,
            "message": "Vuls complete.",
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
