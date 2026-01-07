#!/usr/bin/env python3
"""
Dalfox Tool
XSS scanner and parameter analyzer.
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
    Execute Dalfox.
    """
    target = args.get('target')
    if not target:
        return {"status": "error", "message": "Target is required"}

    # Check for dalfox binary
    dalfox_path = shutil.which("dalfox")
    if not dalfox_path:
        return {"status": "error", "message": "dalfox binary not found."}

    # Output file
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
        output_path = tmp.name

    # Construct command
    # url : Target URL
    # --format json : Output in JSON
    # -o : Output file
    command = [dalfox_path, "url", target, "--format", "json", "-o", output_path]

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
            print(f"DALFOX: {line.strip()}", file=sys.stderr, flush=True)

        process.wait()
        
        status = "success" if process.returncode == 0 else "error"
        results = []
        
        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            with open(output_path, "r") as f:
                content = f.read()
                try:
                    results = json.loads(content)
                except:
                    # Try NDJSON
                    results = [json.loads(line) for line in content.splitlines() if line.strip()]
            os.remove(output_path)

        return {
            "status": status,
            "message": f"Dalfox complete. Found {len(results)} vulnerabilities.",
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
