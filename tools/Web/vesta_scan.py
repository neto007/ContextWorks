#!/usr/bin/env python3
"""
Vesta Tool
Cloud and Container Security Scanner.
"""
import sys
import json
import subprocess
import shutil
import shlex
import os

def main(**args):
    """
    Execute Vesta.
    """
    target = args.get('target')
    # target might be optional for some vesta commands
    
    # Check for vesta binary/script
    vesta_path = shutil.which("vesta") or "/usr/local/bin/vesta"
    if not os.path.exists(vesta_path) and not shutil.which("vesta"):
        # Check if python script
        if os.path.exists("/opt/vesta/vesta.py"):
            vesta_path = "python3 /opt/vesta/vesta.py"
        else:
            return {"status": "error", "message": "vesta not found."}

    # Construct command
    command = shlex.split(vesta_path)
    if target:
        command.append(target)

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
                print(f"VESTA: {line}", file=sys.stderr, flush=True)
                output_lines.append(line)

        process.wait()
        
        status = "success" if process.returncode == 0 else "error"

        return {
            "status": status,
            "message": "Vesta scan complete.",
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
