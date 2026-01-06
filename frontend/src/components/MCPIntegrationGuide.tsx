import React, { useState } from 'react';
import { Copy, Check, BookOpen, Terminal, Code, ArrowLeft } from 'lucide-react';

interface MCPIntegrationGuideProps {
    onBack: () => void;
}

const MCPIntegrationGuide: React.FC<MCPIntegrationGuideProps> = ({ onBack }) => {
    const [copiedSnippet, setCopiedSnippet] = useState<string | null>(null);

    const handleCopy = (text: string, id: string) => {
        navigator.clipboard.writeText(text);
        setCopiedSnippet(id);
        setTimeout(() => setCopiedSnippet(null), 2000);
    };

    const claudeConfig = `{
  "mcpServers": {
    "security-platform": {
      "command": "curl",
      "args": [
        "-X", "POST",
        "-H", "Authorization: Bearer YOUR_API_KEY_HERE",
        "-H", "Content-Type: application/json",
        "-d", "@-",
        "http://localhost:8000/mcp/YOUR_MCP_ID/message"
      ]
    }
  }
}`;

    const curlExample = `# Initialize MCP
curl -X POST http://localhost:8000/mcp/YOUR_MCP_ID/message \\
  -H "Authorization: Bearer YOUR_API_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{
    "jsonrpc": "2.0",
    "id": 1,
    "method": "initialize",
    "params": {
      "protocolVersion": "2024-11-05"
    }
  }'

# List available tools
curl -X POST http://localhost:8000/mcp/YOUR_MCP_ID/message \\
  -H "Authorization: Bearer YOUR_API_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{
    "jsonrpc": "2.0",
    "id": 2,
    "method": "tools/list",
    "params": {}
  }'

# Execute a tool
curl -X POST http://localhost:8000/mcp/YOUR_MCP_ID/message \\
  -H "Authorization: Bearer YOUR_API_KEY" \\
  -H "Content-Type: application/json" \\
  -d '{
    "jsonrpc": "2.0",
    "id": 3,
    "method": "tools/call",
    "params": {
      "name": "nikto",
      "arguments": {
        "target": "https://example.com"
      }
    }
  }'`;

    const pythonExample = `import requests

MCP_ID = "YOUR_MCP_ID"
API_KEY = "YOUR_API_KEY"
BASE_URL = "http://localhost:8000"

headers = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

# List tools
response = requests.post(
    f"{BASE_URL}/mcp/{MCP_ID}/message",
    headers=headers,
    json={
        "jsonrpc": "2.0",
        "id": 1,
        "method": "tools/list",
        "params": {}
    }
)

tools = response.json()["result"]["tools"]
print(f"Available tools: {[t['name'] for t in tools]}")

# Execute tool
response = requests.post(
    f"{BASE_URL}/mcp/{MCP_ID}/message",
    headers=headers,
    json={
        "jsonrpc": "2.0",
        "id": 2,
        "method": "tools/call",
        "params": {
            "name": "nikto",
            "arguments": {"target": "https://example.com"}
        }
    }
)

result = response.json()["result"]
print(result["content"][0]["text"])`;

    return (
        <div className="bg-[#0b0b11] rounded-lg shadow-xl border border-[#1a1b26] overflow-hidden">
            <div className="bg-gradient-to-r from-[#8be9fd]/20 to-[#bd93f9]/20 px-6 py-4 border-b border-[#1a1b26] flex items-center justify-between">
                <div>
                    <div className="flex items-center gap-3">
                        <BookOpen size={24} className="text-[#8be9fd]" />
                        <h3 className="text-xl font-bold text-white uppercase tracking-wider">Integration Guide</h3>
                    </div>
                    <p className="text-sm text-[#6272a4] mt-2">How to connect LLMs and applications to your MCP servers</p>
                </div>
                <button
                    onClick={onBack}
                    className="p-2 hover:bg-white/10 rounded-full transition-colors group"
                    title="Back to MCPs"
                >
                    <ArrowLeft size={20} className="text-[#f8f8f2] group-hover:text-white" />
                </button>
            </div>

            <div className="p-6 space-y-6">
                {/* Claude Desktop */}
                <div>
                    <div className="flex items-center gap-2 mb-3">
                        <Terminal size={18} className="text-[#bd93f9]" />
                        <h4 className="text-lg font-bold text-[#bd93f9] uppercase tracking-wide">Claude Desktop</h4>
                    </div>
                    <p className="text-sm text-[#f8f8f2] mb-3">
                        Add this configuration to your <code className="bg-[#1a1b26] px-2 py-1 rounded text-[#50fa7b] font-mono text-xs">claude_desktop_config.json</code>:
                    </p>
                    <div className="relative">
                        <pre className="bg-[#1a1b26] rounded p-4 text-xs font-mono text-[#f8f8f2] overflow-x-auto custom-scrollbar">
                            {claudeConfig}
                        </pre>
                        <button
                            onClick={() => handleCopy(claudeConfig, 'claude')}
                            className="absolute top-3 right-3 p-2 bg-[#282a36] hover:bg-[#44475a] rounded transition-colors"
                        >
                            {copiedSnippet === 'claude' ? (
                                <Check size={16} className="text-[#50fa7b]" />
                            ) : (
                                <Copy size={16} className="text-[#6272a4]" />
                            )}
                        </button>
                    </div>
                    <div className="mt-2 text-xs text-[#6272a4] flex items-start gap-2">
                        <span>💡</span>
                        <span>Replace <code className="text-[#f1fa8c]">YOUR_MCP_ID</code> and <code className="text-[#f1fa8c]">YOUR_API_KEY</code> with values from your MCP above</span>
                    </div>
                </div>

                {/* cURL Examples */}
                <div>
                    <div className="flex items-center gap-2 mb-3">
                        <Terminal size={18} className="text-[#50fa7b]" />
                        <h4 className="text-lg font-bold text-[#50fa7b] uppercase tracking-wide">cURL Examples</h4>
                    </div>
                    <p className="text-sm text-[#f8f8f2] mb-3">
                        Test your MCP server using cURL:
                    </p>
                    <div className="relative">
                        <pre className="bg-[#1a1b26] rounded p-4 text-xs font-mono text-[#f8f8f2] overflow-x-auto custom-scrollbar max-h-[400px]">
                            {curlExample}
                        </pre>
                        <button
                            onClick={() => handleCopy(curlExample, 'curl')}
                            className="absolute top-3 right-3 p-2 bg-[#282a36] hover:bg-[#44475a] rounded transition-colors"
                        >
                            {copiedSnippet === 'curl' ? (
                                <Check size={16} className="text-[#50fa7b]" />
                            ) : (
                                <Copy size={16} className="text-[#6272a4]" />
                            )}
                        </button>
                    </div>
                </div>

                {/* Python SDK */}
                <div>
                    <div className="flex items-center gap-2 mb-3">
                        <Code size={18} className="text-[#ffb86c]" />
                        <h4 className="text-lg font-bold text-[#ffb86c] uppercase tracking-wide">Python SDK</h4>
                    </div>
                    <p className="text-sm text-[#f8f8f2] mb-3">
                        Integrate MCP into your Python applications:
                    </p>
                    <div className="relative">
                        <pre className="bg-[#1a1b26] rounded p-4 text-xs font-mono text-[#f8f8f2] overflow-x-auto custom-scrollbar max-h-[400px]">
                            {pythonExample}
                        </pre>
                        <button
                            onClick={() => handleCopy(pythonExample, 'python')}
                            className="absolute top-3 right-3 p-2 bg-[#282a36] hover:bg-[#44475a] rounded transition-colors"
                        >
                            {copiedSnippet === 'python' ? (
                                <Check size={16} className="text-[#50fa7b]" />
                            ) : (
                                <Copy size={16} className="text-[#6272a4]" />
                            )}
                        </button>
                    </div>
                </div>

                {/* Endpoints */}
                <div className="bg-[#1a1b26] rounded-lg p-4">
                    <h4 className="text-sm font-bold text-[#8be9fd] uppercase tracking-wider mb-3">Available Endpoints</h4>
                    <div className="space-y-2 text-xs">
                        <div className="flex items-start gap-3">
                            <code className="bg-[#282a36] px-2 py-1 rounded text-[#50fa7b] font-mono whitespace-nowrap">POST</code>
                            <div className="flex-1">
                                <code className="text-[#f8f8f2] font-mono">/mcp/{'{mcp_id}'}/message</code>
                                <p className="text-[#6272a4] mt-1">Send JSON-RPC 2.0 messages (recommended)</p>
                            </div>
                        </div>
                        <div className="flex items-start gap-3">
                            <code className="bg-[#282a36] px-2 py-1 rounded text-[#8be9fd] font-mono whitespace-nowrap">GET</code>
                            <div className="flex-1">
                                <code className="text-[#f8f8f2] font-mono">/mcp/{'{mcp_id}'}/sse</code>
                                <p className="text-[#6272a4] mt-1">SSE stream for real-time events</p>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default MCPIntegrationGuide;
