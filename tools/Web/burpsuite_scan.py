#!/usr/bin/env python3
"""
Burp Suite (Dastardly) Tool
DAST scanner by PortSwigger for CI/CD.
"""
import sys
import json
import subprocess
import shutil
import shlex
import os
import tempfile
import xml.etree.ElementTree as ET

def main(**args):
    """
    Execute Dastardly scan.
    """
    target = args.get('target')
    if not target:
        return {"status": "error", "message": "Target is required"}

    # In our K8s environment, we assume the binary 'dastardly' or similar is not there,
    # because Dastardly is typically a full docker image.
    # However, for our 'custom' build mode, we should install required tools.
    # But Dastardly is proprietary/binary. 
    # PortSwigger provides a docker image.
    # If we want to run it INSIDE our worker, we'd need to mock it or find a way.
    # Given the requirements, I will implement it as a wrapper that assumes
    # the environment has been set up to run the scanner.
    
    # Actually, Dastardly is a Java app. We can download and run it if we have JRE.
    # But it's easier to just use their official ECR image in the YAML defined build.
    
    # Let's assume the YAML will use the PortSwigger image as base or install it.
    
    # Construction of command for Dastardly (Java based)
    # Typically: java -jar dastardly.jar ...
    
    # For now, I'll follow the pattern of calling it if it exists.
    dastardly_path = "/usr/local/bin/dastardly" # Placeholder for where we might link it
    
    # Create temp file for XML report
    with tempfile.NamedTemporaryFile(suffix=".xml", delete=False) as tmp:
        report_path = tmp.name

    # Dastardly uses ENV vars for config
    os.environ["BURP_START_URL"] = target
    os.environ["BURP_REPORT_FILE_PATH"] = report_path

    try:
        # Run Dastardly (Assuming it's available in path)
        # PortSwigger image has /dastardly/dastardly.jar
        
        cmd = ["java", "-jar", "/dastardly/dastardly.jar"]
        
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1
        )

        for line in process.stdout:
            print(f"BURP: {line.strip()}", file=sys.stderr, flush=True)

        process.wait()
        
        status = "success" if process.returncode == 0 else "error"
        findings = []
        
        if os.path.exists(report_path) and os.path.getsize(report_path) > 0:
            try:
                tree = ET.parse(report_path)
                root = tree.getroot()
                for testsuite in root.findall(".//testsuite"):
                     for testcase in testsuite.findall("testcase"):
                        failure = testcase.find("failure")
                        if failure is not None:
                            findings.append({
                                "name": testcase.get("name"),
                                "message": failure.get("message"),
                                "detail": failure.text
                            })
                os.remove(report_path)
            except Exception as e:
                print(f"DEBUG: XML Parse error: {e}", file=sys.stderr, flush=True)

        return {
            "status": status,
            "message": f"Burp Dastardly scan complete. Found {len(findings)} issues.",
            "data": {
                "target": target,
                "findings": findings
            }
        }

    except Exception as e:
        if os.path.exists(report_path):
            os.remove(report_path)
        return {"status": "error", "message": str(e)}

if __name__ == "__main__":
    params = {}
    if len(sys.argv) > 1:
        try:
            params = json.loads(sys.argv[1])
        except:
            params = {}
    print(json.dumps(main(**params), indent=2))
