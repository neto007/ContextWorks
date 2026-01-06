import subprocess
import os
import sys
import json
import glob

def run_paramspider(domain: str):
    image = "python:alpine"
    job_id = os.environ.get("WM_JOB_ID", "local_test_paramspider")

    print(f"DEBUG: Pulling image {image}...", file=sys.stderr, flush=True)
    subprocess.run(["docker", "pull", image], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    # ParamSpider usually writes to results/domain.txt
    install_and_run = (
        "apk add --no-cache git >/dev/null && "
        "git clone https://github.com/devanshbatham/ParamSpider >/dev/null && "
        "cd ParamSpider && pip install . >/dev/null && "
        f"paramspider -d {domain}"
    )

    cmd = [
        "docker", "run",
        "--name", job_id,
        image,
        "sh", "-c",
        install_and_run
    ]
    
    print(f"DEBUG: Running paramspider...", file=sys.stderr, flush=True)
    
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
                print(f"PARAM: {line.strip()}", file=sys.stderr, flush=True)
                
        process.wait()

        # Copy output (results usually in results/)
        # But we don't know exact path? It's typically relative to run dir.
        # We cd'd into ParamSpider, so results/domain.txt inside there.
        
        local_output_dir = f"/tmp/{job_id}_paramspider"
        os.makedirs(local_output_dir, exist_ok=True)
        
        cp_cmd = ["docker", "cp", f"{job_id}:/ParamSpider/results/.", local_output_dir]
        cp_result = subprocess.run(cp_cmd, capture_output=True, text=True)
        
        params = []
        
        if cp_result.returncode == 0:
             # Find txt files
             files = glob.glob(f"{local_output_dir}/*.txt")
             for fpath in files:
                with open(fpath, "r") as f:
                    params.extend([l.strip() for l in f if l.strip()])
             
             import shutil
             shutil.rmtree(local_output_dir)
        else:
             print(f"DEBUG: Could not copy output: {cp_result.stderr}", file=sys.stderr, flush=True)

        return {"domain": domain, "parameters": params}

    except Exception as e:
        print(f"Error running paramspider: {e}", file=sys.stderr, flush=True)
        return {"error": str(e)}
    finally:
        subprocess.run(["docker", "rm", "-f", job_id], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def main(domain: str = "scanme.nmap.org"):
    print(f"DEBUG: Starting ParamSpider on {domain}", file=sys.stderr, flush=True)
    result = run_paramspider(domain)
    return result

if __name__ == "__main__":
    if len(sys.argv) > 1:
        main(sys.argv[1])
    else:
        main()
