
import sys
import unittest
from unittest.mock import patch, MagicMock, mock_open
import json
import os

# Add the tools directory to path
sys.path.append('/home/machine/repository/windmill/MCPplatform/backend/tools/Web')
import nikto_scan

class TestNiktoScan(unittest.TestCase):
    @patch('nikto_scan.subprocess.Popen')
    @patch('nikto_scan.shutil.which')
    def test_nikto_execution(self, mock_which, mock_popen):
        # Mock nikto existence
        mock_which.return_value = "/usr/bin/nikto"
        
        # Mock subprocess Popen
        mock_process = MagicMock()
        mock_process.returncode = 0
        mock_process.stdout.readline.side_effect = ["Nikto v2.1.6", "Target IP: 127.0.0.1", ""]
        mock_process.poll.side_effect = [0]
        mock_popen.return_value = mock_process
        
        # Mock file I/O for JSON output
        sample_data = {
            "banner": "Apache/2.4.41",
            "host": "scanme.nmap.org",
            "ip": "45.33.32.156",
            "port": 80,
            "vulnerabilities": [
                 {
                     "id": "123",
                     "msg": "X-Frame-Options header is not present"
                 }
            ]
        }
        
        # Use tempfile mocking properly or integration test style? 
        # Since the script uses real tempfile, we should probably mock open/exists or just let it write to a real temp file if we could control the path.
        # But script generates random temp path. 
        # Easier to mock os.path.exists and open.
        
        with patch('builtins.open', mock_open(read_data=json.dumps(sample_data))) as mock_file, \
             patch('os.path.exists', return_value=True), \
             patch('os.path.getsize', return_value=100), \
             patch('os.remove') as mock_remove:
             
            result = nikto_scan.main(target="scanme.nmap.org")
            
            self.assertEqual(result['status'], 'success')
            self.assertIn("Found 1 items", result['message'])
            self.assertEqual(result['data']['banner'], "Apache/2.4.41")
            self.assertEqual(len(result['data']['vulnerabilities']), 1)
            
    @patch('nikto_scan.subprocess.Popen')
    @patch('nikto_scan.shutil.which')
    def test_nikto_failure(self, mock_which, mock_popen):
         mock_which.return_value = "/usr/bin/nikto"
         
         # Mock failure (return code 1 and empty/missing file)
         mock_process = MagicMock()
         mock_process.returncode = 1
         mock_process.stdout.readline.side_effect = ["Error...", ""]
         mock_process.poll.side_effect = [0]
         mock_popen.return_value = mock_process
         
         with patch('os.path.exists', return_value=False): # File not created
             result = nikto_scan.main(target="scanme.nmap.org")
             self.assertEqual(result['status'], 'error')
             # It should match one of our error messages containing "produced no output file"
             self.assertIn("produced no output file", result['data'].get('error_details', ''))

if __name__ == '__main__':
    unittest.main()
