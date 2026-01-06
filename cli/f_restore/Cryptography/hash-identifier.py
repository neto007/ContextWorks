import subprocess
import os
import sys
import json

def run_hash_id(hash_value: str):
    image = "kalilinux/kali-rolling"
    job_id = os.environ.get("WM_JOB_ID", "local_test_hashid")

    # hash-identifier is usually interactive.
    # We can pipe input.
    
    install_and_run = (
        "apt-get update >/dev/null && "
        "apt-get install -y hash-identifier >/dev/null && "
        f"echo '{hash_value}' | hash-identifier"
    )

    cmd = [
        "docker", "run",
        "--name", job_id,
        image,
        "sh", "-c",
        install_and_run
    ]
    
    print(f"DEBUG: Running hash-identifier...", file=sys.stderr, flush=True)
    
    try:
        process = subprocess.Popen(
            cmd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, 
            text=True, 
            bufsize=1
        )
        
        possible_hashes = []
        
        while True:
            line = process.stdout.readline()
            if not line and process.poll() is not None:
                break
            if line:
                line_stripped = line.strip()
                print(f"HASH-ID: {line_stripped}", file=sys.stderr, flush=True)
                if "[+]" in line_stripped:
                    possible_hashes.append(line_stripped)
                
        process.wait()
        
        return {"hash": hash_value, "possible_types": possible_hashes}

    except Exception as e:
        print(f"Error running hash-identifier: {e}", file=sys.stderr, flush=True)
        return {"error": str(e)}
    finally:
        subprocess.run(["docker", "rm", "-f", job_id], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def main(hash_value: str = "5f4dcc3b5aa765d61d8327deb882cf99"):
    print(f"DEBUG: Starting Hash-Identifier", file=sys.stderr, flush=True)
    result = run_hash_id(hash_value)
    return result

if __name__ == "__main__":
    if len(sys.argv) > 1:
        main(sys.argv[1])
    else:
        main()
