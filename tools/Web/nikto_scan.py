#!/usr/bin/env python3
"""
Nikto Scan Tool
Executes Nikto web server scanner with advanced configuration options.
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
    Execute Nikto scan..
    """
    target = args.get('target')
    if not target:
        return {"status": "error", "message": "Target is required"}

    # Check for nikto
    nikto_path = shutil.which("nikto")
    if not nikto_path:
        # Fallback path check
        if os.path.exists("/usr/bin/nikto"):
            nikto_path = "/usr/bin/nikto"
        elif os.path.exists("/usr/local/bin/nikto"):
            nikto_path = "/usr/local/bin/nikto"
        else:
             # If nikto command not found, try looking for nikto.pl 
             if os.path.exists("/usr/bin/nikto.pl"):
                 nikto_path = "/usr/bin/nikto.pl"
             else:
                return {"status": "error", "message": f"nikto binary not found. PATH={os.environ.get('PATH')}"}

    # Sanitize target (remove protocol for host flag if needed, but nikto handles both)
    # Nikto -h accepts URLs or Hostnames.
    target = target.strip()
    
    # Create temp file for JSON output
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp_json:
        json_output_path = tmp_json.name

    # Base command
    # -Format json -o <output_file>
    command = [nikto_path, "-h", target, "-Format", "json", "-o", json_output_path]

    # Port
    port = args.get('port')
    if port:
        command.extend(["-port", str(port)])
        
    # Tuning
    tuning = args.get('tuning')
    if tuning:
        command.extend(["-Tuning", str(tuning)])
        
    # SSL
    if args.get('ssl'):
        command.extend(["-ssl"])

    # Extra arguments
    extra_args = args.get('arguments')
    if extra_args:
        command.extend(shlex.split(extra_args))
        
    # Nikto can be verbose, but we want to stream its stdout to logs
    # It doesn't have a reliable "quiet" mode that still outputs good logs, so we just capture stdout
    
    try:
        # Popen to stream output
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=sys.stderr, # Send stderr directly to system logs
            text=True,
            bufsize=1
        )
        
        # Stream stdout (human readable progress) to stderr for the platform logs
        while True:
            line = process.stdout.readline()
            if not line and process.poll() is not None:
                break
            if line:
                line = line.strip()
                print(f"NIKTO: {line}", file=sys.stderr, flush=True)
                
        # Wait for finish
        process.wait()
        
        status = "success" if process.returncode == 0 else "error"
        
        # Nikto return codes:
        # 0: No vulnerabilities found (sometimes)
        # 1: Vulnerabilities found (sometimes) or error
        # It's inconsistent. We rely on the output file existence and content.
        
        scan_data = {}
        error_details = None

        if os.path.exists(json_output_path) and os.path.getsize(json_output_path) > 0:
            try:
                with open(json_output_path, 'r') as f:
                    scan_data = json.load(f)
                
                # Handle case where Nikto returns a list (often in newer versions)
                if isinstance(scan_data, list):
                    if len(scan_data) > 0:
                        scan_data = scan_data[0]
                    else:
                        scan_data = {}
                
                # If we successfully parsed JSON, consider it a success even if return code was 1 (often means vulns found)
                 # Nikto JSON usually has a "vulnerabilities" list
                status = "success"
                
            except json.JSONDecodeError as e:
                status = "error"
                error_details = f"Failed to parse Nikto JSON output: {str(e)}"
        else:
             if status == "success": # If process claimed success but no file
                 status = "error"
                 error_details = "Nikto finished but produced no output file."
             else:
                 error_details = "Nikto failed with non-zero exit code and produced no output file."

        # Clean up
        if os.path.exists(json_output_path):
            os.remove(json_output_path)

        # Construct summary
        vuln_count = 0
        if "vulnerabilities" in scan_data:
            vuln_count = len(scan_data["vulnerabilities"])
        
        summary = f"Nikto scan complete. Found {vuln_count} items."
        if scan_data.get("banner"):
            summary += f" Server: {scan_data['banner']}"
            
        output_data = {
            "status": status,
            "message": summary,
            "data": scan_data
        }
        
        if error_details:
             output_data["data"]["error_details"] = error_details

        return output_data

    except Exception as e:
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
