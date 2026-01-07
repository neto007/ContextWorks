#!/usr/bin/env python3
"""
Katana Tool
Next-generation crawling and spidering framework.
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
    Execute Katana.
    """
    target = args.get('target')
    if not target:
        return {"status": "error", "message": "Target is required"}

    # Check for katana binary
    katana_path = shutil.which("katana")
    if not katana_path:
        if os.path.exists("/usr/local/bin/katana"):
            katana_path = "/usr/local/bin/katana"
        else:
            return {"status": "error", "message": "katana binary not found."}

    # Output file
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
        output_path = tmp.name

    # Construct command
    # -u : Target URL
    # -j : JSON output format
    # -o : Output file
    # -nc: No color
    # -silent: Silent mode
    command = [katana_path, "-u", target, "-j", "-o", output_path, "-nc", "-silent"]

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
            # Katana with -j usually outputs json objects to stdout too
            print(f"KATANA: {line.strip()}", file=sys.stderr, flush=True)

        process.wait()
        
        status = "success" if process.returncode == 0 else "error"
        results = []
        
        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            with open(output_path, "r") as f:
                for line in f:
                    if line.strip():
                        try:
                            results.append(json.loads(line))
                        except:
                            pass
            os.remove(output_path)

        return {
            "status": status,
            "message": f"Katana crawl complete. Found {len(results)} items.",
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
