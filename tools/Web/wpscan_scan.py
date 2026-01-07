#!/usr/bin/env python3
"""
WPScan Tool
WordPress vulnerability scanner.
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
    Execute WPScan.
    """
    target = args.get('target')
    if not target:
        return {"status": "error", "message": "Target is required"}

    # Check for wpscan binary
    wpscan_path = shutil.which("wpscan")
    if not wpscan_path:
        return {"status": "error", "message": "wpscan binary not found."}

    # Construct command
    # --format json : Output in JSON
    # --no-banner : Cleaner logs
    command = [wpscan_path, "--url", target, "--format", "json", "--no-banner"]

    # API Token
    api_token = args.get('api_token')
    if api_token:
        command.extend(["--api-token", api_token])
    else:
        command.extend(["--random-user-agent"])

    # Extra arguments
    extra_args = args.get('arguments')
    if extra_args:
        command.extend(shlex.split(extra_args))

    try:
        # WPScan outputs JSON to stdout, and logs to stderr
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )

        # Stream stderr for logs
        # This is slightly tricky as stderr might block. 
        # But for WPScan usually logs come first.
        
        # Simple non-blocking read or just let it finish if we only care about FINAL json
        stdout, stderr = process.communicate()
        
        # Print logs to stderr for Windmill
        if stderr:
            for line in stderr.splitlines():
                print(f"WPSCAN: {line}", file=sys.stderr, flush=True)

        process.wait()
        
        status = "success" if process.returncode == 0 else "error"
        
        try:
            results = json.loads(stdout)
        except:
            results = {"raw_output": stdout[:2000]}
            if process.returncode != 0 and not stdout:
                status = "error"

        return {
            "status": status,
            "message": "WPScan complete.",
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
