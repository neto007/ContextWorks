import subprocess
import os
import sys
import json
import tempfile
import base64

def run_droidlysis(
    file_content: bytes = b"",
    filename: str = "app.apk"
):
    """
    Run Droidlysis.
    
    Args:
        file_content: APK file content (bytes or base64).
        filename: APK filename.
    """
    image = "python:3-alpine"
    job_id = os.environ.get("WM_JOB_ID", "local_test_droidlysis")
    
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
    
    # Droidlysis has some deps
    setup_and_run = (
        "apk add --no-cache git libmagic >/dev/null && "
        "pip install droidlysis >/dev/null 2>&1 && "
        f"droidlysis --input /app_data/{filename} --output /app_data/droid_out"
    )
    
    cmd = [
        "docker", "run", "--rm", "--name", job_id,
        "-v", f"{tmpdir}:/app_data",
        image, "sh", "-c", setup_and_run
    ]
    
    print(f"DEBUG: Running Droidlysis on {filename}...", file=sys.stderr, flush=True)
    
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
    print(json.dumps(run_apk_path(file_content, filename), indent=2), flush=True)

if __name__ == "__main__":
    main()
