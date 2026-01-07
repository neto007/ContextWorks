#!/usr/bin/env python3
"""
Sqlmap Scan Tool
Advanced SQL injection and database takeover tool.
"""
import sys
import json
import subprocess
import shutil
import shlex
import os
import tempfile
import re

def main(**args):
    """
    Execute Sqlmap scan.
    """
    targets = args.get('target')
    if not targets:
        return {"status": "error", "message": "Target is required"}

    # Check for sqlmap binary
    sqlmap_path = shutil.which("sqlmap")
    if not sqlmap_path:
        if os.path.exists("/usr/local/bin/sqlmap"):
            sqlmap_path = "/usr/local/bin/sqlmap"
        else:
            return {"status": "error", "message": "sqlmap binary not found."}

    # Handle multiple targets or single
    if isinstance(targets, str):
        if ',' in targets:
            targets_list = [t.strip() for t in targets.split(',') if t.strip()]
        else:
            targets_list = [targets]
    else:
        targets_list = targets

    # Create temp file for targets if multiple
    targets_file = None
    if len(targets_list) > 1:
        with tempfile.NamedTemporaryFile(mode='w', suffix=".txt", delete=False) as f:
            for t in targets_list:
                if "://" not in t: t = f"http://{t}"
                f.write(f"{t}\n")
            targets_file = f.name

    # Construct command
    # --batch : Never ask for user input
    # --random-agent : Use random HTTP User-Agent
    # --forms : Parse and test forms
    # --crawl=1 : Crawl the website
    command = [sqlmap_path, "--batch", "--random-agent", "--forms", "--crawl=1"]

    if targets_file:
        command.extend(["-m", targets_file])
    else:
        target = targets_list[0]
        if "://" not in target: target = f"http://{target}"
        command.extend(["-u", target])

    # Extra arguments
    extra_args = args.get('arguments')
    if extra_args:
        command.extend(shlex.split(extra_args))

    # Real-time parsing logic
    all_findings = []
    current_url = "N/A"
    
    target_pattern = re.compile(r"starting scanner for URL ['\"](.+?)['\"]")
    vuln_pattern = re.compile(r"(is vulnerable|appears to be injectable)")

    try:
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )

        for line in process.stdout:
            line = line.strip()
            if not line: continue
            
            # Print to stderr for Windmill logs
            print(f"SQLMAP: {line}", file=sys.stderr, flush=True)
            
            # Detect target change
            m_target = target_pattern.search(line)
            if m_target:
                current_url = m_target.group(1)
            
            # Detect vulnerability
            if vuln_pattern.search(line):
                all_findings.append({
                    "target": current_url,
                    "finding": line
                })

        process.wait()
        
        if targets_file and os.path.exists(targets_file):
            os.remove(targets_file)

        status = "success" if process.returncode == 0 else "error"
        
        return {
            "status": status,
            "message": f"Sqlmap scan complete. Found {len(all_findings)} vulnerabilities.",
            "data": {
                "targets": targets_list,
                "vulnerabilities": all_findings
            }
        }

    except Exception as e:
        if targets_file and os.path.exists(targets_file):
            os.remove(targets_file)
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    params = {}
    if len(sys.argv) > 1:
        try:
            params = json.loads(sys.argv[1])
        except:
            params = {}
    print(json.dumps(main(**params), indent=2))
