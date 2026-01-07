#!/usr/bin/env python3
"""
Semgrep Tool
Lightweight static analysis for many languages.
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
    Execute Semgrep.
    """
    target = args.get('target', '.')
    config = args.get('config', 'p/default')
    
    semgrep_path = shutil.which("semgrep")
    if not semgrep_path:
        return {"status": "error", "message": "semgrep binary not found."}

    # Output file
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
        output_path = tmp.name

    # Construct command
    # --json : JSON output
    # --output : Output file
    command = [semgrep_path, "scan", "--json", "--output", output_path, "--config", config, target]

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
            print(f"SEMGREP: {line.strip()}", file=sys.stderr, flush=True)

        process.wait()
        
        status = "success" if process.returncode == 0 else "error"
        results = {}
        
        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            with open(output_path, "r") as f:
                try:
                    results = json.load(f)
                except:
                    pass
            os.remove(output_path)

        return {
            "status": status,
            "message": "Semgrep scan complete.",
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
