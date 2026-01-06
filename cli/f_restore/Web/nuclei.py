import subprocess
import os
import sys
import json
import urllib.parse

def run_nuclei(target: str):
    image = "projectdiscovery/nuclei:latest"
    job_id = os.environ.get("WM_JOB_ID", "local_test_nuclei")

    # Sanitize target logic
    # Nuclei handles URLs well, but usually wants protocol if web scanning
    if "://" not in target:
         target = f"https://{target}"

    # Pull image
    print(f"DEBUG: Pulling image {image}...", file=sys.stderr, flush=True)
    subprocess.run(["docker", "pull", image], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    # Construct command
    # -u target : Target URL
    # -j : JSON output
    # -o /tmp/nuclei_out.json : Output file (JSON lines)
    # -nc : No color (for easier log reading, though raw ansi works too)
    # -stats : Show stats
    # We want text output on stdout to stream to user, and JSON to file.
    # Nuclei sends "findings" to stdout by default.
    # If we use -o, it might silence stdout? 
    # Usually -o writes to file AND stdout still happens unless silent.
    # Let's verify behaviors. But generally scanners do both.
    
    cmd = [
        "docker", "run",
        "--name", job_id,
        image,
        "-u", target,
        "-json-export", "/tmp/nuclei_out.json", # JSON export to file
        "-no-color",
        "-stats" 
        # Note: Nuclei defaults to downloading templates on first run. 
        # This image works out of the box.
    ]
    
    print(f"DEBUG: Running command: {' '.join(cmd)}", file=sys.stderr, flush=True)
    
    try:
        # Popen to steam output
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
                line = line.strip()
                # Print to logs so user sees progress
                print(f"NUCLEI: {line}", file=sys.stderr, flush=True)
                
        # Wait for finish
        process.wait()
        
        # Read the JSON file from the container
        # Nuclei -json-export can output a JSON array or NDJSON depending on version/flags.
        # We handle both cases to ensure a flat list of findings.
        
        local_json_path = f"/tmp/{job_id}_nuclei.json"
        cp_cmd = ["docker", "cp", f"{job_id}:/tmp/nuclei_out.json", local_json_path]
        cp_result = subprocess.run(cp_cmd, capture_output=True, text=True)
        
        if cp_result.returncode != 0:
             return {"error": "Could not copy output file", "details": cp_result.stderr}
             
        results = []
        try:
            with open(local_json_path, "r") as f:
                # First try to load as a single JSON entity (e.g. Array)
                try:
                    file_content = f.read()
                    data = json.loads(file_content)
                    if isinstance(data, list):
                        results = data
                    elif isinstance(data, dict):
                        results = [data]
                except json.JSONDecodeError:
                    # Fallback to NDJSON (line by line)
                    # Reset file pointer or just use the content read
                    f.seek(0) # Logic above read all, but if it failed, maybe it's multi-object
                    # Actually json.loads won't fail on valid JSON array, but will on NDJSON
                    # parse lines from file_content
                    for line in file_content.splitlines():
                        if line.strip():
                            try:
                                results.append(json.loads(line))
                            except:
                                pass
                                
            if os.path.exists(local_json_path):
                os.remove(local_json_path)
            
            return {"target": target, "findings": results}
        except Exception as e:
            return {"error": f"Failed to read/parse output: {str(e)}"}

    except Exception as e:
        return {"error": str(e)}

def main(target: str = "https://scanme.nmap.org"):
    print(f"DEBUG: Scanning target: {target}", file=sys.stderr, flush=True)
    result = run_nuclei(target)
    return result

if __name__ == "__main__":
    target_arg = sys.argv[1] if len(sys.argv) > 1 else "https://scanme.nmap.org"
    main(target_arg)
