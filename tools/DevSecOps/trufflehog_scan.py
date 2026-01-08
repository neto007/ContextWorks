#!/usr/bin/env python3
"""
Trufflehog Tool
Finds secrets in repositories and filesystems.
Refactored to align with robust CLI implementation.
"""
import sys
import json
import subprocess
import shutil
import shlex
import os

def main(**args):
    """
    Execute Trufflehog.
    """
    # 1. Parse Arguments
    target = args.get('target', '').strip()
    scan_type = args.get('scan_type', 'git').strip().replace('"', '').replace("'", "")
    only_verified = args.get('only_verified', True)
    
    # Handle boolean input that might come as string from some UIs
    if isinstance(only_verified, str):
        only_verified = only_verified.lower() == 'true'

    if not target:
        return {"status": "error", "message": "Target is required"}

    # 2. Check Dependency
    th_path = shutil.which("trufflehog")
    if not th_path:
        # If running in environment without trufflehog, try to find it in likely places or fail
        # But this script is intended to run inside the docker image where it IS installed.
        return {"status": "error", "message": "trufflehog binary not found in container"}

    # 3. Construct Command
    # Start with base binary
    command = [th_path]
    
    # Add scan type command (e.g. 'git', 'filesystem')
    command.append(scan_type)
    
    # Add target
    command.append(target)
    
    # Add flags
    command.append("--json")
    
    if only_verified:
        command.append("--only-verified")

    # Extra arguments
    extra_args = args.get('arguments')
    if extra_args:
        command.extend(shlex.split(extra_args))

    print(f"DEBUG: Running command: {command}", file=sys.stderr, flush=True)

    try:
        # 4. Execute Process
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, # Capture stderr to debug/ignore logs
            text=True, # We'll try text mode first, but manual read loop is safer for bytes if encoding issues arise.
            # However, for simplicity in this wrapper, text=True with utf-8 default is usually fine for JSON.
            bufsize=1
        )

        results = []
        
        # 5. Read Output Loop
        # We read line by line. TruffleHog V3 outputs NDJSON.
        for line in process.stdout:
            line = line.strip()
            if not line:
                continue
                
            try:
                obj = json.loads(line)
                
                # Transform/Simplify for Windmill output if necessary, 
                # or just pass through the full object.
                # Let's clean it up slightly for better display in UI tables
                
                # Verify if it's a valid finding object by checking common keys
                if 'SourceMetadata' in obj or 'DetectorName' in obj:
                    results.append(obj)
                
            except json.JSONDecodeError:
                # Not a JSON line, likely a log message that slipped into stdout
                print(f"TRUFFLE_LOG: {line}", file=sys.stderr, flush=True)
            except Exception as e:
                print(f"ERROR parsing line: {e} | Line: {line[:50]}...", file=sys.stderr, flush=True)

        # 6. Wait for completion
        process.wait()
        
        # Check stderr if needed
        # stderr_output = process.stderr.read()
        # if stderr_output:
        #     print(f"STDERR: {stderr_output}", file=sys.stderr)

        status = "success"
        if process.returncode != 0:
            # Trufflehog might return non-zero if secrets are found? 
            # Check docs. V3 usually returns 0 if command ran successfully, 
            # OR might return exit code 183 if secrets found (sometimes).
            # But usually we care if we got results.
            
            # If we got results, it's a success in terms of "the scan worked".
            if not results:
                status = "error" # Or partial?
                print(f"Process exited with {process.returncode}", file=sys.stderr)

        return {
            "status": status,
            "message": f"Trufflehog scan complete. Found {len(results)} secrets.",
            "data": results,
            "raw_command": str(command)
        }

    except Exception as e:
        return {"status": "error", "message": f"Execution failed: {str(e)}"}

if __name__ == "__main__":
    params = {}
    if len(sys.argv) > 1:
        try:
            params = json.loads(sys.argv[1])
        except:
            # If not json, maybe handle simpler args or just empty
            params = {}
    print(json.dumps(main(**params), indent=2))
