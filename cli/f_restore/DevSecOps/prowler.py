import subprocess
import os
import sys
import json
import glob

def run_prowler(provider: str, arguments: str):
    image = "prowlercloud/prowler:latest"
    job_id = os.environ.get("WM_JOB_ID", "local_test_prowler")

    # Pull image
    print(f"DEBUG: Pulling image {image}...", file=sys.stderr, flush=True)
    subprocess.run(["docker", "pull", image], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    # Prepare environment variables for credentials
    # Pass all AWS_, AZURE_, GOOGLE_ env vars to container
    env_vars = []
    for k, v in os.environ.items():
        if k.startswith("AWS_") or k.startswith("AZURE_") or k.startswith("GOOGLE_"):
            env_vars.extend(["-e", f"{k}={v}"])

    # Output directory in container
    output_dir = "/tmp/output"
    
    cmd = [
        "docker", "run",
        "--name", job_id,
        *env_vars,
        image,
        provider,
        "-M", "json",
        "-o", output_dir
    ]
    
    if arguments:
        cmd.extend(arguments.split())

    print(f"DEBUG: Running command: {' '.join(cmd)}", file=sys.stderr, flush=True)
    
    try:
        process = subprocess.Popen(
            cmd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, 
            text=True, 
            bufsize=1
        )
        
        # Stream stdout
        while True:
            line = process.stdout.readline()
            if not line and process.poll() is not None:
                break
            if line:
                print(f"PROWLER: {line.strip()}", file=sys.stderr, flush=True)
                
        process.wait()

        # Read output
        # Prowler creates a file with a timestamp name, e.g. prowler-output-ACCOUNT-TIMESTAMP.json
        # We need to list files in the container dir or copy the whole dir.
        
        local_output_dir = f"/tmp/{job_id}_output"
        os.makedirs(local_output_dir, exist_ok=True)
        
        cp_cmd = ["docker", "cp", f"{job_id}:{output_dir}/.", local_output_dir]
        cp_result = subprocess.run(cp_cmd, capture_output=True, text=True)
        
        result_data = []
        
        if cp_result.returncode == 0:
            # Find json file
            files = glob.glob(f"{local_output_dir}/*.json")
            if files:
                # Prowler JSON output is a list of objects or lines of objects depending on version.
                # v3 usually uses a list of objects in standard json mode.
                try:
                    with open(files[0], "r") as f:
                        content = f.read()
                        if content.strip():
                            result_data = json.loads(content)
                except Exception as e:
                     print(f"DEBUG: Failed to parse JSON: {e}", file=sys.stderr, flush=True)
            
            # Clean up local
            import shutil
            shutil.rmtree(local_output_dir)
        else:
             print(f"DEBUG: Could not copy files: {cp_result.stderr}", file=sys.stderr, flush=True)

        return result_data

    except Exception as e:
        print(f"Error running prowler: {e}", file=sys.stderr, flush=True)
        return {"error": str(e)}
    finally:
        # Cleanup container
        subprocess.run(["docker", "rm", "-f", job_id], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def main(provider: str = "aws", arguments: str = ""):
    print(f"DEBUG: Starting Prowler scan for {provider}", file=sys.stderr, flush=True)
    result = run_prowler(provider, arguments)
    return result

if __name__ == "__main__":
    # Simple CLI arg parsing for local test
    provider = sys.argv[1] if len(sys.argv) > 1 else "aws"
    main(provider)
