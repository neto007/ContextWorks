import subprocess
import os
import sys
import json
import tempfile
import base64

def run_qiling(
    file_content: bytes = b"",
    filename: str = "binary_file",
    rootfs_path: str = ""
):
    """
    Run qiling emulation.
    
    Args:
        file_content: Binary file content (bytes or base64).
        filename: Binary filename.
        rootfs_path: Path to the rootfs directory.
    """
    image = "python:3-alpine"
    job_id = os.environ.get("WM_JOB_ID", "local_test_qiling")
    
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
    
    # Qiling requires a rootfs. For simple tests, we just import it.
    # We provide a basic script that tries to run the binary.
    qiling_script = f"""
from qiling import Qiling
import sys

def my_qiling():
    ql = Qiling(["/app_data/{filename}"], "/app_data/rootfs")
    ql.run()

if __name__ == "__main__":
    my_qiling()
"""
    
    # Create the qiling runner script
    with open("ql_runner.py", "w") as f:
        f.write(qiling_script)
        
    setup_and_run = (
        "apk add --no-cache build-base cmake >/dev/null && "
        "pip install qiling >/dev/null 2>&1 && "
        "python /app_data/ql_runner.py"
    )
    
    cmd = [
        "docker", "run", "--rm", "--name", job_id,
        "-v", f"{os.getcwd()}:/app_data",
        "-v", f"{os.path.dirname(abs_path)}:/app_data/bin_dir",
        image, "sh", "-c", setup_and_run
    ]
    
    print(f"DEBUG: Running qiling on {filename}...", file=sys.stderr, flush=True)
    
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
    # This is a bit complex to test without a proper rootfs
    if not file_content:
        return {"error": "Provide file_content (binary file bytes)"}
    print(json.dumps(run_binary_path(file_content, filename), indent=2), flush=True)

if __name__ == "__main__":
    main()
