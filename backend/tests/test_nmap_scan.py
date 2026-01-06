
import sys
import os
import unittest
from unittest.mock import patch, MagicMock

# Add the tools directory to path so we can import the module
sys.path.append('/home/machine/repository/windmill/MCPplatform/backend/tools/Network')
import nmap_scan

class TestNmapScan(unittest.TestCase):
    @patch('nmap_scan.subprocess.Popen')
    @patch('nmap_scan.shutil.which')
    @patch('nmap_scan.ET.parse')
    def test_xml_parsing(self, mock_et_parse, mock_which, mock_popen):
        # Mock nmap existence
        mock_which.return_value = "/usr/bin/nmap"
        
        # Sample Nmap XML Output
        sample_xml = """<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE nmaprun>
<nmaprun scanner="nmap" args="nmap -p 80 -oX - scanme.nmap.org" start="1678888888" startstr="Wed Mar 15 12:00:00 2023" version="7.93" xmloutputversion="1.05">
<host starttime="1678888888" endtime="1678888890">
<status state="up" reason="echo-reply" reason_ttl="50"/>
<address addr="45.33.32.156" addrtype="ipv4"/>
<hostnames>
<hostname name="scanme.nmap.org" type="user"/>
<hostname name="scanme.nmap.org" type="PTR"/>
</hostnames>
<ports>
<port protocol="tcp" portid="80"><state state="open" reason="syn-ack" reason_ttl="50"/><service name="http" method="table" conf="3"/></port>
<port protocol="tcp" portid="9929"><state state="closed" reason="reset" reason_ttl="50"/><service name="nping-echo" method="table" conf="3"/></port>
</ports>
<os>
<osmatch name="Linux 5.4" accuracy="100" line="65605">
<osclass type="general purpose" vendor="Linux" osfamily="Linux" osgen="5.X" accuracy="100"><cpe>cpe:/o:linux:linux_kernel:5.4</cpe></osclass>
</osmatch>
</os>
</host>
</nmaprun>
"""
        # Mock ET.parse to return a tree from string
        import xml.etree.ElementTree as ET
        mock_tree = MagicMock()
        mock_tree.getroot.return_value = ET.fromstring(sample_xml)
        mock_et_parse.return_value = mock_tree

        # Mock subprocess Popen
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.stdout.readline.side_effect = ["Starting Nmap...", "Scanning...", ""]
        mock_process.poll.side_effect = [0] # Done immediately when checked
        mock_popen.return_value = mock_process

        # Run main
        result = nmap_scan.main(target="scanme.nmap.org", port_spec="80")

        # Assertions
        self.assertEqual(result['status'], 'success')
        self.assertIn("Found 1 hosts and 1 open ports", result['message'])
        
        # Verify cleaner output (no command, no raw_output_tail)
        self.assertNotIn("command", result['data'])
        self.assertNotIn("raw_output_tail", result['data'])

        data = result['data']
        self.assertEqual(len(data['hosts']), 1)
        host = data['hosts'][0]
        self.assertEqual(host['address'], "45.33.32.156")
        self.assertIn("scanme.nmap.org", host['hostnames'])
        
        self.assertEqual(len(host['ports']), 2)
        port_80 = next(p for p in host['ports'] if p['port'] == 80)
        self.assertEqual(port_80['state'], 'open')
        self.assertEqual(port_80['service'], 'http')
        
        port_9929 = next(p for p in host['ports'] if p['port'] == 9929)
        self.assertEqual(port_9929['state'], 'closed')

        print("Test passed successfully!")

if __name__ == '__main__':
    unittest.main()
