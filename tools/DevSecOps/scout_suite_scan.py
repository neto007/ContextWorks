#!/usr/bin/env python3
"""
Scout-suite Tool
Multi-cloud security auditing tool.
"""
import sys
import json
import subprocess
import shutil
import shlex
import os
import glob

def main(**args):
    """
    Execute Scout-suite.
    """
    provider = args.get('provider', 'aws')
    
    scout_path = shutil.which("scout")
    if not scout_path:
        return {"status": "error", "message": "scout binary not found."}

    # Scout suite produces an HTML report and a JSON data file
    # Inside scout_report/scout-suite-report/inc-gen/
    
    command = [scout_path, provider]

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
            print(f"SCOUT-SUITE: {line.strip()}", file=sys.stderr, flush=True)

        process.wait()
        
        status = "success" if process.returncode == 0 else "error"
        
        # Look for the JSON data file
        json_file = None
        data_files = glob.glob("scout_report/scout-suite-report/inc-gen/*.js") # It often uses .js which is JSON assigned to a variable
        if not data_files:
             data_files = glob.glob("scout_report/scout-suite-report/inc-gen/*.json")
             
        results = {"message": "Scan complete. Check logs for details."}
        if data_files:
             # Basic extraction for now
             results = {"report_files": data_files}

        return {
            "status": status,
            "message": "Scout-suite scan complete.",
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
