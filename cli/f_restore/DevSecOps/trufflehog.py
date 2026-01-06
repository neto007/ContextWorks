import subprocess
import os
import sys
import json

def run_trufflehog(repo_url: str):
    image = "trufflesecurity/trufflehog:latest"
    job_id = os.environ.get("WM_JOB_ID", "local_test_trufflehog")

    # Native Execution Detection (Toolbox Mode)
    import shutil
    trufflehog_bin = shutil.which("trufflehog")
    
    if trufflehog_bin:
        print(f"DEBUG: Found native trufflehog at {trufflehog_bin}. Running in Toolbox mode.", file=sys.stderr, flush=True)
        cmd = [
            trufflehog_bin,
            "git",
            repo_url,
            "--json",
            "--only-verified"
        ]
    else:
        # Fallback to Docker-in-Docker
        print(f"DEBUG: Native trufflehog not found. Pulling image {image}...", file=sys.stderr, flush=True)
        # Allow docker pull output to go to stderr so user sees progress layers
        subprocess.run(["docker", "pull", image], check=True, stdout=sys.stderr, stderr=sys.stderr)
        
        # TruffleHog git command prints JSON to stdout with --json
        cmd = [
            "docker", "run",
            "--name", job_id,
            image,
            "git",
            repo_url,
            "--json",
            "--only-verified" # Filter to only show secrets verified against the provider
        ]
    
    print(f"DEBUG: Running trufflehog...", file=sys.stderr, flush=True)
    
    try:
        process = subprocess.Popen(
            cmd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, 
            text=True, 
            bufsize=1
        )
        
        json_results = []
        
        accumulated_data = b""
        
        # Use os.read for unbuffered reading
        fd = process.stdout.fileno()
        
        while True:
            # Check if process is done
            retcode = process.poll()
            
            # Read available data
            try:
                # We can't block indefinitely on read if process might be dead
                # but os.read blocks.
                # However, since we are inside docker runner, we can't easily use select 
                # if we want to keep it simple.
                # But readline() blocks too.
                # Let's try reading chunk.
                chunk = os.read(fd, 4096)
            except OSError:
                chunk = b""

            if not chunk:
                if retcode is not None:
                    break
                # Only if process is still running but no data, we might spin.
                # But os.read usually blocks until data or EOF.
                continue

            # Process chunk
            accumulated_data += chunk
            
            # Try to decode lines from accumulator
            while b'\n' in accumulated_data:
                line_bytes, remaining = accumulated_data.split(b'\n', 1)
                accumulated_data = remaining
                line = line_bytes.decode('utf-8', errors='replace')
                
                if line:
                    # Each line is a JSON object in JSON output mode for TruffleHog V3?
                    # "trufflehog git ... --json" usually outputs NDJSON.
                    try:
                        obj = json.loads(line)
                        json_results.append(obj)
                        
                        # Extract meaningful info safely
                        detector = obj.get('DetectorName', 'Unknown')
                        
                        # Handle Redacted vs Raw
                        redacted = obj.get('Redacted', '')
                        if not redacted and 'Raw' in obj:
                             raw_val = obj['Raw']
                             if len(raw_val) > 4:
                                 redacted = raw_val[:4] + "..."
                             else:
                                 redacted = "***"
                        
                        # Try to find commit/file info in SourceMetadata
                        # SourceMetadata -> Data -> Git -> ...
                        meta = obj.get('SourceMetadata', {}).get('Data', {})
                        location_info = "Unknown"
                        
                        if 'Git' in meta:
                            git_meta = meta['Git']
                            # Keys might be lowercase or capitalized depending on version
                            commit = git_meta.get('commit', git_meta.get('Commit', 'Unknown'))
                            file_path = git_meta.get('file', git_meta.get('File', 'Unknown'))
                            line_num = git_meta.get('line', git_meta.get('Line', '?'))
                            location_info = f"Commit: {commit}, File: {file_path}:{line_num}"
                        elif 'Filesystem' in meta:
                            fs_meta = meta['Filesystem']
                            file_path = fs_meta.get('file', fs_meta.get('File', 'Unknown'))
                            location_info = f"File: {file_path}"
                        else:
                            # Fallback: print available keys in Data
                            location_info = f"MetaKeys: {list(meta.keys())}"

                        print(f"TRUFFLE: [{detector}] {location_info} | Found: {redacted}", file=sys.stderr, flush=True)
                    except Exception as ex:
                        # Non-json line or parse error
                        print(f"TRUFFLE-LOG: {line.strip()} ({ex})", file=sys.stderr, flush=True)
                
        process.wait()

        return {"repo": repo_url, "secrets": json_results}

    except Exception as e:
        print(f"Error running trufflehog: {e}", file=sys.stderr, flush=True)
        return {"error": str(e)}
    finally:
        subprocess.run(["docker", "rm", "-f", job_id], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def main(repo_url: str = "https://github.com/juice-shop/juice-shop.git"):
    print(f"DEBUG: Starting TruffleHog on {repo_url}", file=sys.stderr, flush=True)
    result = run_trufflehog(repo_url)
    return result

if __name__ == "__main__":
    if len(sys.argv) > 1:
        main(sys.argv[1])
    else:
        main()
