#!/usr/bin/env python3
"""
Cloudpeler Tool
Auditor for cloud permissions.
"""
import sys
import json
import subprocess
import shutil
import shlex
import os

def main(**args):
    """
    Execute Cloudpeler.
    """
    cloudpeler_path = shutil.which("cloudpeler")
    if not cloudpeler_path:
        if os.path.exists("/usr/local/bin/cloudpeler"):
            cloudpeler_path = "/usr/local/bin/cloudpeler"
        else:
             return {"status": "error", "message": "cloudpeler binary not found."}

    # Construct command
    command = [cloud_peler_path]

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
                print(f"CLOUDPELER: {line}", file=sys.stderr, flush=True)
                output_lines.append(line)

        process.wait()
        
        status = "success" if process.returncode == 0 else "error"

        return {
            "status": status,
            "message": "Cloudpeler complete.",
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
