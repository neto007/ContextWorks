#!/usr/bin/env python3
"""
Script para converter ferramentas restantes de path para file_content pattern.
Converte 14 ferramentas restantes (apkhunt já foi feita manualmente).
"""

import os
import re

# Template base para conversão
PYTHON_TEMPLATE = '''import subprocess
import os
import sys
import json
import tempfile
import base64

def {func_name}(
    file_content: bytes = b"",
    filename: str = "{default_filename}"
):
    """
    {docstring}
    
    Args:
        file_content: {file_type} file content (bytes or base64).
        filename: {file_type} filename.
    """
    image = "{docker_image}"
    job_id = os.environ.get("WM_JOB_ID", "local_test_{tool_name}")
    
    if isinstance(file_content, str):
        try:
            file_content = base64.b64decode(file_content)
        except:
            return {{"error": "file_content must be bytes or valid base64 string"}}
    
    if not file_content:
        return {{"error": "file_content cannot be empty"}}
    
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = os.path.join(tmpdir, filename)
        
        with open(file_path, 'wb') as f:
            f.write(file_content)
        
        print(f"DEBUG: File created: {{file_path}} ({{len(file_content)}} bytes)", file=sys.stderr, flush=True)
        
        {setup_and_run}
        
        cmd = [
            "docker", "run", "--rm", "--name", job_id,
            "-v", f"{{tmpdir}}:/app_data",
            image, "sh", "-c", setup_and_run
        ]
        
        print(f"DEBUG: Running {tool_display} on {{filename}}...", file=sys.stderr, flush=True)
        
        try:
            result = subprocess.run(cmd, capture_output=True, text=True)
            return {{
                "stdout": result.stdout,
                "stderr": result.stderr,
                "success": result.returncode == 0
            }}
        except Exception as e:
            return {{"error": str(e)}}

def main(file_content: bytes = b"", filename: str = "{default_filename}"):
    if not file_content:
        return {{"error": "Provide file_content ({file_type} file bytes)"}}
    print(json.dumps({func_name}(file_content, filename), indent=2), flush=True)

if __name__ == "__main__":
    main()
'''

# Ferramentas restantes para converter (14)
TOOLS_REMAINING = [
    # APK tools (5 restantes)
    ("adhrit", "adhrit.py", "Run Adhrit", "APK", "python:3-alpine", "test.apk"),
    ("androwarn", "androwarn.py", "Run Androwarn", "APK", "python:3-alpine", "test.apk"),
    ("apkleaks", "apkleaks.py", "Run APKLeaks", "APK", "python:3-alpine", "test.apk"),
    ("app_info_scanner", "app_info_scanner.py", "Run AppInfoScanner", "APK", "python:3-alpine", "test.apk"),
    ("droidlysis", "droidlysis.py", "Run Droidlysis", "APK", "python:3-alpine", "test.apk"),
    
    # Binary tools (9)
    ("rz_ghidra", "rz_ghidra.py", "Run rz-ghidra", "Binary", "rizinorg/rizin:latest", "/bin/ls"),
    ("cwe_checker", "cwe_checker.py", "Run cwe_checker", "Binary", "fkiecad/cwe_checker", "/bin/ls"),
    ("habo", "habo.py", "Run HaboMalHunter", "Binary", "ubuntu:20.04", "/bin/ls"),
    ("qiling", "qiling.py", "Run qiling", "Binary", "python:3-alpine", "/bin/ls"),
    ("dorothy2", "dorothy2.py", "Run dorothy2", "Binary", "ruby:alpine", "test.exe"),
    ("bincat", "bincat.py", "Run bincat", "Binary", "airbusseclab/bincat:latest", "/bin/ls"),
    ("binwalk", "binwalk.py", "Run binwalk", "Binary", "python:3-alpine", "/bin/ls"),
    ("angr", "angr.py", "Run angr", "Binary", "angr/angr:latest", "/bin/ls"),
    ("binabs", "binabs.py", "Run BinAbsInspector", "Binary", "openjdk:11-jre-slim", "/bin/ls"),
]

print(f"Ferramentas restantes para converter: {len(TOOLS_REMAINING)}", flush=True)
for tool in TOOLS_REMAINING:
    print(f"  - {tool[1]}", flush=True)
