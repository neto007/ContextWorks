#!/usr/bin/env python3
"""
Murphysec Tool
Open source security scanner.
"""
import sys
import json
import subprocess
import shutil
import shlex
import os

def main(**args):
    """
    Execute Murphysec.
    """
    target = args.get('target', '.')
    
    ms_path = shutil.which("murphysec")
    if not ms_path:
        return {"status": "error", "message": "murphysec binary not found."}

    # Construct command
    # scan <target>
    # --json : JSON output
    command = [ms_path, "scan", target, "--json"]

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
                print(f"MURPHYSEC: {line}", file=sys.stderr, flush=True)
                output_lines.append(line)

        process.wait()
        
        status = "success" if process.returncode == 0 else "error"
        
        full_output = "\n".join(output_lines)
        results = {}
        try:
            start_idx = full_output.find('{')
            if start_idx != -1:
                results = json.loads(full_output[start_idx:])
            else:
                results = {"raw_output": full_output}
        except:
             results = {"raw_output": full_output}

        return {
            "status": status,
            "message": "Murphysec scan complete.",
            "data": results
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
