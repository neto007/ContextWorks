#!/usr/bin/env python3
import sys
import json
import subprocess
import re
import os

def execute_command(cmd):
    """Executes a command and streams output to stderr for live platform logs."""
    print(f"DEBUG: Running command: {' '.join(cmd)}", file=sys.stderr, flush=True)
    
    findings = []
    
    # Dirb output is very verbose. We look for lines starting with '+'
    # Example: "+ http://example.com/index.html (CODE:200|SIZE:1024)"
    finding_pattern = re.compile(r"^\+\s+(?P<url>https?://\S+)\s+\(CODE:(?P<code>\d+)\|SIZE:(?P<size>\d+)\)")

    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1
    )

    for line in process.stdout:
        line = line.strip()
        if not line:
            continue
            
        print(f"DIRB: {line}", file=sys.stderr, flush=True)
        
        match = finding_pattern.match(line)
        if match:
            findings.append(match.groupdict())
        elif line.startswith("DIRECTORY:"):
            # Also capture directories
            findings.append({"type": "directory", "info": line})

def main(**args):
    target = args.get("target")
    wordlist = args.get("wordlist")
    
    if not target:
        return {"status": "error", "message": "Target URL is required"}

    cmd = ["dirb", target]
    if wordlist:
        cmd.append(wordlist)
    
    findings, exit_code = execute_command(cmd)

    return {
        "status": "success" if exit_code in [0, 1] else "error",
        "data": {
            "target": target,
            "findings_count": len(findings),
            "findings": findings
        }
    }

if __name__ == "__main__":
    params = {}
    if len(sys.argv) > 1:
        try:
            params = json.loads(sys.argv[1])
        except Exception as e:
            print(json.dumps({"status": "error", "message": f"Invalid JSON arguments: {e}"}))
            sys.exit(1)
            
    print(json.dumps(main(**params), indent=2))
