#!/usr/bin/env python3
"""
Kube-hunter Tool
Hunts for security weaknesses in Kubernetes clusters.
"""
import sys
import json
import subprocess
import shutil
import shlex
import os

def main(**args):
    """
    Execute Kube-hunter.
    """
    target = args.get('target') # e.g., remote URL or node IP
    
    kh_path = shutil.which("kube-hunter")
    if not kh_path:
        return {"status": "error", "message": "kube-hunter binary not found."}

    # Construct command
    # --report json : JSON report
    command = [kh_path, "--report", "json"]

    if target:
        command.extend(["--remote", target])
    else:
        command.append("--pod") # Default to internal pod scan

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
                print(f"KUBE-HUNTER: {line}", file=sys.stderr, flush=True)
                output_lines.append(line)

        process.wait()
        
        status = "success" if process.returncode == 0 else "error"
        
        # Parse JSON from output
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
            "message": "Kube-hunter scan complete.",
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
