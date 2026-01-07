#!/usr/bin/env python3
"""
HTTPX Scan Tool
Executes HTTPX for web probing and technology detection.
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
    Execute HTTPX scan.
    """
    target = args.get('target')
    if not target:
        return {"status": "error", "message": "Target is required"}

    # Check for httpx binary
    bin_path = shutil.which("httpx")
    if not bin_path:
        if os.path.exists("/usr/local/bin/httpx"):
            bin_path = "/usr/local/bin/httpx"
        else:
            return {"status": "error", "message": "httpx binary not found."}

    # Create temp file for JSON output
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp_json:
        json_output_path = tmp_json.name

    # Base command
    command = [
        bin_path,
        "-u", target,
        "-json",
        "-o", json_output_path,
        "-no-color"
    ]

    if args.get('title', True):
        command.append("-title")
    if args.get('status_code', True):
        command.append("-sc")
    if args.get('tech_detect', True):
        command.append("-td")
    if args.get('follow_redirects'):
        command.append("-fr")

    # Extra arguments
    extra_args = args.get('arguments')
    if extra_args:
        command.extend(shlex.split(extra_args))

    try:
        # Popen to stream output
        # httpx prints results to stdout and logs/errors to stderr
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, # Merge for easier streaming
            text=True,
            bufsize=1
        )
        
        while True:
            line = process.stdout.readline()
            if not line and process.poll() is not None:
                break
            if line:
                line = line.strip()
                # If it's the JSON result line, we might still want to print it as log
                print(f"HTTPX: {line}", file=sys.stderr, flush=True)
                
        # Wait for finish
        process.wait()
        
        status = "success" if process.returncode == 0 else "error"
        
        results = []
        if os.path.exists(json_output_path) and os.path.getsize(json_output_path) > 0:
            try:
                with open(json_output_path, "r") as f:
                    for line in f:
                        if line.strip():
                            try:
                                results.append(json.loads(line))
                            except:
                                pass
            except Exception as e:
                print(f"Error parsing JSON output: {e}", file=sys.stderr)

        # Cleanup
        if os.path.exists(json_output_path):
            os.remove(json_output_path)

        summary = f"HTTPX scan complete. Found {len(results)} targets/responses."
        
        return {
            "status": status,
            "message": summary,
            "data": {
                "target": target,
                "findings": results
            }
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
        if 'json_output_path' in locals() and os.path.exists(json_output_path):
             os.remove(json_output_path)
        return {
            "status": "error",
            "message": str(e)
        }

if __name__ == "__main__":
    params = {}
    if len(sys.argv) > 1:
        try:
            params = json.loads(sys.argv[1])
        except:
            params = {}
    
    print(json.dumps(main(**params), indent=2))
