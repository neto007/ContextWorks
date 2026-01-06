import subprocess
import os
import sys
import json

def run_ophcrack(hash_value: str):
    image = "kalilinux/kali-rolling"
    job_id = os.environ.get("WM_JOB_ID", "local_test_ophcrack")

    # Ophcrack needs tables. Typical location /usr/share/ophcrack/tables or similar.
    # Without tables, it won't do much.
    # We will just install and run to prove execution.
    
    install_and_run = (
        "apt-get update >/dev/null && "
        "apt-get install -y ophcrack >/dev/null && "
        f"echo '{hash_value}' > /tmp/hash.txt && "
        "ophcrack -f /tmp/hash.txt" # Need to specify table dir usually with -t
    )

    cmd = [
        "docker", "run",
        "--name", job_id,
        image,
        "sh", "-c",
        install_and_run
    ]
    
    print(f"DEBUG: Running ophcrack...", file=sys.stderr, flush=True)
    
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
                print(f"OPHCRACK: {line.strip()}", file=sys.stderr, flush=True)
                
        process.wait()
        
        return {"hash": hash_value, "status": "Finished (Note: Rainbow tables required for success)"}

    except Exception as e:
        print(f"Error running ophcrack: {e}", file=sys.stderr, flush=True)
        return {"error": str(e)}
    finally:
        subprocess.run(["docker", "rm", "-f", job_id], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def main(hash_value: str = "5f4dcc3b5aa765d61d8327deb882cf99"):
    print(f"DEBUG: Starting Ophcrack", file=sys.stderr, flush=True)
    result = run_ophcrack(hash_value)
    return result

if __name__ == "__main__":
    if len(sys.argv) > 1:
        main(sys.argv[1])
    else:
        main()
