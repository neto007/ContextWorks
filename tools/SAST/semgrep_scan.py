#!/usr/bin/env python3
"""
Semgrep Scan Tool
Executes Semgrep SAST (Static Application Security Testing) with advanced configuration options.
Supports local directories and Git repositories.
"""
import sys
import json
import subprocess
import shutil
import shlex
import os
import tempfile
import re
from pathlib import Path
from urllib.parse import urlparse

def is_git_url(target):
    """Check if target is a Git repository URL."""
    git_patterns = [
        r'^https?://.*\.git$',
        r'^git@.*:.*\.git$',
        r'^https?://github\.com/',
        r'^https?://gitlab\.com/',
        r'^https?://bitbucket\.org/',
    ]
    return any(re.match(pattern, target) for pattern in git_patterns)

def make_paths_relative(data, prefix):
    """
    Recursively walk through the data and replace absolute paths with relative ones.
    """
    if isinstance(data, str):
        if data.startswith(prefix):
            rel_path = data[len(prefix):].lstrip('/')
            return f"./{rel_path}"
        return data
    elif isinstance(data, list):
        return [make_paths_relative(item, prefix) for item in data]
    elif isinstance(data, dict):
        return {key: make_paths_relative(value, prefix) for key, value in data.items()}
    return data

def clone_repository(repo_url, temp_dir, token=None):
    """Clone a Git repository to a temporary directory."""
    print(f"GIT: Cloning repository {repo_url}...", file=sys.stderr, flush=True)
    
    final_url = repo_url
    if token:
        # Inject token into URL
        # Assumes HTTPS URL: https://github.com/user/repo.git -> https://token@github.com/user/repo.git
        if repo_url.startswith("https://"):
            parts = repo_url.split("https://", 1)
            final_url = f"https://{token}@{parts[1]}"
            print("GIT: Using provided token for authentication", file=sys.stderr, flush=True)
    
    try:
        # Avoid leaking token in process list if possible, but for simple clone this acts as CLI arg
        # To mask it in logs, we print repo_url (original) above, not final_url
        result = subprocess.run(
            ['git', 'clone', '--depth', '1', final_url, temp_dir],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=300  # 5 minutes timeout
        )
        
        if result.returncode != 0:
            # Mask token in error message
            error_msg = result.stderr
            if token:
                error_msg = error_msg.replace(token, "***")
            return False, f"Git clone failed: {error_msg}"
        
        print(f"GIT: Repository cloned successfully to {temp_dir}", file=sys.stderr, flush=True)
        return True, None
        
    except subprocess.TimeoutExpired:
        return False, "Git clone timeout (5 minutes)"
    except Exception as e:
        return False, f"Git clone error: {str(e)}"

def main(**args):
    """
    Execute Semgrep scan on local directory or Git repository.
    """
    target = args.get('target')
    if not target:
        return {"status": "error", "message": "Target is required (local path or Git URL)"}

    # Check for semgrep
    semgrep_path = shutil.which("semgrep")
    if not semgrep_path:
        # Fallback path check
        if os.path.exists("/usr/local/bin/semgrep"):
            semgrep_path = "/usr/local/bin/semgrep"
        elif os.path.exists("/usr/bin/semgrep"):
            semgrep_path = "/usr/bin/semgrep"
        else:
            return {"status": "error", "message": f"semgrep binary not found. PATH={os.environ.get('PATH')}"}

    # Check if target is a Git URL or local path
    is_repo = is_git_url(target)
    temp_clone_dir = None
    cleanup_required = False

    # Resolution of Token
    # 1. Argument 'token'
    # 2. Environment 'GITHUB_TOKEN'
    token = args.get('token')
    if not token:
        token = os.environ.get('GITHUB_TOKEN')
    
    if is_repo:
        # Create temporary directory for cloning
        temp_clone_dir = tempfile.mkdtemp(prefix="semgrep_repo_")
        cleanup_required = True
        
        # Clone repository
        success, error = clone_repository(target, temp_clone_dir, token=token)
        if not success:
            if temp_clone_dir and os.path.exists(temp_clone_dir):
                shutil.rmtree(temp_clone_dir)
            return {"status": "error", "message": error}
        
        # Update target to cloned directory
        actual_target = temp_clone_dir
    else:
        # Validate local path
        target = target.strip()
        if not os.path.exists(target):
            return {"status": "error", "message": f"Target path does not exist: {target}"}
        actual_target = target

    # Create temp file for JSON output
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as tmp_json:
        json_output_path = tmp_json.name

    # Base command
    # --json: Output results in JSON format
    # --output: Write to file
    command = [semgrep_path, "scan", "--json", "--output", json_output_path]

    # Add target (will be cloned repo or local directory)
    command.append(actual_target)

    # Config/Rules
    config = args.get('config', 'auto')
    if config:
        command.extend(["--config", config])

    # Severity filter
    severity = args.get('severity')
    if severity:
        command.extend(["--severity", severity])

    # Language filter
    lang = args.get('lang')
    if lang:
        command.extend(["--lang", lang])

    # Exclude patterns
    exclude = args.get('exclude')
    if exclude:
        for pattern in exclude.split(','):
            pattern = pattern.strip()
            if pattern:
                command.extend(["--exclude", pattern])

    # Max memory (MB)
    max_memory = args.get('max_memory')
    if max_memory:
        command.extend(["--max-memory", str(max_memory)])

    # Timeout (seconds)
    timeout = args.get('timeout')
    if timeout:
        command.extend(["--timeout", str(timeout)])

    # Verbose mode for streaming logs
    command.append("--verbose")

    # Extra arguments
    extra_args = args.get('arguments')
    if extra_args:
        command.extend(shlex.split(extra_args))

    try:
        # Popen to stream output
        process = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )
        
        # Stream stderr (Semgrep logs) to platform logs
        # Semgrep outputs progress to stderr
        stderr_lines = []
        while True:
            line = process.stderr.readline()
            if not line and process.poll() is not None:
                break
            if line:
                line = line.strip()
                stderr_lines.append(line)
                print(f"SEMGREP: {line}", file=sys.stderr, flush=True)
                
        # Wait for finish
        process.wait()
        
        # Semgrep return codes:
        # 0: No findings
        # 1: Findings found
        # 2+: Error
        status = "success" if process.returncode in [0, 1] else "error"
        
        scan_data = {}
        error_details = None

        if os.path.exists(json_output_path) and os.path.getsize(json_output_path) > 0:
            try:
                with open(json_output_path, 'r') as f:
                    scan_data = json.load(f)
                
                # Convert absolute paths to relative
                if actual_target:
                    prefix = str(Path(actual_target).absolute())
                    scan_data = make_paths_relative(scan_data, prefix)

                # Semgrep JSON structure has "results" and "errors" keys
                # Consider it success even with return code 1 (findings)
                if process.returncode <= 1:
                    status = "success"
                
            except json.JSONDecodeError as e:
                status = "error"
                error_details = f"Failed to parse Semgrep JSON output: {str(e)}"
        else:
            if process.returncode >= 2:
                status = "error"
                error_details = f"Semgrep failed with exit code {process.returncode}. " + "\n".join(stderr_lines[-5:])
            else:
                # No output but exit code OK - possibly no findings
                scan_data = {"results": [], "errors": []}
                status = "success"

        # Clean up
        if os.path.exists(json_output_path):
            os.remove(json_output_path)

        # Construct summary
        findings_count = 0
        errors_count = 0
        
        if "results" in scan_data:
            findings_count = len(scan_data["results"])
        if "errors" in scan_data:
            errors_count = len(scan_data["errors"])
        
        summary = f"Semgrep scan complete. Found {findings_count} findings"
        if errors_count > 0:
            summary += f" with {errors_count} errors"
        summary += "."
            
        output_data = {
            "status": status,
            "message": summary,
            "data": scan_data
        }
        
        if error_details:
            output_data["data"]["error_details"] = error_details

        return output_data

    except Exception as e:
        import traceback
        traceback.print_exc()
        return {
            "status": "error",
            "message": str(e)
        }
    finally:
        # Cleanup temporary files
        if 'json_output_path' in locals() and os.path.exists(json_output_path):
            os.remove(json_output_path)
        
        # Cleanup cloned repository
        if cleanup_required and temp_clone_dir and os.path.exists(temp_clone_dir):
            print(f"GIT: Cleaning up cloned repository {temp_clone_dir}", file=sys.stderr, flush=True)
            shutil.rmtree(temp_clone_dir)

if __name__ == "__main__":
    params = {}
    if len(sys.argv) > 1:
        try:
            params = json.loads(sys.argv[1])
        except:
            params = {}
    
    print(json.dumps(main(**params), indent=2))
