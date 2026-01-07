#!/usr/bin/env python3
"""
Trufflehog Tool
Finds secrets in repositories and filesystems.
"""
import sys
import json
import subprocess
import shutil
import shlex
import os

def main(**args):
    """
    Execute Trufflehog.
    """
    target = args.get('target')
    scan_type = args.get('scan_type', 'git')
    
    if not target:
        return {"status": "error", "message": "Target is required"}

    th_path = shutil.which("trufflehog")
    if not th_path:
        return {"status": "error", "message": "trufflehog binary not found."}

    # Construct command
    # --json : JSON output
    command = [th_path, scan_type, target, "--json"]

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

        results = []
        for line in process.stdout:
            line = line.strip()
            if line:
                try:
                    # Trufflehog outputs one JSON object per line
                    results.append(json.loads(line))
                except:
                    print(f"TRUFFLEHOG: {line}", file=sys.stderr, flush=True)

        process.wait()
        
        status = "success" if process.returncode == 0 else "error"

        return {
            "status": status,
            "message": "Trufflehog scan complete.",
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
