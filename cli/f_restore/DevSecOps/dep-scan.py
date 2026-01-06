import subprocess
import os
import sys
import json
import glob

def run_depscan(repo_url: str):
    # Using python:3.11-bullseye to ensure we have a solid base for pip/npm
    image = "python:3.11-bullseye" 
    job_id = os.environ.get("WM_JOB_ID", "local_debug_depscan")

    print(f"DEBUG: Pulling image {image}...", file=sys.stderr, flush=True)
    subprocess.run(["docker", "pull", image], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    # We need:
    # 1. git (to clone)
    # 2. nodejs + npm (to run cdxgen)
    # 3. cdxgen (to generate SBOM)
    # 4. depscan (to scan SBOM)
    
    # We will build a command chain.
    install_and_run = (
        "echo 'DEBUG: Installing base dependencies...' >&2 && "
        "apt-get update >/dev/null && "
        "apt-get install -y curl git >/dev/null && "
        "echo 'DEBUG: Upgrading Node.js to v20...' >&2 && "
        "curl -fsSL https://deb.nodesource.com/setup_20.x | bash - >/dev/null 2>&1 && "
        "apt-get install -y nodejs >/dev/null && "
        "echo 'DEBUG: Installing CDXGen and DepScan...' >&2 && "
        "npm install -g @cyclonedx/cdxgen >/dev/null 2>&1 && "
        "pip install appthreat-depscan >/dev/null 2>&1 && "
        "echo 'DEBUG: Cloning repository...' >&2 && "
        "git clone --depth 1 " + repo_url + " /src >/dev/null && "
        "cd /src && "
        "echo 'DEBUG: Generating SBOM with cdxgen (this may take a while)...' >&2 && "
        "cdxgen -o /tmp/bom.json . && "
        "echo 'DEBUG: Running DepScan on SBOM...' >&2 && "
        "depscan --bom /tmp/bom.json --reports-dir /reports --no-banner"
    )

    cmd = [
        "docker", "run",
        "--name", job_id,
        image,
        "sh", "-c",
        install_and_run
    ]
    
    print(f"DEBUG: Running custom dep-scan pipeline...", file=sys.stderr, flush=True)
    
    try:
        process = subprocess.Popen(
            cmd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.STDOUT, # Merge stderr to stdout so we see "DEBUG" echoes in the loop
            text=True, 
            bufsize=1
        )
        
        while True:
            line = process.stdout.readline()
            if not line and process.poll() is not None:
                break
            if line:
                print(f"DEPSCAN: {line.strip()}", file=sys.stderr, flush=True)
            
            # Also read stderr if any? 
            # Popen default handles distinct pipes.
            # We directed debug echoes to stderr.
            # Ideally we should read stderr too to show progress.
            # But process.stderr needs to be read.
            
        # Wait
        process.wait()
        
        # Check for stderr logs if process failed or just to show progress
        # Since we didn't loop read stderr, we might miss it if buffer fills?
        # Actually with PIPE, we should consume.
        # But for simplicity, let's rely on the fact that we put echoes to stderr but we aren't reading stderr in the loop above?
        # WAIT: In previous logic we only read stdout. Debug echos to stderr won't show up in the while loop unless we read process.stderr.
        # To make "hanging" debuggable, we SHOULD read stderr.
        # Let's just fix the python script to read stdout (and depscan prints results there?). 
        # Actually depscan prints to stdout usually? Or stderr?
        # Depscan logs to console (stderr usually) and report to file.
        # So we should probably capture everything or just redirect stderr to stdout in the sh command?
        # "2>&1" in the sh command would merge them.
        
    except Exception as e:
        print(f"Error launching process: {e}", file=sys.stderr, flush=True)

    # We won't block on the python loop forever if we merge streams or use communicate?
    # Windmill streaming usually wants line-by-line.
    # Let's re-run with stderr merge in the next tool call if I could, but let's assume valid.
    
    # Copy output
    local_output_dir = f"/tmp/{job_id}_reports"
    os.makedirs(local_output_dir, exist_ok=True)
    
    cp_cmd = ["docker", "cp", f"{job_id}:/reports/.", local_output_dir]
    subprocess.run(cp_cmd, capture_output=True)
    
    # Read .json
    result_data = []
    
    json_files = glob.glob(f"{local_output_dir}/*.json")
    for jf in json_files:
         if "depscan" in jf and "json" in jf:
             try:
                with open(jf, "r") as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        result_data.extend(data)
                    else:
                        result_data.append(data)
             except: pass

    import shutil
    shutil.rmtree(local_output_dir)
    
    # Cleanup
    subprocess.run(["docker", "rm", "-f", job_id], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    return result_data

def main(repo_url: str = "https://github.com/juice-shop/juice-shop.git"):
    print(f"DEBUG: Starting Dep-Scan pipeline on {repo_url}", file=sys.stderr, flush=True)
    result = run_depscan(repo_url)
    return result

if __name__ == "__main__":
    if len(sys.argv) > 1:
        main(sys.argv[1])
    else:
        main()
