import subprocess
import os
import sys
import json
import tempfile
import base64

def run_apkleaks(
    file_content: bytes = b"",
    filename: str = "app.apk"
):
    """
    Run APKLeaks.
    
    Args:
        file_content: APK file content (bytes or base64).
        filename: APK filename.
    """
    image = "python:3-alpine"
    job_id = os.environ.get("WM_JOB_ID", "local_test_apkleaks")
    
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
        "pip install apkleaks >/dev/null 2>&1 && "
        f"apkleaks -f /app/{base_name} -o /app/results.json"
    )
    
    cmd = [
        "docker", "run", "--rm", "--name", job_id,
        "-v", f"{os.path.dirname(abs_path)}:/app",
        image, "sh", "-c", setup_and_run
    ]
    
    print(f"DEBUG: Running APKLeaks on {filename}...", file=sys.stderr, flush=True)
    
    try:
        # We try to read the results.json from the mounted dir
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        results_file = os.path.join(os.path.dirname(abs_path), "results.json")
        if os.path.exists(results_file):
            with open(results_file, "r") as f:
                findings = json.load(f)
            os.remove(results_file)
            return findings
        else:
            return {
                "stdout": result.stdout,
                "stderr": result.stderr,
                "success": result.returncode == 0,
                "note": "results.json not found"
            }
    except Exception as e:
        return {"error": str(e)}

def main(file_content: bytes = b"", filename: str = "test.apk"):
    if not file_content:
        return {"error": "Provide file_content (APK file bytes)"}
    print(json.dumps(run_apk_file_path(file_content, filename), indent=2), flush=True)

if __name__ == "__main__":
    main()
