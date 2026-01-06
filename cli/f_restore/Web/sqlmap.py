import subprocess
import os
import sys
import json
import re
import shutil

def run_sqlmap(targets_input):
    image = "sqlmapproject/sqlmap:latest" # Official image
    job_id = os.environ.get("WM_JOB_ID", "local_test_sqlmap")

    # Handle input
    targets = []
    if isinstance(targets_input, list):
        targets = targets_input
    elif isinstance(targets_input, str):
        targets = [t.strip() for t in targets_input.replace(',', '\n').split('\n') if t.strip()]
    
    if not targets:
        return {"error": "No targets provided"}

    sanitized = []
    for t in targets:
        if "://" not in t: t = f"http://{t}"
        sanitized.append(t)
    
    targets_str = "\\n".join(sanitized)

    print(f"DEBUG: Pulling image {image}...", file=sys.stderr, flush=True)
    subprocess.run(["docker", "pull", image], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    # Official image usually has entrypoint "sqlmap"
    # We want to create a targets file first.
    # We'll use a shell wrap.
    # Alpine based image inside usually? 
    
    install_and_run = (
        f"echo -e '{targets_str}' > /tmp/targets.txt && "
        "sqlmap -m /tmp/targets.txt --batch --disable-coloring --forms --crawl=1 --random-agent"
    )

    cmd = [
        "docker", "run",
        "--name", job_id,
        "--entrypoint", "",
        image,
        "sh", "-c",
        install_and_run
    ]
    
    print(f"DEBUG: Running sqlmap...", file=sys.stderr, flush=True)
    
    all_findings = []
    current_target = "Unknown"
    
    # Regexes
    target_pattern = re.compile(r"starting scanner for URL ['\"](.+?)['\"]")
    vuln_pattern = re.compile(r"(is vulnerable|appears to be injectable)")
    
    try:
        process = subprocess.Popen(
            cmd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, 
            text=True, 
            bufsize=1
        )
        
        while True:
            line = process.stdout.readline()
            if not line and process.poll() is not None:
                break
            if line:
                line = line.strip()
                print(f"SQLMAP: {line}", file=sys.stderr, flush=True)
                
                m_target = target_pattern.search(line)
                if m_target:
                    current_target = m_target.group(1)
                
                if vuln_pattern.search(line):
                    all_findings.append({
                        "target": current_target,
                        "message": line
                    })
                
        process.wait()
        
        # We could try to copy /root/.local/share/sqlmap/output/ if we wanted CSVs/logs.
        # But text parsing is often "good enough" for real-time alerts.
        
        return {
            "scanned_targets": sanitized,
            "vulnerable_count": len(all_findings),
            "findings": all_findings
        }

    except Exception as e:
        print(f"Error running sqlmap: {e}", file=sys.stderr, flush=True)
        return {"error": str(e)}
    finally:
        subprocess.run(["docker", "rm", "-f", job_id], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def main(targets_arg):
    if not targets_arg:
        # Default test target
        targets_arg = "http://testphp.vulnweb.com/artists.php?artist=1"
        
    print(f"DEBUG: Scanning targets: {targets_arg}", file=sys.stderr, flush=True)
    result = run_sqlmap(targets_arg)
    return result

if __name__ == "__main__":
    arg = sys.argv[1] if len(sys.argv) > 1 else ""
    main(arg)
