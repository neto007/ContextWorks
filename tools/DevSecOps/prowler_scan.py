#!/usr/bin/env python3
"""
Prowler Tool
Auditing and security tool for AWS, Azure, and Google Cloud.
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
    Execute Prowler scan.
    """
    cloud_provider = args.get('provider', 'aws')
    
    prowler_path = shutil.which("prowler")
    if not prowler_path:
        return {"status": "error", "message": "prowler binary not found."}

    # Output file
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp:
        output_path = tmp.name

    # Construct command
    # -M json : Output JSON
    # --output-path : Output directory
    # --output-filename : Output filename
    output_dir = os.path.dirname(output_path)
    output_filename = os.path.basename(output_path)

    command = [prowler_path, cloud_provider, "--output-format", "json", "--output-directory", output_dir, "--output-filename", output_filename]

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
            print(f"PROWLER: {line.strip()}", file=sys.stderr, flush=True)

        process.wait()
        
        status = "success" if process.returncode == 0 else "error"
        results = {}
        
        # Prowler appends format to filename e.g. .json
        actual_json_path = output_path + ".json"
        
        if os.path.exists(actual_json_path) and os.path.getsize(actual_json_path) > 0:
            with open(actual_json_path, "r") as f:
                try:
                    results = json.load(f)
                except:
                    pass
            os.remove(actual_json_path)
        elif os.path.exists(output_path):
             os.remove(output_path)

        return {
            "status": status,
            "message": "Prowler scan complete.",
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
