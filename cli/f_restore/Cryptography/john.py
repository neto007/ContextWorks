import subprocess
import os
import sys
import json

def run_john(hash_value: str, hash_type: str):
    image = "kalilinux/kali-rolling"
    job_id = os.environ.get("WM_JOB_ID", "local_test_john")

    # Install john dynamically to ensure latest
    install_and_run = (
        "apt-get update >/dev/null && "
        "apt-get install -y john >/dev/null && "
        f"echo '{hash_value}' > /tmp/hash.txt && "
        f"john --format={hash_type} /tmp/hash.txt && "
        "john --show /tmp/hash.txt"
    )

    cmd = [
        "docker", "run",
        "--name", job_id,
        image,
        "sh", "-c",
        install_and_run
    ]
    
    print(f"DEBUG: Running John on hash...", file=sys.stderr, flush=True)
    
    try:
        process = subprocess.Popen(
            cmd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, 
            text=True, 
            bufsize=1
        )
        
        cracked = None
        
        while True:
            line = process.stdout.readline()
            if not line and process.poll() is not None:
                break
            if line:
                line_stripped = line.strip()
                print(f"JOHN: {line_stripped}", file=sys.stderr, flush=True)
                # Output of --show: "password"
                if ":" in line_stripped: 
                    # Usually "user:password" or just "password" depending on format
                    cracked = line_stripped
                
        process.wait()
        
        return {"hash": hash_value, "cracked": cracked or "Not Compliant/Failed"}

    except Exception as e:
        print(f"Error running john: {e}", file=sys.stderr, flush=True)
        return {"error": str(e)}
    finally:
        subprocess.run(["docker", "rm", "-f", job_id], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def main(hash_value: str = "5f4dcc3b5aa765d61d8327deb882cf99", hash_type: str = "raw-md5"):
    print(f"DEBUG: Starting John", file=sys.stderr, flush=True)
    result = run_john(hash_value, hash_type)
    return result

if __name__ == "__main__":
    main()
