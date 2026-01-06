import subprocess
import os
import sys
import json
import glob
import shutil

def run_scout_suite(provider: str):
    image = "python:3.11-slim"
    job_id = os.environ.get("WM_JOB_ID", "local_test_scout")

    # Pull image
    print(f"DEBUG: Pulling image {image}...", file=sys.stderr, flush=True)
    subprocess.run(["docker", "pull", image], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    # Prepare environment variables for credentials
    env_vars = []
    for k, v in os.environ.items():
        if k.startswith("AWS_") or k.startswith("AZURE_") or k.startswith("GOOGLE_"):
            env_vars.extend(["-e", f"{k}={v}"])

    # Output directory in container
    container_output_dir = "/tmp/scout-report"
    
    # Command to install and run
    # Scout Suite outputs to a folder. We need to find the .js file in it.
    install_and_run = (
        "pip install scoutsuite >/dev/null && "
        f"scout {provider} --no-browser --report-dir {container_output_dir}"
    )

    cmd = [
        "docker", "run",
        "--name", job_id,
        *env_vars,
        image,
        "sh", "-c",
        install_and_run
    ]
    
    print(f"DEBUG: Running command: docker run ... scout {provider}", file=sys.stderr, flush=True)
    
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
                print(f"SCOUT: {line.strip()}", file=sys.stderr, flush=True)
                
        process.wait()

        if process.returncode != 0:
             _, stderr_output = process.communicate()
             print(f"DEBUG: Process stderr: {stderr_output}", file=sys.stderr, flush=True)
             return {"error": "Scout Suite failed", "details": stderr_output}

        # Copy output
        local_output_dir = f"/tmp/{job_id}_scout"
        os.makedirs(local_output_dir, exist_ok=True)
        
        cp_cmd = ["docker", "cp", f"{job_id}:{container_output_dir}/.", local_output_dir]
        cp_result = subprocess.run(cp_cmd, capture_output=True, text=True)
        
        result_data = {}
        
        if cp_result.returncode == 0:
            # Find the result .js file (usually scoutsuite-results/scoutsuite_results_....js)
            # The structure is usually: report-dir/scoutsuite-results/scoutsuite_results_...js
            js_files = glob.glob(f"{local_output_dir}/**/scoutsuite_results_*.js", recursive=True)
            
            if js_files:
                target_file = js_files[0]
                try:
                    with open(target_file, "r") as f:
                        lines = f.readlines()
                        # Content is like: scoutsuite_results = { ... }
                        # We skip the first line (assignment) or find the first '{'
                        full_content = "".join(lines)
                        json_start = full_content.find("{")
                        if json_start != -1:
                            json_content = full_content[json_start:]
                            result_data = json.loads(json_content)
                        else:
                             return {"error": "Could not find JSON object in result file"}
                except Exception as e:
                     return {"error": f"Failed to parse JS/JSON: {e}"}
            else:
                 return {"error": "No result .js file found in output"}
            
            # Clean up local
            shutil.rmtree(local_output_dir)
        else:
             return {"error": "Could not copy files", "details": cp_result.stderr}

        return result_data

    except Exception as e:
        print(f"Error running scout suite: {e}", file=sys.stderr, flush=True)
        return {"error": str(e)}
    finally:
        # Cleanup container
        subprocess.run(["docker", "rm", "-f", job_id], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def main(provider: str = "aws"):
    print(f"DEBUG: Starting Scout Suite scan for {provider}", file=sys.stderr, flush=True)
    result = run_scout_suite(provider)
    return result

if __name__ == "__main__":
    provider = sys.argv[1] if len(sys.argv) > 1 else "aws"
    main(provider)
