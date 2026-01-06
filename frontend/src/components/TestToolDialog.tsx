import React, { useState } from 'react';
import { X, Play, XCircle } from 'lucide-react';
import { Button } from "@/components/ui/Button/Button";
import { type Argument } from './ArgumentsBuilder';

interface TestToolDialogProps {
    scriptCode: string;
    arguments: Argument[];
    toolName: string;
    toolId?: string;
    image?: string;
    onClose: () => void;
}

const TestToolDialog: React.FC<TestToolDialogProps> = ({ scriptCode, arguments: toolArguments, toolName, toolId, image, onClose }) => {
    const [testArgs, setTestArgs] = useState<Record<string, any>>({});
    const [testing, setTesting] = useState(false);
    const [testResult, setTestResult] = useState<any>(null);
    const [error, setError] = useState<string | null>(null);

    const handleTest = async () => {
        setTesting(true);
        setTestResult(null);
        setError(null);

        try {
            const res = await fetch('/api/tools/test', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    script_code: scriptCode,
                    arguments: testArgs,
                    tool_name: toolName,
                    tool_id: toolId || toolName,
                    image: image
                })
            });

            if (!res.ok) {
                const text = await res.text();
                throw new Error(`Server error: ${res.status} ${text}`);
            }

            if (!res.body) throw new Error("No response body");

            const reader = res.body.getReader();
            const decoder = new TextDecoder();

            let fullLogs = "";

            while (true) {
                const { done, value } = await reader.read();
                if (done) break;

                const chunk = decoder.decode(value, { stream: true });
                const lines = chunk.split('\n');

                for (const line of lines) {
                    if (!line.trim()) continue;
                    try {
                        const msg = JSON.parse(line);

                        // Handle different message types from stream
                        // Backend Protocol (v2): type=[start, stderr, stdout, exit], data=...
                        if (msg.type === 'start') {
                            fullLogs += `\n🔄 Starting Job ${msg.id}...\n`;
                        } else if (msg.type === 'stderr') {
                            // Kubernetes logs come here (including app logs)
                            fullLogs += msg.data;
                        } else if (msg.type === 'stdout') {
                            // Final Result
                            fullLogs += `\n--- RESULT ---\n${typeof msg.data === 'object' ? JSON.stringify(msg.data, null, 2) : msg.data}\n`;
                        } else if (msg.type === 'exit') {
                            if (msg.code === 0) {
                                fullLogs += `\n✅ Execution completed (Exit Code: 0)\n`;
                            } else {
                                fullLogs += `\n❌ Execution failed (Exit Code: ${msg.code})\n`;
                            }
                        }
                        // Legacy/Alternative Protocol
                        else if (msg.status === 'log') {
                            fullLogs += msg.content;
                        } else if (msg.status === 'error') {
                            fullLogs += `\n❌ Error: ${msg.message}\n`;
                            setError(msg.message);
                        } else if (msg.status === 'running') {
                            fullLogs += `\n🔄 ${msg.step}\n`;
                        } else if (msg.status === 'completed') {
                            fullLogs += `\n✅ Execution completed\n`;
                        }

                        // Update UI with latest logs
                        // We use a temporary object structure to mimic the result expectation
                        setTestResult({
                            logs: fullLogs,
                            result: null // Real result parsing would be here if we returned it separately
                        });

                    } catch (e) {
                        console.warn("Failed to parse log line:", line);
                    }
                }
            }

        } catch (err: any) {
            console.error('Test error:', err);
            const message = err instanceof Error ? err.message : String(err);
            setError(message);
        } finally {
            setTesting(false);
        }
    };

    const handleArgChange = (argName: string, value: any) => {
        setTestArgs(prev => ({ ...prev, [argName]: value }));
    };

    return (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-[60] p-4">
            <div className="bg-[#0b0b11] rounded-lg shadow-2xl border border-[#1a1b26] w-full max-w-3xl max-h-[80vh] flex flex-col">
                {/* Header */}
                <div className="bg-gradient-to-r from-[#1a1b26] to-[#282a36] px-6 py-4 flex justify-between items-center rounded-t-lg flex-shrink-0">
                    <div>
                        <h3 className="text-xl font-bold text-white flex items-center gap-2">
                            🧪 Test Tool
                        </h3>
                        <p className="text-sm text-[#6272a4]">Run script with test arguments</p>
                    </div>
                    <Button variant="ghost" size="sm" onClick={onClose}>
                        <X size={20} />
                    </Button>
                </div>

                {/* Content */}
                <div className="flex-1 overflow-auto p-6 custom-scrollbar">
                    {/* Arguments Input */}
                    {toolArguments.length > 0 ? (
                        <div className="mb-6">
                            <h4 className="text-sm font-mono text-[#8be9fd] uppercase mb-3">
                                Test Arguments
                            </h4>
                            <div className="space-y-3">
                                {toolArguments.map((arg) => (
                                    <div key={arg.name}>
                                        <label className="block text-sm font-mono text-[#6272a4] mb-2">
                                            {arg.name}
                                            {arg.required && <span className="text-[#ff5555]"> *</span>}
                                            <span className="text-xs ml-2">({arg.type})</span>
                                        </label>
                                        {arg.type === 'bool' ? (
                                            <select
                                                className="w-full bg-[#1a1b26] border border-[#282a36] rounded px-4 py-2 text-white font-mono focus:outline-none focus:border-[#8be9fd]"
                                                value={testArgs[arg.name] ?? (arg.default || 'false')}
                                                onChange={(e) => handleArgChange(arg.name, e.target.value === 'true')}
                                            >
                                                <option value="false">false</option>
                                                <option value="true">true</option>
                                            </select>
                                        ) : (
                                            <input
                                                type={arg.type === 'int' ? 'number' : 'text'}
                                                className="w-full bg-[#1a1b26] border border-[#282a36] rounded px-4 py-2 text-white font-mono focus:outline-none focus:border-[#8be9fd]"
                                                placeholder={arg.description}
                                                value={testArgs[arg.name] ?? (arg.default || '')}
                                                onChange={(e) => handleArgChange(arg.name, arg.type === 'int' ? parseInt(e.target.value) : e.target.value)}
                                            />
                                        )}
                                    </div>
                                ))}
                            </div>
                        </div>
                    ) : (
                        <div className="mb-6 p-4 bg-[#1a1b26] rounded border border-[#282a36]">
                            <p className="text-[#6272a4] text-sm font-mono">
                                No arguments defined for this tool
                            </p>
                        </div>
                    )}

                    {/* Execution Logs & Result */}
                    <div className="flex flex-col h-[400px] bg-[#0b0b11] rounded-lg border border-[#282a36] overflow-hidden">
                        <div className="flex items-center justify-between px-4 py-2 bg-[#1a1b26] border-b border-[#282a36]">
                            <div className="flex items-center gap-2">
                                <span className="font-mono text-xs text-[#6272a4] uppercase font-bold">Terminal Output</span>
                                {testing && <span className="flex h-2 w-2 rounded-full bg-[#50fa7b] animate-pulse" />}
                            </div>
                            <div className="flex items-center gap-1.5 opacity-50">
                                <div className="w-2.5 h-2.5 rounded-full bg-[#ff5555]"></div>
                                <div className="w-2.5 h-2.5 rounded-full bg-[#f1fa8c]"></div>
                                <div className="w-2.5 h-2.5 rounded-full bg-[#50fa7b]"></div>
                            </div>
                        </div>

                        <div className="flex-1 p-4 overflow-auto font-mono text-xs custom-scrollbar space-y-1">
                            {(!testResult?.logs && !error && !testing) ? (
                                <div className="h-full flex flex-col items-center justify-center text-[#6272a4]/50 gap-2">
                                    <Play size={32} />
                                    <p>Ready to execute</p>
                                </div>
                            ) : (
                                <>
                                    {testResult?.logs?.split('\n').map((line: string, i: number) => {
                                        if (!line) return null;

                                        // System messages
                                        if (line.includes('🔄'))
                                            return <div key={i} className="text-[#8be9fd] font-bold pb-1 border-b border-[#8be9fd]/10 mb-1">{line}</div>;
                                        if (line.includes('✅'))
                                            return <div key={i} className="text-[#50fa7b] font-bold mt-2 pt-2 border-t border-[#50fa7b]/20">{line}</div>;
                                        if (line.includes('❌'))
                                            return <div key={i} className="text-[#ff5555] font-bold">{line}</div>;

                                        // Result separator
                                        if (line.includes('--- RESULT ---'))
                                            return <div key={i} className="text-[#f1fa8c] font-bold mt-4 mb-2">--- RESULT ---</div>;

                                        // Standard Output
                                        return (
                                            <div key={i} className="text-[#f8f8f2] pl-2 border-l-2 border-[#6272a4]/20 hover:border-[#6272a4]/50 transition-colors whitespace-pre-wrap break-all">
                                                {line}
                                            </div>
                                        );
                                    })}

                                    {error && (
                                        <div className="mt-4 p-3 bg-[#ff5555]/10 border border-[#ff5555]/30 rounded text-[#ff5555]">
                                            <div className="font-bold flex items-center gap-2 mb-1">
                                                <XCircle size={14} />
                                                Execution Error
                                            </div>
                                            <div className="whitespace-pre-wrap opacity-90">{error}</div>
                                        </div>
                                    )}

                                    {testing && (
                                        <div className="text-[#6272a4] animate-pulse pl-2 font-bold">_</div>
                                    )}
                                </>
                            )}
                        </div>
                    </div>
                </div>

                {/* Footer */}
                <div className="px-6 py-4 bg-[#1a1b26] rounded-b-lg flex justify-end gap-3 flex-shrink-0">
                    <Button
                        variant="outline"
                        onClick={onClose}
                        className="border-[#6272a4]/40"
                    >
                        Close
                    </Button>
                    <Button
                        onClick={handleTest}
                        disabled={testing}
                        className="bg-[#8be9fd] hover:bg-[#8be9fd]/90 text-[#050101] font-bold gap-2"
                    >
                        <Play size={16} />
                        {testing ? 'Running...' : 'Run Test'}
                    </Button>
                </div>
            </div>
        </div>
    );
};

export default TestToolDialog;
