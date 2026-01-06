import subprocess
import os
import sys
import json

def run_dirsearch(target: str):
    image = "kalilinux/kali-rolling"
    job_id = os.environ.get("WM_JOB_ID", "local_test_dirsearch")

    print(f"DEBUG: Pulling image {image}...", file=sys.stderr, flush=True)
    subprocess.run(["docker", "pull", image], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    # Use Kali's dirsearch package.
    # It usually comes with wordlists in /usr/share/dirsearch or /usr/share/wordlists
    install_and_run = (
        "apt-get update >/dev/null && "
        "apt-get install -y dirsearch >/dev/null && "
        f"dirsearch -u {target} --format=json -o /tmp/report.json"
    )

    cmd = [
        "docker", "run",
        "--name", job_id,
        image,
        "sh", "-c",
        install_and_run
    ]
    
    print(f"DEBUG: Running dirsearch...", file=sys.stderr, flush=True)
    
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
                print(f"DIRSEARCH: {line.strip()}", file=sys.stderr, flush=True)
                
        process.wait()

        # Copy output
        local_output = f"/tmp/{job_id}_dirsearch.json"
        
        cp_cmd = ["docker", "cp", f"{job_id}:/tmp/report.json", local_output]
        cp_result = subprocess.run(cp_cmd, capture_output=True, text=True)
        
        result_data = {}
        
        if cp_result.returncode == 0:
            try:
                with open(local_output, "r") as f:
                    result_data = json.load(f)
                os.remove(local_output)
            except Exception as e:
                # File might be empty if no findings
                pass
        else:
             print(f"DEBUG: Could not copy output: {cp_result.stderr}", file=sys.stderr, flush=True)

        return result_data

    except Exception as e:
        print(f"Error running dirsearch: {e}", file=sys.stderr, flush=True)
        return {"error": str(e)}
    finally:
        subprocess.run(["docker", "rm", "-f", job_id], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def main(target: str = "https://scanme.nmap.org"):
    print(f"DEBUG: Starting Dirsearch on {target}", file=sys.stderr, flush=True)
    result = run_dirsearch(target)
    return result

if __name__ == "__main__":
    if len(sys.argv) > 1:
        main(sys.argv[1])
    else:
        main()
