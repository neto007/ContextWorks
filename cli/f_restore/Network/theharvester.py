import subprocess
import os
import sys
import json
import urllib.parse
import xml.etree.ElementTree as ET

def run_theharvester(target: str):
    image = "python:alpine" 
    # theHarvester is surprisingly hard to install in alpine due to pip deps.
    # We'll use 'kalilinux/kali-rolling' to ensure success, similar to dnsenum.
    image = "kalilinux/kali-rolling"
    job_id = os.environ.get("WM_JOB_ID", "local_test_theharvester")

    target = target.replace("http://", "").replace("https://", "").split("/")[0]

    # Pull image
    print(f"DEBUG: Pulling image {image}...", file=sys.stderr, flush=True)
    subprocess.run(["docker", "pull", image], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    install_and_run = (
        "apt-get update >/dev/null && "
        "apt-get install -y theharvester >/dev/null && "
        f"theHarvester -d {target} -b all -l 500 -f /tmp/harvester"
    )
    
    cmd = [
        "docker", "run",
        "--name", job_id,
        image,
        "sh", "-c",
        install_and_run
    ]
    
    print(f"DEBUG: Running command: {' '.join(cmd)}", file=sys.stderr, flush=True)
    
    try:
        process = subprocess.Popen(
            cmd, 
            stdout=subprocess.PIPE, 
            stderr=subprocess.PIPE, 
            text=True, 
            bufsize=1
        )
        
        while True:
            line = process.stdout.readline()
            if not line and process.poll() is not None:
                break
            if line:
                line = line.strip()
                print(f"THEHARVESTER: {line}", file=sys.stderr, flush=True)
                
        process.wait()
        
        # Read Output (XML or JSON). -f /tmp/harvester generates /tmp/harvester.xml and .json sometimes?
        # Version 4+ uses JSON by default? Or XML?
        # Let's check for both.
        
        local_json_path = f"/tmp/{job_id}_harvester.json"
        local_xml_path = f"/tmp/{job_id}_harvester.xml"
        
        # Try JSON first
        cp_cmd = ["docker", "cp", f"{job_id}:/tmp/harvester.json", local_json_path]
        cp_result = subprocess.run(cp_cmd, capture_output=True, text=True)
        
        if cp_result.returncode == 0:
            with open(local_json_path, "r") as f:
                return json.load(f)
        
        # If JSON fail, try XML
        cp_cmd_xml = ["docker", "cp", f"{job_id}:/tmp/harvester.xml", local_xml_path]
        cp_result_xml = subprocess.run(cp_cmd_xml, capture_output=True, text=True)
        
        if cp_result_xml.returncode == 0:
            with open(local_xml_path, "r") as f:
                 content = f.read()
            os.remove(local_xml_path)
            # Parse XML logic here if needed
            return {"target": target, "format": "xml", "content": content} # Return raw or parsed?
            
        return {"error": "No output file found (scan failed/empty?)"}

    except Exception as e:
        return {"error": str(e)}

def main(target: str = "scanme.nmap.org"):
    print(f"DEBUG: Scanning target: {target}", file=sys.stderr, flush=True)
    result = run_theharvester(target)
    return result

if __name__ == "__main__":
    target_arg = sys.argv[1] if len(sys.argv) > 1 else "scanme.nmap.org"
    main(target_arg)
