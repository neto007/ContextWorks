import subprocess
import os
import sys
import json
import re

def run_metasploit(target: str, module: str, options: str):
    image = "metasploitframework/metasploit-framework:latest"
    job_id = os.environ.get("WM_JOB_ID", "local_test_msf")

    print(f"DEBUG: Pulling image {image}...", file=sys.stderr, flush=True)
    subprocess.run(["docker", "pull", image], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    # Construct Resource Script (.rc)
    # 1. use <module>
    # 2. set RHOSTS <target>
    # 3. set <OPTION> <VALUE>
    # 4. run
    # 5. exit
    
    rc_content = [
        f"use {module}",
        f"set RHOSTS {target}",
        "set VERBOSE true" # Ensure we get output
    ]
    
    if options:
        for line in options.split("\n"):
            line = line.strip()
            if line and "=" in line:
                key, val = line.split("=", 1)
                rc_content.append(f"set {key.strip()} {val.strip()}")
            elif line:
                # Direct command or set without = ? Metasploit 'set' uses space.
                # Assuming user input "KEY=VAL" or "KEY VAL" logic.
                parts = line.split(None, 1)
                if len(parts) == 2:
                    rc_content.append(f"set {parts[0]} {parts[1]}")

    rc_content.append("run")
    rc_content.append("exit -y")
    
    rc_str = "\n".join(rc_content)
    
    print(f"DEBUG: Generated Resource Script:\n{rc_str}", file=sys.stderr, flush=True)
    
    # We pass RC via stdin or file. 
    # File is safer.
    
    install_and_run = (
        f"echo \"{rc_str}\" > /tmp/scan.rc && "
        "msfconsole -q -r /tmp/scan.rc"
    )

    cmd = [
        "docker", "run",
        "--name", job_id,
        "--entrypoint", "",
        image,
        "sh", "-c",
        install_and_run
    ]
    
    print(f"DEBUG: Running Metasploit...", file=sys.stderr, flush=True)
    
    # Output structure
    structured_output = {
        "module": module,
        "target": target,
        "findings": [],
        "logs": []
    }
    
    # Regex for standard MSF output
    # [+] Success/Good
    # [*] Status/Info
    # [-] Error/Fail
    # [!] Warning
    line_pattern = re.compile(r"^\s*\[([+*\-!])\]\s*(.*)")
    
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
                raw_line = line.strip()
                # Print to logs for streaming user feedback
                print(f"MSF: {raw_line}", file=sys.stderr, flush=True)
                
                # Parse
                match = line_pattern.match(raw_line)
                if match:
                    symbol = match.group(1)
                    message = match.group(2)
                    
                    entry = {"type": symbol, "message": message}
                    
                    if symbol == "+":
                        entry["severity"] = "high"
                        structured_output["findings"].append(entry)
                    elif symbol == "!":
                         entry["severity"] = "medium"
                    else:
                         entry["severity"] = "info"
                    
                    structured_output["logs"].append(entry)
                else:
                    # Non-standard line
                    if raw_line:
                        structured_output["logs"].append({"type": "raw", "message": raw_line})
                
        process.wait()

        return structured_output

    except Exception as e:
        print(f"Error running msf: {e}", file=sys.stderr, flush=True)
        return {"error": str(e)}
    finally:
        subprocess.run(["docker", "rm", "-f", job_id], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def main(target: str = "scanme.nmap.org", module: str = "auxiliary/scanner/portscan/tcp", options: str = "PORTS=80,443,8080"):
    print(f"DEBUG: Starting Metasploit {module} on {target}", file=sys.stderr, flush=True)
    result = run_metasploit(target, module, options)
    print(json.dumps(result, indent=2), flush=True)
    return result

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Windmill might pass args. Simple handling:
        # If args passed, assume main called by windmill wrapper with kwargs usually.
        # But for CLI testing:
        main()
    else:
        main()
