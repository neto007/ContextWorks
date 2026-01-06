import subprocess
import os
import sys
import json
import time
import shutil

def run_command(cmd, shell=False, env=None):
    """Auxiliary function to run commands and print debug info."""
    print(f"DEBUG: Running: {' '.join(cmd) if isinstance(cmd, list) else cmd}", file=sys.stderr, flush=True)
    try:
        result = subprocess.run(
            cmd,
            shell=shell,
            check=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env
        )
        return result.stdout.strip()
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Command failed with rc {e.returncode}", file=sys.stderr, flush=True)
        print(f"STDERR: {e.stderr}", file=sys.stderr, flush=True)
        raise e

def setup_vulnerability_dbs(volume_name: str):
    """Fetches/Updates vulnerability databases into the docker volume."""
    print("STATUS: Setting up vulnerability databases... This may take a while.", file=sys.stderr, flush=True)
    
    # Check if volume exists, create if not
    subprocess.run(["docker", "volume", "create", volume_name], check=False)

    # 1. Fetch NVD (National Vulnerability Database)
    # Fetching recent years to save time, or full? Let's fetch 2002-current year for full coverage or last 5 years?
    # Usually "fetch nvd" fetches all.
    # vulsio/go-cve-dictionary fetch nvd
    print("STATUS: Fetching NVD data...", file=sys.stderr, flush=True)
    try:
        run_command([
            "docker", "run", "--rm",
            "-v", f"{volume_name}:/vuls",
            "-w", "/vuls",
            "--log-driver", "none", # Reduce noise
            "vulsio/go-cve-dictionary",
            "fetch", "nvd"
        ])
    except Exception as e:
        print(f"WARNING: NVD fetch failed or interrupted: {e}", file=sys.stderr, flush=True)

    # 2. Fetch OVAL (OS Vulnerability Assessment Language)
    # We will fetch Ubuntu and Debian for generic coverage. Ideally this should be configurable.
    # For now, let's fetch Ubuntu and Debian.
    targets = ["ubuntu", "debian", "alpine"]
    print(f"STATUS: Fetching OVAL data for {targets}...", file=sys.stderr, flush=True)
    for t in targets:
        try:
            run_command([
                "docker", "run", "--rm",
                "-v", f"{volume_name}:/vuls",
                "-w", "/vuls",
                "--log-driver", "none",
                "vulsio/goval-dictionary",
                "fetch", t
            ])
        except Exception as e:
            print(f"WARNING: OVAL fetch for {t} failed: {e}", file=sys.stderr, flush=True)

def generate_config(target, user, port, key_path, current_dir):
    """Generates config.toml content."""
    # Vuls config format
    config = f"""
[servers]

[servers.{target.replace('.', '_')}]
host = "{target}"
port = "{port}"
user = "{user}"
keyPath = "/vuls/id_rsa"
scanMode = ["fast"] # fast or fast-root or deep. fast is usually enough for connection test.
"""
    config_path = os.path.join(current_dir, "config.toml")
    with open(config_path, "w") as f:
        f.write(config)
    return config_path

def run_vuls(
    target: str,
    ssh_user: str,
    ssh_key: str,
    port: str = "22",
    setup_dbs: bool = False
):
    volume_name = "vuls-data"
    job_id = os.environ.get("WM_JOB_ID", "local_test_vuls")
    current_dir = os.getcwd() # Windmill executes in a temp dir
    
    # Ensure volume exists
    subprocess.run(["docker", "volume", "create", volume_name], stdout=subprocess.DEVNULL)

    if setup_dbs:
        setup_vulnerability_dbs(volume_name)

    # 1. Prepare SSH Key
    key_file_path = os.path.join(current_dir, "id_rsa")
    with open(key_file_path, "w") as f:
        f.write(ssh_key + "\n") # Ensure newline at end
    os.chmod(key_file_path, 0o600)

    # 2. Generate Config
    config_path = generate_config(target, ssh_user, port, "/vuls/id_rsa", current_dir)
    
    # 3. Running Scan
    print(f"STATUS: Starting Vuls Scan against {target}...", file=sys.stderr, flush=True)
    
    # Mounts:
    # - vuls-data:/vuls (The DBs)
    # - config.toml:/vuls/config.toml (The Config)
    # - id_rsa:/vuls/id_rsa (The Key)
    # Workdir: /vuls
    
    server_name = target.replace('.', '_')
    
    scan_cmd = [
        "docker", "run", "--rm",
        "--name", f"{job_id}_scan",
        "-v", f"{volume_name}:/vuls",
        "-v", f"{config_path}:/vuls/config.toml",
        "-v", f"{key_file_path}:/vuls/id_rsa",
        "vulsio/vuls",
        "scan",
        "-config", "/vuls/config.toml"
    ]
    
    # Attempt configtest first? No, vuls scan checks config.
    
    scan_output = ""
    try:
        # Use simple run first to capture output
        # If connection fails, it exits non-zero
        scan_proc = subprocess.run(
            scan_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT, # Merge stderr to stdout for parsing
            text=True
        )
        scan_output = scan_proc.stdout
        print(f"SCAN LOGS:\n{scan_output}", file=sys.stderr, flush=True)
        
        if scan_proc.returncode != 0:
            return {
                "error": "Vuls Scan Failed",
                "details": scan_output,
                "hint": "Check SSH connection, user, key permissions, or firewall."
            }
            
    except Exception as e:
        return {"error": f"Execution error: {str(e)}"}

    # 4. Reporting
    # If scan succeeded, we generate a report.
    # Vuls report -format-json
    print("STATUS: Generating Report...", file=sys.stderr, flush=True)
    report_cmd = [
        "docker", "run", "--rm",
        "--name", f"{job_id}_report",
        "-v", f"{volume_name}:/vuls",
        "-v", f"{config_path}:/vuls/config.toml",
        "vulsio/vuls",
        "report",
        "-format-json"
    ]
    
    try:
        report_proc = subprocess.run(
            report_cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        if report_proc.returncode != 0:
             print(f"REPORT DEBUG: {report_proc.stderr}", file=sys.stderr, flush=True)
             return {"error": "Report Generation Failed", "details": report_proc.stderr}

        # Parse JSON output
        # Vuls prints JSON to stdout
        try:
             json_report = json.loads(report_proc.stdout)
             # Extract relevant info
             # The result is usually a map: { "timestamp": ... , "reportedAt": ... , "scannedCves": ... }
             # Or it might be a list of scan results if multiple servers.
             # We configured 1 server.
             
             # If map, it might carry `[servers.{name}]` in key or something?
             # Let's return raw structure first or clean it up.
             return json_report
             
        except json.JSONDecodeError:
            return {"error": "Invalid JSON from report", "raw_output": report_proc.stdout}

    except Exception as e:
        return {"error": f"Report execution error: {str(e)}"}
    finally:
        # Cleanup temp files
        if os.path.exists(key_file_path):
            os.remove(key_file_path)
        if os.path.exists(config_path):
            os.remove(config_path)

def main(
    target: str = "192.168.1.10",
    ssh_user: str = "root",
    ssh_key: str = "-----BEGIN RSA PRIVATE KEY-----...",
    port: str = "22",
    setup_dbs: bool = False
):
    if ssh_key.startswith("-----BEGIN"):
        pass # It's likely a key content
    else:
        # If user passed a file path? In Windmill usually it's passed as content (Secret).
        pass

    return run_vuls(target, ssh_user, ssh_key, port, setup_dbs)

if __name__ == "__main__":
    # Mock execution for local testing not fully supported without real args
    # Windmill calls main()
    pass
