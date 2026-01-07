#!/usr/bin/env python3
"""
FFUF Scan Tool
Executes Fuzz Faster U Fool (FFUF).
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
    Execute FFUF scan.
    """
    target = args.get('target')
    if not target:
        return {"status": "error", "message": "Target is required"}

    # Check for ffuf binary
    ffuf_path = shutil.which("ffuf")
    if not ffuf_path:
        if os.path.exists("/usr/local/bin/ffuf"):
            ffuf_path = "/usr/local/bin/ffuf"
        else:
            return {"status": "error", "message": "ffuf binary not found."}

    # Sanitize target logic
    if "://" not in target:
         target = f"https://{target}"
    
    # Ensure FUZZ keyword is present
    if "FUZZ" not in target:
        if not target.endswith("/"):
            target += "/"
        target += "FUZZ"

    # Create temp file for JSON output
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp_json:
        json_output_path = tmp_json.name

    # Construct command
    # -u : Target URL
    # -o : Output file
    # -of: Output format
    # -s : Silent
    command = [
        ffuf_path,
        "-u", target,
        "-o", json_output_path,
        "-of", "json",
        "-s"
    ]

    # Wordlist
    wordlist = args.get('wordlist')
    if wordlist:
        command.extend(["-w", wordlist])
    elif os.path.exists("/usr/share/wordlists/common.txt"):
        command.extend(["-w", "/usr/share/wordlists/common.txt"])

    # Extra arguments
    extra_args = args.get('arguments')
    if extra_args:
        command.extend(shlex.split(extra_args))

    try:
        # Popen to stream output
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )

        while True:
            line = process.stdout.readline()
            if not line and process.poll() is not None:
                break
            if line:
                # FFUF silent might still output results to stdout.
                # We'll print them to stderr for logs.
                print(f"FFUF: {line.strip()}", file=sys.stderr, flush=True)
                
        process.wait()
        
        status = "success" if process.returncode == 0 else "error"
        results = []
        
        if os.path.exists(json_output_path) and os.path.getsize(json_output_path) > 0:
            try:
                with open(json_output_path, "r") as f:
                    data = json.load(f)
                    results = data.get("results", [])
            except:
                pass
        
        # Clean up
        if os.path.exists(json_output_path):
            os.remove(json_output_path)

        return {
            "status": status,
            "message": f"FFUF scan complete. Found {len(results)} items.",
            "data": {
                "target": target,
                "results": results
            }
        }

    except Exception as e:
        if 'json_output_path' in locals() and os.path.exists(json_output_path):
             os.remove(json_output_path)
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    params = {}
    if len(sys.argv) > 1:
        try:
            params = json.loads(sys.argv[1])
        except:
            params = {}
    print(json.dumps(main(**params), indent=2))
