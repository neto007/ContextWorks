import subprocess
import os
import sys
import json
import shutil

def run_semgrep(repo_url: str):
    image = "returntocorp/semgrep"
    job_id = os.environ.get("WM_JOB_ID", "local_test_semgrep")

    print(f"DEBUG: Pulling image {image}...", file=sys.stderr, flush=True)
    subprocess.run(["docker", "pull", image], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    # Semgrep container might not have git.
    # We can try to use a script that installs git if missing, or use a volume mount pattern where we clone first?
    # Windmill usually runs as a user. 
    # Let's try to run `git clone` inside the container. 
    # Notes: Semgrep image is based on Alpine usually? 
    # Let's assume we can apk add git.
    
    # Valid output is JSON.
    
    install_and_run = (
        "apk add --no-cache git >/dev/null 2>&1 || (apt-get update && apt-get install -y git >/dev/null 2>&1) && "
        f"git clone {repo_url} /src --depth 1 >/dev/null && "
        "semgrep scan --config=auto --json --output=/tmp/semgrep.json /src"
    )

    cmd = [
        "docker", "run",
        "--name", job_id,
        "--entrypoint", "", # Override default entrypoint
        image,
        "sh", "-c",
        install_and_run
    ]
    
    print(f"DEBUG: Running semgrep...", file=sys.stderr, flush=True)
    
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
                # Semgrep text output usually goes to stderr if json is selected? 
                # Or if we pipe it. 
                # Since we used --output, stdout might be clean or empty.
                print(f"SEMGREP: {line.strip()}", file=sys.stderr, flush=True)
                
        process.wait()

        # Copy output
        local_output = f"/tmp/{job_id}_semgrep.json"
        
        cp_cmd = ["docker", "cp", f"{job_id}:/tmp/semgrep.json", local_output]
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
             print(f"DEBUG: Could not copy output: {cp_result.stderr}", file=sys.stderr, flush=True)

        return result_data

    except Exception as e:
        print(f"Error running semgrep: {e}", file=sys.stderr, flush=True)
        return {"error": str(e)}
    finally:
        subprocess.run(["docker", "rm", "-f", job_id], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def main(repo_url: str = "https://github.com/juice-shop/juice-shop.git"):
    print(f"DEBUG: Starting Semgrep on {repo_url}", file=sys.stderr, flush=True)
    result = run_semgrep(repo_url)
    return result

if __name__ == "__main__":
    if len(sys.argv) > 1:
        main(sys.argv[1])
    else:
        main()
