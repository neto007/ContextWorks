import subprocess
import os
import sys
import xml.etree.ElementTree as ET
import json

import urllib.parse

def run_nmap(target: str):
    # Sanitize target (remove http://, https://, trailing slashes)
    if "://" in target:
        try:
            parsed = urllib.parse.urlparse(target)
            target = parsed.netloc
        except Exception:
            pass # fallback to original if parsing fails
    
    # Remove trailing slash if present (and not removed by urlparse)
    target = target.rstrip("/")

    image = "instrumentisto/nmap:latest"
    # Windmill provides the job ID in the environment variable WM_JOB_ID
    job_id = os.environ.get("WM_JOB_ID", "local_test_id")
    
    # Pull image to ensure it's up to date
    subprocess.run(["docker", "pull", image], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    
    # Run nmap with XML output to stdout (-oX -)
    # We name the container with the job ID as required by Windmill, but we do NOT use --rm
    # because Windmill wants to manage the container lifecycle.
    # -oX /tmp/nmap_out.xml : Output XML to file (machine readable)
    # -v : Verbose (to stdout, human readable)
    # --stats-every 5s : Print progress statistics
    cmd = [
        "docker", "run",
        "--name", job_id,
        image,
        "nmap",
        "-Pn", # Treat all hosts as online (skip host discovery)
        "-oX", "/tmp/nmap_out.xml",
        "-v",
        "--stats-every", "5s",
        target
    ]
    
    print(f"DEBUG: Running command: {' '.join(cmd)}", file=sys.stderr, flush=True)
    
    try:
        # Popen to steam output
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )
        
        # Stream stdout (human readable progress)
        while True:
            line = process.stdout.readline()
            if not line and process.poll() is not None:
                break
            if line:
                line = line.strip()
                print(f"NMAP: {line}", file=sys.stderr, flush=True)
                
        # Wait for finish
        process.wait()
        
        # Check if failed
        if process.returncode != 0:
             _, stderr_output = process.communicate()
             print(f"DEBUG: Process stderr: {stderr_output}", file=sys.stderr, flush=True)
             return {"error": "Nmap failed", "details": stderr_output}

        # Read the XML file from the container
        # Since the container has stopped, `docker exec` will fail ("container is not running").
        # We must use `docker cp` to copy the file out.
        
        # Copy to a local temp file
        local_xml_path = f"/tmp/{job_id}_nmap.xml"
        cp_cmd = ["docker", "cp", f"{job_id}:/tmp/nmap_out.xml", local_xml_path]
        cp_result = subprocess.run(cp_cmd, capture_output=True, text=True)
        
        if cp_result.returncode != 0:
             return {"error": "Could not copy output file", "details": cp_result.stderr}
             
        try:
            with open(local_xml_path, "r") as f:
                xml_content = f.read()
            # Clean up local temp file
            os.remove(local_xml_path)
            
            root = ET.fromstring(xml_content)
        except Exception as e:
             return {"error": f"Failed to read or parse local XML: {str(e)}"}
        
        # Clean up container (handled by main try/finally usually, but here manually if needed)
        # Main function usually does cleanup? 
        # Actually nmap.py doesn't have a try/finally for cleanup in run_nmap, let's look at main.
        # Wait, previous code didn't use --rm so container sticks around.
        # We should remove it after reading.
        
        scan_result = {}
        
        scan_result = {
            "target": target, # Use the sanitized target
            "hosts": []
        }
        
        for host in root.findall('host'):
            host_data = {
                "address": "",
                "ports": []
            }
            
            # Get address
            address = host.find('address')
            if address is not None:
                host_data["address"] = address.get('addr')
            
            # Get ports
            ports = host.find('ports')
            if ports is not None:
                for port in ports.findall('port'):
                    port_data = {
                        "port": port.get('portid'),
                        "protocol": port.get('protocol'),
                        "state": port.find('state').get('state'),
                        "service": port.find('service').get('name') if port.find('service') is not None else "unknown"
                    }
                    host_data["ports"].append(port_data)
            
            scan_result["hosts"].append(host_data)
            
        return scan_result
        return scan_result
    except ET.ParseError as e:
        return {"error": f"Failed to parse XML: {str(e)}"}
    except Exception as e:
        print(f"Error running nmap or processing output: {e}", file=sys.stderr, flush=True)
        return {"error": f"An unexpected error occurred: {str(e)}"}
    finally:
        # Cleanup container
        subprocess.run(["docker", "rm", "-f", job_id], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

def main(target: str = "scanme.nmap.org"):
    print(f"DEBUG: Received target: {target}", file=sys.stderr, flush=True)
    result = run_nmap(target)
    return result

if __name__ == "__main__":
    # Windmill passes arguments as named arguments in a way we can just use main calling convention
    # But for a script execution, it often calls the file. 
    # If run as a python script, we need to handle args or rely on Windmill's python execution wrapper.
    # Windmill Python scripts usually expose a main input function.
    
    # For local CLI testing:
    target_arg = sys.argv[1] if len(sys.argv) > 1 else "scanme.nmap.org"
    main(target_arg)
