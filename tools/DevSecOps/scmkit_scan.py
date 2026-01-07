#!/usr/bin/env python3
"""
SCMKit Tool
Toolkit for SCM (Source Control Management) security auditing.
"""
import sys
import json
import subprocess
import shutil
import shlex
import os

def main(**args):
    """
    Execute SCMKit.
    """
    # SCMKit is typically a .NET application or run via dotnet/script
    # If we are using a wrapper or pre-built binary:
    scmkit_path = shutil.which("scmkit")
    if not scmkit_path:
        if os.path.exists("/usr/local/bin/scmkit"):
            scmkit_path = "/usr/local/bin/scmkit"
        else:
            return {"status": "error", "message": "scmkit binary not found."}

    # Construct command
    command = [scmkit_path]

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
                print(f"SCMKIT: {line}", file=sys.stderr, flush=True)
                output_lines.append(line)

        process.wait()
        
        status = "success" if process.returncode == 0 else "error"

        return {
            "status": status,
            "message": "SCMKit complete.",
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
