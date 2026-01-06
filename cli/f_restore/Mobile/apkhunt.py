import subprocess
import os
import sys
import json
import tempfile
import base64

def run_apkhunt(
    file_content: bytes = b"",
    filename: str = "app.apk"
):
    """
    Run APKHunt.
    
    Args:
        file_content: APK file content (bytes or base64).
        filename: APK filename.
    """
    image = "golang:alpine"
    job_id = os.environ.get("WM_JOB_ID", "local_test_apkhunt")
    
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
            "apk add --no-cache git >/dev/null && "
            "git clone https://github.com/Cyber-Buddy/APKHunt.git /app >/dev/null && "
            "cd /app && "
            "go build -o APKHunt main.go >/dev/null 2>&1 && "
            f"./APKHunt -p /app_data/{filename}"
        )
        
        cmd = [
            "docker", "run", "--rm", "--name", job_id,
            "-v", f"{tmpdir}:/app_data",
            image, "sh", "-c", setup_and_run
        ]
        
        print(f"DEBUG: Running APKHunt on {filename}...", file=sys.stderr, flush=True)
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "success": result.returncode == 0
            }
        except Exception as e:
            return {"error": str(e)}

def main(file_content: bytes = b"", filename: str = "test.apk"):
    if not file_content:
        return {"error": "Provide file_content (APK file bytes)"}
    print(json.dumps(run_apkhunt(file_content, filename), indent=2), flush=True)

if __name__ == "__main__":
    main()

