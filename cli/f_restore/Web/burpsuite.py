import subprocess
import os
import sys
import json
import xml.etree.ElementTree as ET

def run_dastardly(target: str):
    image = "public.ecr.aws/portswigger/dastardly:latest"
    job_id = os.environ.get("WM_JOB_ID", "local_test_dastardly")

    print(f"DEBUG: Pulling image {image}...", file=sys.stderr, flush=True)
    try:
        subprocess.run(["docker", "pull", image], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True) # stderr=PIPE to capture
    except subprocess.CalledProcessError as e:
         print(f"DEBUG: Docker pull failed: {e.stderr}", file=sys.stderr, flush=True)
         # Fallback? Maybe skip pull and try run if local exists?
         # Dastardly needs latest usually.
         # Re-raise or return error
         return {"error": f"Failed to pull Dastardly image: {e.stderr}"}
    
    # Dastardly outputs to a report file.
    # Env vars (Updated for 2025+ versions):
    # BURP_START_URL (previously DASTARDLY_TARGET_URL)
    # BURP_REPORT_FILE_PATH (previously DASTARDLY_OUTPUT_FILE)
    
    # Dastardly runs as user 'dastardly' (uid 1000). 
    # Must write to a writable dir like /tmp.
    
    cmd = [
        "docker", "run",
        "--name", job_id,
        "-e", f"BURP_START_URL={target}",
        "-e", "BURP_REPORT_FILE_PATH=/tmp/dastardly-report.xml",
        image
    ]

    print(f"DEBUG: Running Dastardly (Burp Suite)...", file=sys.stderr, flush=True)
    
    try:
        process = subprocess.Popen(
            cmd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.STDOUT, # Merge stderr into stdout
            text=True, 
            bufsize=1
        )
        
        while True:
            line = process.stdout.readline()
            if not line and process.poll() is not None:
                break
            if line:
                print(f"BURP: {line.strip()}", file=sys.stderr, flush=True)
                
        process.wait()

        # Copy output
        local_output = f"/tmp/{job_id}_report.xml"
        
        cp_cmd = ["docker", "cp", f"{job_id}:/tmp/dastardly-report.xml", local_output]
        cp_result = subprocess.run(cp_cmd, capture_output=True, text=True)
        
        findings = []
        
        if cp_result.returncode == 0:
            try:
                # Parse JUnit XML to JSON
                tree = ET.parse(local_output)
                root = tree.getroot()
                # JUnit format: testsuites -> testsuite -> testcase
                # Dastardly uses testcase for each finding? Or suite?
                # Usually: <testcase name="..."><failure message="...">...</failure></testcase>
                
                for testsuite in root.findall(".//testsuite"):
                     for testcase in testsuite.findall("testcase"):
                        # If failed, it's a finding?
                        failure = testcase.find("failure")
                        if failure is not None:
                            findings.append({
                                "name": testcase.get("name"),
                                "severity": "vulnerability", # Dastardly failure means found issue
                                "message": failure.get("message"),
                                "detail": failure.text
                            })
                            
                os.remove(local_output)
            except Exception as e:
                print(f"DEBUG: XML Parse error: {e}", file=sys.stderr, flush=True)
        else:
             print(f"DEBUG: Could not copy output (might be empty/failed run): {cp_result.stderr}", file=sys.stderr, flush=True)

        return {
            "target": target,
            "tool": "Dastardly (Burp Suite)",
            "count": len(findings),
            "findings": findings
        }

    except Exception as e:
        print(f"Error running dastardly: {e}", file=sys.stderr, flush=True)
        return {"error": str(e)}
    finally:
        subprocess.run(["docker", "rm", "-f", job_id], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def main(target: str = "https://gin-and-juice.shop"):
    print(f"DEBUG: Starting Burp Suite (Dastardly) on {target}", file=sys.stderr, flush=True)
    result = run_dastardly(target)
    # Output to stdout to satisfy windmill script structure (last return)
    # But usually returned dict is handled by engine.
    # For CLI test:
    # print(json.dumps(result, indent=2), flush=True)
    return result

if __name__ == "__main__":
    if len(sys.argv) > 1:
        main(sys.argv[1])
    else:
        main()
