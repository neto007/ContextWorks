#!/usr/bin/env python3
import sys
import json
import subprocess
import os
import tempfile

def main(**args):
    url = args.get("url")
    extensions = args.get("extensions", "php,html,js,txt")
    wordlist = args.get("wordlist")
    threads = args.get("threads", 10)
    
    if not url:
        return {"status": "error", "message": "URL is required"}

    # Use a temporary file for JSON output
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
        output_file = tmp.name

    cmd = [
        "dirsearch",
        "-u", url,
        "-e", extensions,
        "-t", str(threads),
        "--format=json",
        "-o", output_file
    ]

    if wordlist:
        cmd.extend(["-w", wordlist])

    print(f"DEBUG: Running command: {' '.join(cmd)}", file=sys.stderr, flush=True)

    try:
        # Run dirsearch. It streams some info to stdout/stderr.
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )

        for line in process.stdout:
            print(f"DIRSEARCH: {line.strip()}", file=sys.stderr, flush=True)

        process.wait()

        # Read the JSON results
        findings = []
        if os.path.exists(output_file) and os.path.getsize(output_file) > 0:
            with open(output_file, 'r') as f:
                try:
                    raw_data = json.load(f)
                    findings = raw_data
                except json.JSONDecodeError:
                    print(f"DEBUG: Could not parse JSON output from {output_file}", file=sys.stderr)
        
        # Cleanup
        if os.path.exists(output_file):
            os.remove(output_file)

        return {
            "status": "success",
            "data": {
                "url": url,
                "findings": findings
            }
        }

    except Exception as e:
        return {"status": "error", "message": f"Execution failed: {str(e)}"}

if __name__ == "__main__":
    params = {}
    if len(sys.argv) > 1:
        try:
            params = json.loads(sys.argv[1])
        except Exception as e:
            print(json.dumps({"status": "error", "message": f"Invalid JSON arguments: {e}"}))
            sys.exit(1)

    print(json.dumps(main(**params), indent=2))
