#!/usr/bin/env python3
"""
Kube-bench Tool
Checks whether Kubernetes is deployed according to security best practices as defined in the CIS Kubernetes Benchmark.
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
    Execute Kube-bench scan.
    """
    # Kube-bench usually needs a config directory and depends on the cluster type.
    
    kb_path = shutil.which("kube-bench")
    if not kb_path:
        if os.path.exists("/usr/local/bin/kube-bench"):
            kb_path = "/usr/local/bin/kube-bench"
        else:
            return {"status": "error", "message": "kube-bench binary not found."}

    # Construct command
    # --json : Output JSON
    command = [kb_path, "--json"]

    # Extra arguments (e.g., --benchmark cis-1.23)
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

        output_lines = []
        for line in process.stdout:
            line = line.strip()
            if line:
                # Kube-bench output can be large, we'll try to detect if it's logging or the json
                if not line.startswith('{') and not line.startswith('['):
                    print(f"KUBE-BENCH: {line}", file=sys.stderr, flush=True)
                output_lines.append(line)

        process.wait()
        
        status = "success" if process.returncode == 0 else "error"
        
        # Try to parse the last part of output as JSON
        full_output = "\n".join(output_lines)
        results = {}
        try:
            # Find the start of JSON
            start_idx = full_output.find('{')
            if start_idx == -1:
                start_idx = full_output.find('[')
            
            if start_idx != -1:
                results = json.loads(full_output[start_idx:])
            else:
                results = {"raw_output": full_output}
        except:
            results = {"raw_output": full_output}

        return {
            "status": status,
            "message": "Kube-bench scan complete.",
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
