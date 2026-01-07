#!/usr/bin/env python3
"""
Wafw00f Tool
Web Application Firewall Fingerprinting Tool.
"""
import sys
import json
import subprocess
import shutil
import shlex
import os
import tempfile

def main(**args):
    """
    Execute Wafw00f.
    """
    target = args.get('target')
    if not target:
        return {"status": "error", "message": "Target is required"}

    # Check for wafw00f binary
    waf_path = shutil.which("wafw00f")
    if not waf_path:
        return {"status": "error", "message": "wafw00f binary not found."}

    # Output file
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
        output_path = tmp.name

    # Construct command
    # -f json : JSON format
    # -o : Output file
    command = [waf_path, target, "-f", "json", "-o", output_path]

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

        for line in process.stdout:
            print(f"WAFW00F: {line.strip()}", file=sys.stderr, flush=True)

        process.wait()
        
        status = "success" if process.returncode == 0 else "error"
        results = []
        
        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            with open(output_path, "r") as f:
                try:
                    results = json.load(f)
                except:
                    pass
            os.remove(output_path)

        return {
            "status": status,
            "message": "Wafw00f complete.",
            "data": results
        }

    except Exception as e:
        if os.path.exists(output_path):
            os.remove(output_path)
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    params = {}
    if len(sys.argv) > 1:
        try:
            params = json.loads(sys.argv[1])
        except:
            params = {}
    print(json.dumps(main(**params), indent=2))
