#!/usr/bin/env python3
"""
Gobuster Scan Tool
Executes Gobuster for directory/file, DNS and VHost busting.
"""
import sys
import json
import subprocess
import shutil
import shlex
import os
import re

def main(**args):
    """
    Execute Gobuster scan.
    """
    target = args.get('target')
    if not target:
        return {"status": "error", "message": "Target is required"}

    # Check for gobuster binary
    bin_path = shutil.which("gobuster")
    if not bin_path:
        if os.path.exists("/usr/local/bin/gobuster"):
            bin_path = "/usr/local/bin/gobuster"
        else:
            return {"status": "error", "message": "gobuster binary not found."}

    mode = args.get('mode', 'dir')
    wordlist = args.get('wordlist', '/usr/share/wordlists/common.txt')
    threads = args.get('threads', 10)
    extensions = args.get('extensions')
    
    # Base command
    command = [
        bin_path, mode,
        "-u", target,
        "-w", wordlist,
        "-t", str(threads),
        "--no-color",
        "--no-error"
    ]

    if extensions and mode == 'dir':
        command.extend(["-x", extensions])

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
        
        results = []
        # Pattern for directory mode: /path (Status: 200) [Size: 123]
        pattern = re.compile(r"(\S+)\s+\(Status:\s+(\d+)\)\s+\[Size:\s+(\d+)\]")

        while True:
            line = process.stdout.readline()
            if not line and process.poll() is not None:
                break
            if line:
                line = line.strip()
                print(f"GOBUSTER: {line}", file=sys.stderr, flush=True)
                
                match = pattern.search(line)
                if match:
                    results.append({
                        "path": match.group(1),
                        "status": int(match.group(2)),
                        "size": int(match.group(3)),
                        "raw": line
                    })
                
        # Wait for finish
        process.wait()
        
        status = "success" if process.returncode == 0 or len(results) > 0 else "error"
        summary = f"Gobuster scan complete. Found {len(results)} items."
        
        return {
            "status": status,
            "message": summary,
            "data": {
                "target": target,
                "mode": mode,
                "results": results
            }
        }

    except Exception as e:
        import traceback
        traceback.print_exc()
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
