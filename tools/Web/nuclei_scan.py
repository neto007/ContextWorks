#!/usr/bin/env python3
"""
Nuclei Scan Tool
Executes Nuclei vulnerability scanner.
"""
import sys
import json
import subprocess
import shutil
import shlex
import os
import tempfile
from urllib.parse import urlparse

def main(**args):
    """
    Execute Nuclei scan.
    """
    target = args.get('target')
    if not target:
        return {"status": "error", "message": "Target is required"}

    # Check for nuclei binary
    nuclei_path = shutil.which("nuclei")
    if not nuclei_path:
        # Fallback path check
        if os.path.exists("/usr/local/bin/nuclei"):
            nuclei_path = "/usr/local/bin/nuclei"
        else:
            return {"status": "error", "message": f"nuclei binary not found. PATH={os.environ.get('PATH')}"}

    # Sanitize target logic
    # Nuclei handles URLs well, but usually wants protocol if web scanning
    if "://" not in target and not target.startswith("http"):
         target = f"https://{target}"

    # Create temp file for JSON output
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp_json:
        json_output_path = tmp_json.name

    # Construct command
    # -u target : Target URL
    # -json-export : Output to file
    # -no-color : Clean logs
    # -stats : Show statistics
    command = [
        nuclei_path,
        "-u", target,
        "-json-export", json_output_path,
        "-no-color",
        "-stats"
    ]

    # Templates
    templates = args.get('templates')
    if templates:
        command.extend(["-t", templates])
    
    # Severity
    severity = args.get('severity')
    if severity:
        command.extend(["-severity", severity])

    # Tags
    tags = args.get('tags')
    if tags:
        command.extend(["-tags", tags])

    # Extra arguments
    extra_args = args.get('arguments')
    if extra_args:
        command.extend(shlex.split(extra_args))

    try:
        # Popen to stream output
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE, # Nuclei prints stats/info to stderr usually? Or stdout? Reference says stdout.
            # Nuclei behavior: findings on stdout, stats on stderr usually.
            # Let's verify: The reference script monitored process.stdout.
            # We will monitor stdout and print to sys.stderr (logs).
            text=True,
            bufsize=1
        )
        
        # Stream stdout (Nuclei findings/logs)
        # Note: We merge stderr to stdout or handle both?
        # Let's handle stdout for logs.
        # Wait, if we use -json-export, standard output might be quiet or just finding text.
        
        # We'll use a thread/selector or just simple readline loop if we only care about one stream blocking.
        # But we should probably capture stderr too for errors.
        
        # Simpler approach: Redirect stderr to stdout in Popen so we read all from one pipe
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, # Merge stderr into stdout
            text=True,
            bufsize=1
        )

        while True:
            line = process.stdout.readline()
            if not line and process.poll() is not None:
                break
            if line:
                line = line.strip()
                print(f"NUCLEI: {line}", file=sys.stderr, flush=True)
                
        # Wait for finish
        process.wait()
        
        status = "success" if process.returncode == 0 else "error"
        
        results = []
        error_details = None

        if os.path.exists(json_output_path) and os.path.getsize(json_output_path) > 0:
            try:
                with open(json_output_path, "r") as f:
                    file_content = f.read()
                    
                    # Try to parse as single JSON array first (newer nuclei versions)
                    try:
                        data = json.loads(file_content)
                        if isinstance(data, list):
                            results = data
                        elif isinstance(data, dict):
                            results = [data]
                    except json.JSONDecodeError:
                        # Fallback to NDJSON (line by line)
                        # We re-read lines from the content we just read
                        for line in file_content.splitlines():
                            if line.strip():
                                try:
                                    results.append(json.loads(line))
                                except:
                                    pass
            except Exception as e:
                status = "error"
                error_details = f"Failed to read/parse output: {str(e)}"
        else:
             if process.returncode != 0:
                 status = "error"
                 error_details = "Nuclei failed." # Logs are already streamed

        # Clean up
        if os.path.exists(json_output_path):
            os.remove(json_output_path)

        # Construct summary
        findings_count = len(results)
        summary = f"Nuclei scan complete. Found {findings_count} findings."
        
        output_data = {
            "status": status,
            "message": summary,
            "data": {
                "target": target,
                "findings": results
            }
        }
        
        if error_details:
             output_data["data"]["error_details"] = error_details

        return output_data

    except Exception as e:
        import traceback
        traceback.print_exc()
        if 'json_output_path' in locals() and os.path.exists(json_output_path):
             os.remove(json_output_path)
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

# Small change 1767820028.7892163