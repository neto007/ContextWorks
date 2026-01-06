import subprocess
import os
import sys
import json

def run_katana(target: str):
    image = "projectdiscovery/katana:latest"
    job_id = os.environ.get("WM_JOB_ID", "local_test_katana")

    print(f"DEBUG: Pulling image {image}...", file=sys.stderr, flush=True)
    subprocess.run(["docker", "pull", image], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    # -j for JSON output
    # -o for output file
    cmd = [
        "docker", "run",
        "--name", job_id,
        image,
        "-u", target,
        "-j",
        "-o", "/tmp/katana.json"
    ]
    
    print(f"DEBUG: Running katana...", file=sys.stderr, flush=True)
    
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
                # Katana prints JSON lines to stdout if -j is allowed there?
                # But we also sent to file.
                print(f"KATANA: {line.strip()}", file=sys.stderr, flush=True)
                
        process.wait()

        # Copy output
        local_output = f"/tmp/{job_id}_katana.json"
        
        cp_cmd = ["docker", "cp", f"{job_id}:/tmp/katana.json", local_output]
        cp_result = subprocess.run(cp_cmd, capture_output=True, text=True)
        
        result_data = []
        
        if cp_result.returncode == 0:
            try:
                with open(local_output, "r") as f:
                    for line in f:
                        if line.strip():
                            result_data.append(json.loads(line))
                os.remove(local_output)
            except Exception as e:
                pass
        else:
             print(f"DEBUG: Could not copy output: {cp_result.stderr}", file=sys.stderr, flush=True)

        return result_data

    except Exception as e:
        print(f"Error running katana: {e}", file=sys.stderr, flush=True)
        return {"error": str(e)}
    finally:
        subprocess.run(["docker", "rm", "-f", job_id], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def main(target: str = "https://scanme.nmap.org"):
    print(f"DEBUG: Starting Katana on {target}", file=sys.stderr, flush=True)
    result = run_katana(target)
    return result

if __name__ == "__main__":
    if len(sys.argv) > 1:
        main(sys.argv[1])
    else:
        main()
