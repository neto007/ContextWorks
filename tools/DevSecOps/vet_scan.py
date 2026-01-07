#!/usr/bin/env python3
"""
SafeDep VET Tool
Dependency vulnerability and malicious package scanner.
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
    Execute SafeDep VET.
    
    Args:
        path: Directory or file to scan (default: current directory)
        repository: Git repository URL to clone and scan
        arguments: Additional VET arguments (e.g., --malware-query, --filter)
    """
    vet_path = shutil.which("vet")
    if not vet_path:
        return {"status": "error", "message": "vet binary not found."}

    # Check if we need to clone a repository
    repo_url = args.get('repository')
    temp_dir = None
    
    if repo_url:
        # Clone repository to temp directory
        temp_dir = tempfile.mkdtemp(prefix="vet_scan_")
        print(f"VET: Cloning repository {repo_url}...", file=sys.stderr, flush=True)
        
        try:
            clone_result = subprocess.run(
                ["git", "clone", "--depth", "1", repo_url, temp_dir],
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if clone_result.returncode != 0:
                if temp_dir and os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir)
                return {
                    "status": "error", 
                    "message": f"Failed to clone repository: {clone_result.stderr}"
                }
            
            scan_path = temp_dir
            print(f"VET: Repository cloned to {temp_dir}", file=sys.stderr, flush=True)
            
        except subprocess.TimeoutExpired:
            if temp_dir and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
            return {"status": "error", "message": "Repository clone timeout (5 minutes)"}
        except Exception as e:
            if temp_dir and os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
            return {"status": "error", "message": f"Clone error: {str(e)}"}
    else:
        # Get scan path (default to current directory)
        scan_path = args.get('path', '.')
    
    # Construct command: vet scan -D <path>
    command = [vet_path, "scan", "-D", scan_path]

    # Extra arguments (e.g., --malware-query, --filter, etc.)
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
                print(f"VET: {line}", file=sys.stderr, flush=True)
                output_lines.append(line)

        process.wait()
        
        status = "success" if process.returncode == 0 else "error"

        return {
            "status": status,
            "message": "VET scan complete.",
            "data": {
                "raw_output": "\n".join(output_lines)
            }
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}
    finally:
        # Cleanup temp directory if it was created
        if temp_dir and os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
            print(f"VET: Cleaned up temporary directory", file=sys.stderr, flush=True)

if __name__ == "__main__":
    params = {}
    if len(sys.argv) > 1:
        try:
            params = json.loads(sys.argv[1])
        except:
            params = {}
    print(json.dumps(main(**params), indent=2))
