import subprocess
import os
import sys
import json
import glob
import shutil

def run_docker_bench():
    image = "docker/docker-bench-security:latest"
    job_id = os.environ.get("WM_JOB_ID", "local_test_docker_bench")

    # Pull image
    print(f"DEBUG: Pulling image {image}...", file=sys.stderr, flush=True)
    subprocess.run(["docker", "pull", image], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    # Mounts required for docker-bench-security
    # It needs access to host docker socket, /etc, /usr/lib/systemd, etc.
    # We also mount a volume for LOGS to extract JSON.
    
    # Create a volume for logs? Or bind mount?
    # Windmill runner has access to its own filesystem. 
    # Can we bind mount /tmp/output to container?
    # Windmill runner runs in docker. `docker run -v` uses HOST paths.
    # We don't know the HOST path of /tmp.
    # We must use a named volume or `docker cp`.
    # `docker cp` is safer.
    
    # Where does it write logs? 
    # By default, it writes to ./log/ (relative to WORKDIR).
    # WORKDIR in image is `/usr/local/bin` (usually).
    # So `/usr/local/bin/log`.
    
    log_dir_in_container = "/usr/local/bin/log"

    cmd = [
        "docker", "run",
        "--name", job_id,
        "--net", "host",
        "--pid", "host",
        "--userns", "host",
        "--cap-add", "AUDIT_CONTROL",
        "-e", "DOCKER_CONTENT_TRUST=$DOCKER_CONTENT_TRUST", # Pass env if needed
        "-v", "/etc:/etc:ro",
        "-v", "/usr/bin/docker-containerd:/usr/bin/docker-containerd:ro",
        "-v", "/usr/bin/docker-runc:/usr/bin/docker-runc:ro",
        "-v", "/usr/lib/systemd:/usr/lib/systemd:ro",
        "-v", "/var/lib:/var/lib:ro",
        "-v", "/var/run/docker.sock:/var/run/docker.sock:ro",
        "--label", "docker_bench_security",
        image
    ]
    
    print(f"DEBUG: Running command: docker run ... docker-bench-security", file=sys.stderr, flush=True)
    
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
                print(f"DOCKER-BENCH: {line.strip()}", file=sys.stderr, flush=True)
                
        process.wait()

        # Copy logs
        local_output_dir = f"/tmp/{job_id}_docker_bench"
        os.makedirs(local_output_dir, exist_ok=True)
        
        cp_cmd = ["docker", "cp", f"{job_id}:{log_dir_in_container}/.", local_output_dir]
        cp_result = subprocess.run(cp_cmd, capture_output=True, text=True)
        
        result_data = {}
        
        if cp_result.returncode == 0:
            # Find .json file
            files = glob.glob(f"{local_output_dir}/*.json")
            if files:
                try:
                    with open(files[0], "r") as f:
                        result_data = json.load(f)
                except Exception as e:
                    result_data = {"error": f"Failed to parse JSON: {e}"}
            else:
                 result_data = {"warning": "No JSON output found. Check logs."}
            
            shutil.rmtree(local_output_dir)
        else:
             print(f"DEBUG: Copy failed: {cp_result.stderr}", file=sys.stderr, flush=True)
             result_data = {"warning": "Could not copy output file. See logs."}

        return result_data

    except Exception as e:
        print(f"Error running docker-bench: {e}", file=sys.stderr, flush=True)
        return {"error": str(e)}
    finally:
        subprocess.run(["docker", "rm", "-f", job_id], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def main():
    print(f"DEBUG: Starting Docker-Bench-Security", file=sys.stderr, flush=True)
    result = run_docker_bench()
    return result

if __name__ == "__main__":
    main()
