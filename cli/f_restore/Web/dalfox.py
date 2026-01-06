import subprocess
import os
import sys
import json

def run_dalfox(target: str):
    image = "hahwul/dalfox:latest"
    job_id = os.environ.get("WM_JOB_ID", "local_test_dalfox")

    print(f"DEBUG: Pulling image {image}...", file=sys.stderr, flush=True)
    subprocess.run(["docker", "pull", image], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    # Dalfox url target
    # -F for json output is not default? 
    # Dalfox --format json -o /tmp/dalfox.json
    
    cmd = [
        "docker", "run",
        "--name", job_id,
        image,
        "url", target,
        "--format", "json",
        "-o", "/tmp/dalfox.json"
    ]
    
    print(f"DEBUG: Running dalfox...", file=sys.stderr, flush=True)
    
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
                print(f"DALFOX: {line.strip()}", file=sys.stderr, flush=True)
                
        process.wait()

        # Copy output
        local_output = f"/tmp/{job_id}_dalfox.json"
        
        cp_cmd = ["docker", "cp", f"{job_id}:/tmp/dalfox.json", local_output]
        cp_result = subprocess.run(cp_cmd, capture_output=True, text=True)
        
        result_data = []
        
        if cp_result.returncode == 0:
            try:
                with open(local_output, "r") as f:
                    # Dalfox NDJSON or array? 
                    # Usually NDJSON if scanning multiple. But json format might be array.
                    # Let's try load array, if fail try ndjson.
                    content = f.read()
                    if content.strip():
                        try:
                            result_data = json.loads(content)
                        except:
                            # Try NDJSON
                            result_data = [json.loads(line) for line in content.splitlines() if line.strip()]
                os.remove(local_output)
            except Exception as e:
                pass
        else:
             print(f"DEBUG: Could not copy output: {cp_result.stderr}", file=sys.stderr, flush=True)

        return result_data

    except Exception as e:
        print(f"Error running dalfox: {e}", file=sys.stderr, flush=True)
        return {"error": str(e)}
    finally:
        subprocess.run(["docker", "rm", "-f", job_id], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def main(target: str = "https://scanme.nmap.org"):
    print(f"DEBUG: Starting Dalfox on {target}", file=sys.stderr, flush=True)
    result = run_dalfox(target)
    return result

if __name__ == "__main__":
    if len(sys.argv) > 1:
        main(sys.argv[1])
    else:
        main()
