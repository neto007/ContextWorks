import React, { useState, useEffect } from 'react';
import { Clock, Terminal, RotateCcw, Eye, CheckCircle, XCircle } from 'lucide-react';
import { Button } from "@/components/ui/Button/Button";
import { Badge } from "@/components/ui/Badge";
import ExecutionLogs from './ExecutionLogs';

interface Execution {
    id: string;
    tool_name: string;
    tool_path: string;
    target: string;
    status: 'running' | 'success' | 'failed';
    start_time: string;
    end_time?: string;
    logs: string;
    result: string;
}

interface ExecutionHistoryProps {
    toolPath: string;
    onHistoryRestore?: (execution: Execution) => void;
}

const ExecutionHistory: React.FC<ExecutionHistoryProps> = ({ toolPath, onHistoryRestore }) => {
    const [executions, setExecutions] = useState<Execution[]>([]);
    const [loading, setLoading] = useState(false);
    const [selectedId, setSelectedId] = useState<string | null>(null);

    const fetchHistory = async () => {
        setLoading(true);
        try {
            const res = await fetch('/api/executions');
            const all: Execution[] = await res.json();
            setExecutions(all.filter(e => e.tool_path === toolPath));
        } catch (err) {
            console.error('Error fetching history:', err);
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchHistory();
    }, [toolPath]);

    const getStatusBadge = (status: string) => {
        switch (status) {
            case 'success':
                return <Badge variant="success" className="flex items-center gap-1 bg-[#50fa7b]/20 text-[#50fa7b] border-[#50fa7b]/40"><CheckCircle size={12} /> Success</Badge>;
            case 'failed':
                return <Badge variant="destructive" className="flex items-center gap-1 bg-[#ff5555]/20 text-[#ff5555] border-[#ff5555]/40"><XCircle size={12} /> Failed</Badge>;
            case 'running':
                return <Badge variant="secondary" className="flex items-center gap-1 bg-[#bd93f9]/20 text-[#bd93f9] border-[#bd93f9]/40"><RotateCcw size={12} className="animate-spin" /> Running</Badge>;
            default:
                return <Badge variant="outline">{status}</Badge>;
        }
    };

    const formatDate = (dateString: string) => {
        return new Date(dateString).toLocaleString('pt-BR', {
            day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit',
        });
    };

    const selectedExecution = executions.find(e => e.id === selectedId);

    return (
        <div className="h-full flex gap-4">
            <div className={`transition-all ${selectedId ? 'w-1/2' : 'w-full'} bg-[#0b0b11] rounded-lg overflow-hidden flex flex-col shadow-xl`}>
                <div className="bg-gradient-to-r from-[#1a1b26] to-[#282a36] px-6 py-3 flex justify-between items-center">
                    <div className="flex items-center gap-2">
                        <Clock size={16} className="text-[#f1fa8c]" />
                        <h3 className="text-sm font-bold text-white uppercase tracking-wider">
                            History ({executions.length})
                        </h3>
                    </div>
                    <Button variant="ghost" size="sm" onClick={fetchHistory} className="h-8 text-xs gap-1.5 text-[#6272a4] hover:text-white">
                        <RotateCcw size={12} /> Refresh
                    </Button>
                </div>

                <div className="flex-1 overflow-auto custom-scrollbar">
                    {loading ? (
                        <div className="flex items-center justify-center h-full text-[#6272a4]"><Clock className="animate-spin mr-2" size={20} /></div>
                    ) : executions.length === 0 ? (
                        <div className="flex flex-col items-center justify-center h-full text-[#6272a4]/50">
                            <Terminal size={64} strokeWidth={1} />
                            <p className="mt-4 text-sm">No executions yet</p>
                        </div>
                    ) : (
                        <div className="divide-y divide-[#1a1b26]">
                            {executions.map((exec) => (
                                <div
                                    key={exec.id}
                                    onClick={() => setSelectedId(exec.id)}
                                    className={`p-4 cursor-pointer transition-all ${selectedId === exec.id ? 'bg-[#bd93f9]/10' : 'hover:bg-[#1a1b26]/50'}`}
                                >
                                    <div className="flex justify-between items-start mb-2">
                                        {getStatusBadge(exec.status)}
                                        <span className="text-[10px] text-[#6272a4] font-mono">{formatDate(exec.start_time)}</span>
                                    </div>
                                    <div className="text-sm text-[#f8f8f2] font-mono truncate">
                                        Target: <span className="text-[#8be9fd]">{exec.target}</span>
                                    </div>
                                </div>
                            ))}
                        </div>
                    )}
                </div>
            </div>

            {selectedExecution && (
                <div className="w-1/2 bg-[#0b0b11] rounded-lg overflow-hidden flex flex-col shadow-2xl animate-slide-in-right border border-[#1a1b26]">
                    <div className="bg-gradient-to-r from-[#f1fa8c]/20 to-[#ffb86c]/20 px-6 py-4 flex justify-between items-start">
                        <div>
                            <div className="flex items-center gap-2 mb-1">{getStatusBadge(selectedExecution.status)}</div>
                            <p className="text-xs font-mono text-[#6272a4]">ID: {selectedExecution.id.slice(0, 8)}</p>
                        </div>
                        <div className="flex gap-2">
                            {selectedExecution.status === 'running' && onHistoryRestore && (
                                <Button size="sm" onClick={() => onHistoryRestore(selectedExecution)} className="bg-[#bd93f9] hover:bg-[#ff79c6] text-[#282a36] font-bold text-xs">
                                    Resume
                                </Button>
                            )}
                            <button onClick={() => setSelectedId(null)} className="text-[#6272a4] hover:text-white transition-colors p-1 hover:bg-white/10 rounded">
                                <Eye size={18} />
                            </button>
                        </div>
                    </div>

                    <div className="flex-1 overflow-auto custom-scrollbar p-6 space-y-6">
                        <div>
                            <label className="text-xs text-[#6272a4] uppercase tracking-wider block mb-1.5 font-mono">Target</label>
                            <div className="bg-[#1a1b26] px-4 py-2.5 rounded text-sm text-white font-mono">{selectedExecution.target || 'N/A'}</div>
                        </div>

                        <div>
                            <label className="text-xs text-[#6272a4] uppercase tracking-wider block mb-2 font-mono">Logs (STDERR)</label>
                            <div className="bg-[#050101] rounded h-[200px] border border-[#1a1b26]">
                                <ExecutionLogs logs={selectedExecution.logs} autoScroll={false} />
                            </div>
                        </div>

                        <div>
                            <label className="text-xs text-[#6272a4] uppercase tracking-wider block mb-2 font-mono">Result (STDOUT)</label>
                            <div className="bg-[#050101] rounded border border-[#1a1b26] p-4 max-h-[300px] overflow-auto">
                                <pre className="text-xs font-mono text-[#50fa7b] whitespace-pre-wrap">{selectedExecution.result || 'No result available'}</pre>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default ExecutionHistory;
