import subprocess
import os
import sys
import json

def run_vet(repo_url: str):
    image = "ghcr.io/safedep/vet:latest"
    job_id = os.environ.get("WM_JOB_ID", "local_test_vet")

    print(f"DEBUG: Pulling image {image}...", file=sys.stderr, flush=True)
    subprocess.run(["docker", "pull", image], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    # VET works on directories or lockfiles.
    # We clone the repo first.
    # VET image likely has git? If not, we use the shell standard install pattern.
    # ghcr.io/safedep/vet is usually minimal.
    
    install_and_run = (
        "(command -v git >/dev/null || (apt-get update && apt-get install -y git) || (apk add --no-cache git)) && "
        "git clone --depth 1 " + repo_url + " /src >/dev/null && "
        # Run vet scan
        "vet scan -D /src --report-json /tmp/vet-report.json --no-banner"
    )

    cmd = [
        "docker", "run",
        "--name", job_id,
        "--entrypoint", "",
        image,
        "sh", "-c",
        install_and_run
    ]
    
    print(f"DEBUG: Running SafeDep VET...", file=sys.stderr, flush=True)
    
    # We want to stream logs. VET outputs logs to stderr usually.
    
    try:
        process = subprocess.Popen(
            cmd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.STDOUT, 
            text=True, 
            bufsize=1
        )
        
        while True:
            line = process.stdout.readline()
            if not line and process.poll() is not None:
                break
            if line:
                print(f"VET: {line.strip()}", file=sys.stderr, flush=True)
                
        process.wait()

        # Copy output
        local_output = f"/tmp/{job_id}_vet.json"
        
        cp_cmd = ["docker", "cp", f"{job_id}:/tmp/vet-report.json", local_output]
        cp_result = subprocess.run(cp_cmd, capture_output=True, text=True)
        
        result_data = {}
        
        if cp_result.returncode == 0:
            try:
                with open(local_output, "r") as f:
                    result_data = json.load(f)
                os.remove(local_output)
            except Exception as e:
                pass
        else:
             print(f"DEBUG: Could not copy output (no issues found or error): {cp_result.stderr}", file=sys.stderr, flush=True)

        return result_data

    except Exception as e:
        print(f"Error running vet: {e}", file=sys.stderr, flush=True)
        return {"error": str(e)}
    finally:
        subprocess.run(["docker", "rm", "-f", job_id], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def main(repo_url: str = "https://github.com/juice-shop/juice-shop.git"):
    print(f"DEBUG: Starting VET on {repo_url}", file=sys.stderr, flush=True)
    result = run_vet(repo_url)
    return result

if __name__ == "__main__":
    if len(sys.argv) > 1:
        main(sys.argv[1])
    else:
        main()
