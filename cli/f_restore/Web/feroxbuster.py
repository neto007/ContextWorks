import subprocess
import os
import sys
import json
import glob

def run_feroxbuster(target: str, wordlist_url: str):
    image = "epi052/feroxbuster:latest"
    job_id = os.environ.get("WM_JOB_ID", "local_test_ferox")

    print(f"DEBUG: Pulling image {image}...", file=sys.stderr, flush=True)
    subprocess.run(["docker", "pull", image], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    # Feroxbuster accepts -u target.
    # We need to provide a wordlist. 
    # Feroxbuster can download wordlists? Or we can use curl/wget in a shell.
    # Or strict Feroxbuster image might not have curl/wget.
    # Feroxbuster image is usually minimal (scratch or alpine).
    # If scratch, we can't run shell or wget.
    # Let's check if we can pipe wordlist? `cat wordlist | feroxbuster --stdin` ?
    # Official docs: `--stdin` reads from stdin.
    # So we can run a shell container that pipes to feroxbuster? No, single container.
    # Or we use a generic alpine image and install feroxbuster?
    # Actually, feroxbuster releases binaries. 
    # Use alpine, download binary + wordlist. 
    # This is more robust than relying on minimal image nuances.
    
    install_and_run = (
        "apk add --no-cache curl >/dev/null && "
        # Install Feroxbuster binary
        "curl -sL https://raw.githubusercontent.com/epi052/feroxbuster/master/install-nix.sh | bash >/dev/null && "
        "mv feroxbuster /usr/local/bin/ && "
        # Download wordlist
        f"curl -sL {wordlist_url} -o /tmp/wordlist.txt && "
        # Run
        # --json: output json logs
        # --output: file
        f"feroxbuster --url {target} --wordlist /tmp/wordlist.txt --json --output /tmp/ferox.json --no-state"
    )

    cmd = [
        "docker", "run",
        "--name", job_id,
        "alpine:latest",
        "sh", "-c",
        install_and_run
    ]
    
    print(f"DEBUG: Running feroxbuster...", file=sys.stderr, flush=True)
    
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
                # Feroxbuster stdout (with --json) might be the JSON lines themselves?
                # Or regular logs? 
                # If --json is passed, it logs details in JSON?
                # Actually we used --output /tmp/ferox.json, so stdout might differ.
                print(f"FEROX: {line.strip()}", file=sys.stderr, flush=True)
                
        process.wait()

        # Copy output
        local_output = f"/tmp/{job_id}_ferox.json"
        
        cp_cmd = ["docker", "cp", f"{job_id}:/tmp/ferox.json", local_output]
        cp_result = subprocess.run(cp_cmd, capture_output=True, text=True)
        
        result_data = []
        
        if cp_result.returncode == 0:
            try:
                # Feroxbuster JSON output is NDJSON (one JSON object per line)
                with open(local_output, "r") as f:
                    for line in f:
                        if line.strip():
                            result_data.append(json.loads(line))
                os.remove(local_output)
            except Exception as e:
                # If file exists but empty or parse error
                pass
        else:
             print(f"DEBUG: Could not copy output: {cp_result.stderr}", file=sys.stderr, flush=True)

        return result_data

    except Exception as e:
        print(f"Error running feroxbuster: {e}", file=sys.stderr, flush=True)
        return {"error": str(e)}
    finally:
        subprocess.run(["docker", "rm", "-f", job_id], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def main(target: str = "https://scanme.nmap.org", wordlist: str = "https://raw.githubusercontent.com/danielmiessler/SecLists/master/Discovery/Web-Content/common.txt"):
    print(f"DEBUG: Starting Feroxbuster on {target}", file=sys.stderr, flush=True)
    result = run_feroxbuster(target, wordlist)
    return result

if __name__ == "__main__":
    if len(sys.argv) > 1:
        main(sys.argv[1])
    else:
        main()
