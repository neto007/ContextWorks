#!/usr/bin/env python3
"""
gogo Tool
Asset discovery and fingerprinting tool.
"""
import sys
import json
import subprocess
import shutil
import shlex
import os

def main(**args):
    """
    Execute gogo.
    """
    target = args.get('target')
    if not target:
        return {"status": "error", "message": "Target is required"}

    # Check for gogo binary
    gogo_path = shutil.which("gogo") or "/usr/local/bin/gogo"
    if not os.path.exists(gogo_path) and not shutil.which("gogo"):
        return {"status": "error", "message": "gogo binary not found."}

    # Construct command
    # -i : IP/Target
    command = [gogo_path, "-i", target]

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
                print(f"GOGO: {line}", file=sys.stderr, flush=True)
                output_lines.append(line)

        process.wait()
        
        status = "success" if process.returncode == 0 else "error"

        return {
            "status": status,
            "message": "gogo scan complete.",
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
