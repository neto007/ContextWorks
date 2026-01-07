#!/usr/bin/env python3
"""
Feroxbuster Scan Tool
Executes Feroxbuster directory fuzzer.
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
    Execute Feroxbuster scan.
    """
    target = args.get('target')
    if not target:
        return {"status": "error", "message": "Target is required"}

    # Check for feroxbuster binary
    ferox_path = shutil.which("feroxbuster")
    if not ferox_path:
        # Fallback path check
        if os.path.exists("/usr/local/bin/feroxbuster"):
            ferox_path = "/usr/local/bin/feroxbuster"
        else:
            return {"status": "error", "message": "feroxbuster binary not found."}

    # Sanitize target logic
    if "://" not in target:
         target = f"https://{target}"

    # Create temp file for JSON output
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp_json:
        json_output_path = tmp_json.name

    # Construct command
    # --url : Target URL
    # --json : Output to stdout in JSON format
    # --output : Write results to file
    # --no-state : Don't create .state files
    # --silent : Reduce noise
    command = [
        ferox_path,
        "--url", target,
        "--json",
        "--output", json_output_path,
        "--no-state",
        "--silent"
    ]

    # Wordlist
    wordlist = args.get('wordlist')
    if wordlist:
        command.extend(["--wordlist", wordlist])
    elif os.path.exists("/usr/share/wordlists/common.txt"):
        command.extend(["--wordlist", "/usr/share/wordlists/common.txt"])

    # Threads
    threads = args.get('threads')
    if threads:
        command.extend(["--threads", str(threads)])

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
                print(f"FEROXBUSTER: {line.strip()}", file=sys.stderr, flush=True)
                
        process.wait()
        
        status = "success" if process.returncode == 0 else "error"
        results = []
        
        if os.path.exists(json_output_path) and os.path.getsize(json_output_path) > 0:
            with open(json_output_path, "r") as f:
                for line in f:
                    if line.strip():
                        try:
                            results.append(json.loads(line))
                        except:
                            pass
        
        # Clean up
        if os.path.exists(json_output_path):
            os.remove(json_output_path)

        return {
            "status": status,
            "message": f"Feroxbuster scan complete. Found {len(results)} items.",
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
