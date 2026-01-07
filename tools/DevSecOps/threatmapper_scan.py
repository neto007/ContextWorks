#!/usr/bin/env python3
"""
ThreatMapper Tool
Deepfence ThreatMapper scanner.
"""
import sys
import json
import subprocess
import shutil
import shlex
import os

def main(**args):
    """
    Execute ThreatMapper scanner.
    """
    # ThreatMapper usually has a CLI component (secret scanner or vulnerability scanner)
    tm_path = shutil.which("vulnerability-scanner") 
    if not tm_path:
        # Fallback to secrets
        tm_path = shutil.which("secret-scanner")
    
    if not tm_path:
        return {"status": "error", "message": "Deepfence scanner binaries not found."}

    # Construct command
    command = [tm_path]

    # Extra arguments
    extra_args = args.get('arguments')
    target = args.get('target')
    
    if target:
        command.extend(["-image-name", target])

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
                print(f"THREATMAPPER: {line}", file=sys.stderr, flush=True)
                output_lines.append(line)

        process.wait()
        
        status = "success" if process.returncode == 0 else "error"

        return {
            "status": status,
            "message": "ThreatMapper scan complete.",
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
