import subprocess
import os
import sys
import json
import tempfile
import base64

def run_bincat(
    file_content: bytes = b"",
    filename: str = "binary_file"
):
    """
    Run bincat (Binary Code Analysis Toolkit).
    
    Args:
        file_content: Binary file content (bytes or base64).
        filename: Binary filename.
    """
    image = "airbusseclab/bincat:latest"
    job_id = os.environ.get("WM_JOB_ID", "local_test_bincat")
    
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
    
    # bincat usually works with a .ini config file.
    # We'll just show help or run a basic analysis if possible.
    cmd = [
        "docker", "run", "--rm", "--name", job_id,
        "-v", f"{tmpdir}:/app_data",
        image, "bincat", "--help"
    ]
    
    print(f"DEBUG: Running bincat on {filename}...", file=sys.stderr, flush=True)
    
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
