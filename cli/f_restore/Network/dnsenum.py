import subprocess
import os
import sys
import json
import urllib.parse
import xml.etree.ElementTree as ET

def run_dnsenum(target: str):
    image = "kalilinux/kali-rolling"
    job_id = os.environ.get("WM_JOB_ID", "local_test_dnsenum")

    target = target.replace("http://", "").replace("https://", "").split("/")[0]

    # Pull image
    print(f"DEBUG: Pulling image {image}...", file=sys.stderr, flush=True)
    subprocess.run(["docker", "pull", image], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    # apt update/install is slow but reliable for kali tools
    # dnsenum -o /tmp/output.xml domain
    install_and_run = (
        "apt-get update >/dev/null && "
        "apt-get install -y dnsenum >/dev/null && "
        f"dnsenum {target} -o /tmp/dnsenum.xml --noreverse"
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
                print(f"DNSENUM: {line}", file=sys.stderr, flush=True)
                
        process.wait()
        
        # Read XML output
        local_xml_path = f"/tmp/{job_id}_dnsenum.xml"
        cp_cmd = ["docker", "cp", f"{job_id}:/tmp/dnsenum.xml", local_xml_path]
        cp_result = subprocess.run(cp_cmd, capture_output=True, text=True)
        
        if cp_result.returncode != 0:
             return {"error": "Could not copy output file", "details": cp_result.stderr}
             
        try:
            with open(local_xml_path, "r") as f:
                content = f.read()
            os.remove(local_xml_path)
            
            # Simple XML to Dict? Dnsenum XML structure is a bit flat.
            # <testdata> <hostnames> <host> ... </host> </hostnames> </testdata>
            # We'll just return the raw XML string or rudimentary parse?
            # User wants JSON parsing.
            
            root = ET.fromstring(content)
            findings = []
            
            # Extract hosts (A records, etc)
            for host in root.findall(".//host"):
                name = host.find("hostname").text if host.find("hostname") is not None else ""
                ip = host.find("ip").text if host.find("ip") is not None else ""
                findings.append({"hostname": name, "ip": ip})
                
            return {"target": target, "findings": findings}
        except Exception as e:
            return {"error": f"Failed to parse XML: {str(e)}", "raw": content if 'content' in locals() else "N/A"}

    except Exception as e:
        return {"error": str(e)}

def main(target: str = "scanme.nmap.org"):
    print(f"DEBUG: Scanning target: {target}", file=sys.stderr, flush=True)
    result = run_dnsenum(target)
    return result

if __name__ == "__main__":
    target_arg = sys.argv[1] if len(sys.argv) > 1 else "scanme.nmap.org"
    main(target_arg)
