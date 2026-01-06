import subprocess
import os
import sys
import json
import tempfile
import base64

def run_angr(
    file_content: bytes = b"",
    filename: str = "binary_file",
    script_path: str = ""
):
    """
    Run angr.
    
    Args:
        file_content: Binary file content (bytes or base64).
        filename: Binary filename.
        script_path: Path to the angr python script (optional).
    """
    image = "angr/angr:latest"
    job_id = os.environ.get("WM_JOB_ID", "local_test_angr")
    
    abs_bin_path = os.path.abspath(binary_path)
    bin_base = os.path.basename(abs_bin_path)
    
    if script_path:
        abs_script_path = os.path.abspath(script_path)
        script_base = os.path.basename(abs_script_path)
        cmd_run = f"python /app_data/{script_base} /app_data/{bin_base}"
    else:
        # Default: just try to load the project in a python one-liner
        cmd_run = f"python -c \"import angr; p = angr.Project('/app_data/{bin_base}'); print(p.arch)\""
    
    cmd = [
        "docker", "run", "--rm", "--name", job_id,
        "-v", f"{os.path.dirname(abs_bin_path)}:/app_data",
        image, "sh", "-c", cmd_run
    ]
    
    print(f"DEBUG: Running angr on {bin_base}...", file=sys.stderr, flush=True)
    
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
