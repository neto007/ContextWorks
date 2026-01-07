#!/usr/bin/env python3
"""
Docker Bench Security Tool
Verifies best practices for Docker deployment.
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
    Execute Docker Bench Security.
    """
    # Docker Bench needs access to the host's Docker socket and various config files.
    # In a K8s worker, this is typically done via privileged mounts.
    
    bench_path = "/usr/local/bin/docker-bench-security.sh"
    if not os.path.exists(bench_path):
        return {"status": "error", "message": "docker-bench-security.sh not found."}

    # Docker bench writes to a log directory
    with tempfile.TemporaryDirectory() as tmp_dir:
        command = [bench_path, "-l", "/tmp/bench.log", "-c", "json"]
        
        # Extra arguments
        extra_args = args.get('arguments')
        if extra_args:
            command.extend(shlex.split(extra_args))

        try:
            # We must be careful as this tool usually needs root and mounts.
            # The YAML will handle the privileged execution if needed.
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )

            for line in process.stdout:
                print(f"DOCKER-BENCH: {line.strip()}", file=sys.stderr, flush=True)

            process.wait()
            
            status = "success" if process.returncode == 0 else "error"
            
            # Docker bench JSON output is usually in docker-bench-security.sh.log.json
            # in the current directory or specified path
            results = {}
            json_files = glob.glob("/tmp/bench.log*.json") + glob.glob("*.json")
            if json_files:
                with open(json_files[0], "r") as f:
                    try:
                        results = json.load(f)
                    except:
                        pass

            return {
                "status": status,
                "message": "Docker Bench Security complete.",
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
