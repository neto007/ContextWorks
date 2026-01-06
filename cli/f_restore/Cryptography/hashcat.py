import subprocess
import os
import sys
import json

def run_hashcat(hash_value: str, hash_mode: str, attack_mode: str):
    image = "kalilinux/kali-rolling"
    job_id = os.environ.get("WM_JOB_ID", "local_test_hashcat")

    # Force CPU (no GPU in standard docker usually)
    # -D 2 might be OpenCL CPU?
    # --force might be needed if it complains about drivers.
    
    install_and_run = (
        "apt-get update >/dev/null && "
        "apt-get install -y hashcat >/dev/null && "
        f"echo '{hash_value}' > /tmp/hash.txt && "
        f"hashcat -m {hash_mode} -a {attack_mode} /tmp/hash.txt --force --show || "  # Try show first
        f"hashcat -m {hash_mode} -a {attack_mode} /tmp/hash.txt --force --potfile-disable --restore-disable"
    )

    cmd = [
        "docker", "run",
        "--name", job_id,
        image,
        "sh", "-c",
        install_and_run
    ]
    
    print(f"DEBUG: Running hashcat...", file=sys.stderr, flush=True)
    
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
                print(f"HASHCAT: {line.strip()}", file=sys.stderr, flush=True)
                
        process.wait()
        
        return {"hash": hash_value, "status": "Finished (check logs)"}

    except Exception as e:
        print(f"Error running hashcat: {e}", file=sys.stderr, flush=True)
        return {"error": str(e)}
    finally:
        subprocess.run(["docker", "rm", "-f", job_id], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def main(hash_value: str = "5f4dcc3b5aa765d61d8327deb882cf99", hash_mode: str = "0", attack_mode: str = "3"):
    print(f"DEBUG: Starting Hashcat", file=sys.stderr, flush=True)
    result = run_hashcat(hash_value, hash_mode, attack_mode)
    return result

if __name__ == "__main__":
    main()
