#!/usr/bin/env python3
"""
Veinmind Tool
Container security toolset.
"""
import sys
import json
import subprocess
import shutil
import shlex
import os

def main(**args):
    """
    Execute Veinmind.
    """
    target_type = args.get('target_type', 'image')
    target = args.get('target')
    
    if not target:
        return {"status": "error", "message": "Target is required"}

    # Veinmind is usually run via veinmind-runner
    runner_path = shutil.which("veinmind-runner")
    if not runner_path:
        if os.path.exists("/usr/local/bin/veinmind-runner"):
            runner_path = "/usr/local/bin/veinmind-runner"
        else:
            return {"status": "error", "message": "veinmind-runner not found."}

    # Construct command
    # scan <type> <target>
    command = [runner_path, "scan", target_type, target]

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
                print(f"VEINMIND: {line}", file=sys.stderr, flush=True)
                output_lines.append(line)

        process.wait()
        
        status = "success" if process.returncode == 0 else "error"

        return {
            "status": status,
            "message": "Veinmind scan complete.",
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
