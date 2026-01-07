#!/usr/bin/env python3
"""
ParamSpider Tool
Mining parameters from dark corners of Web Archives.
"""
import sys
import json
import subprocess
import shutil
import shlex
import os
import tempfile
import glob

def main(**args):
    """
    Execute ParamSpider.
    """
    domain = args.get('domain')
    if not domain:
        return {"status": "error", "message": "Domain is required"}

    # Check for paramspider binary
    ps_path = shutil.which("paramspider")
    if not ps_path:
        return {"status": "error", "message": "paramspider binary not found."}

    # Construct command
    # -d : Domain
    # --stream : Output results to stdout (if supported by version)
    command = [ps_path, "-d", domain]

    # Extra arguments
    extra_args = args.get('arguments')
    if extra_args:
        command.extend(shlex.split(extra_args))

    try:
        # Create a temporary directory to work in
        # ParamSpider creates a 'results' folder
        with tempfile.TemporaryDirectory() as tmp_dir:
            process = subprocess.Popen(
                command,
                cwd=tmp_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )

            for line in process.stdout:
                print(f"PARAMSPIDER: {line.strip()}", file=sys.stderr, flush=True)

            process.wait()
            
            status = "success" if process.returncode == 0 else "error"
            
            # Read results
            all_params = []
            results_path = os.path.join(tmp_dir, "results", f"{domain}.txt")
            if os.path.exists(results_path):
                with open(results_path, "r") as f:
                    all_params = [line.strip() for line in f if line.strip()]
            else:
                # Try glob if file name differs
                files = glob.glob(os.path.join(tmp_dir, "results", "*.txt"))
                for fpath in files:
                    with open(fpath, "r") as f:
                        all_params.extend([l.strip() for l in f if l.strip()])

            return {
                "status": status,
                "message": f"ParamSpider complete. Found {len(all_params)} parameters.",
                "data": {
                    "domain": domain,
                    "parameters": all_params
                }
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
