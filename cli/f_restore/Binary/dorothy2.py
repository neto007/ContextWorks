import subprocess
import os
import sys
import json
import tempfile
import base64

def run_dorothy2(
    file_content: bytes = b"",
    filename: str = "binary_file"
):
    """
    Run dorothy2 (Malware Analysis Framework).
    
    Args:
        file_content: Binary file content (bytes or base64).
        filename: Binary filename.
    """
    image = "ruby:alpine"
    job_id = os.environ.get("WM_JOB_ID", "local_test_dorothy2")
    
    if isinstance(file_content, str):
        try:
            file_content = base64.b64decode(file_content)
        except:
            return {"error": "file_content must be bytes or valid base64 string"}
    
    if not file_content:
        return {"error": "file_content cannot be empty"}
    
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = os.path.join(tmpdir, filename)
        
        with open(file_path, 'wb') as f:
            f.write(file_content)
        
        print(f"DEBUG: File created: {file_path} ({len(file_content)} bytes)", file=sys.stderr, flush=True)
    
    setup_and_run = (
        "apk add --no-cache git build-base libxml2-dev libxslt-dev >/dev/null && "
        "git clone https://github.com/m4rco-/dorothy2.git /app >/dev/null && "
        "cd /app && "
        "bundle install >/dev/null 2>&1 && "
        f"ruby dorothy.rb -m {base_name}" # Example usage
    )
    
    cmd = [
        "docker", "run", "--rm", "--name", job_id,
        "-v", f"{os.path.dirname(abs_path)}:/app/malware",
        image, "sh", "-c", setup_and_run
    ]
    
    print(f"DEBUG: Running dorothy2 on {filename}...", file=sys.stderr, flush=True)
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        return {
            "stdout": result.stdout,
            "stderr": result.stderr,
            "success": result.returncode == 0
        }
    except Exception as e:
        return {"error": str(e)}

def main(file_content: bytes = b"", filename: str = "binary_file"):
    if not file_content:
        return {"error": "Provide file_content (binary file bytes)"}
    print(json.dumps(run_binary_path(file_content, filename), indent=2), flush=True)

if __name__ == "__main__":
    main()
