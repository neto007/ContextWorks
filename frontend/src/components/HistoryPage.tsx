import React, { useEffect, useState } from 'react';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/Table";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button/Button";
import { Clock, CheckCircle, XCircle, Terminal, Eye, RotateCcw, X } from 'lucide-react';

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
    arguments: Record<string, any>;
}

const HistoryPage: React.FC = () => {
    const [executions, setExecutions] = useState<Execution[]>([]);
    const [selectedExecution, setSelectedExecution] = useState<Execution | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetchExecutions();
        const interval = setInterval(fetchExecutions, 5000);
        return () => clearInterval(interval);
    }, []);

    const fetchExecutions = async () => {
        try {
            const res = await fetch('/api/executions');
            const data = await res.json();
            setExecutions(data);
        } catch (err) {
            console.error('Error fetching executions:', err);
        } finally {
            setLoading(false);
        }
    };

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
        const date = new Date(dateString);
        return date.toLocaleString('pt-BR', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric',
            hour: '2-digit',
            minute: '2-digit',
        });
    };

    return (
        <div className="h-full flex flex-col">
            {/* Header */}
            <div className="mb-6">
                <h1 className="text-3xl font-black text-white tracking-widest uppercase mb-1" style={{ textShadow: "0 0 10px rgba(189,147,249,0.5)" }}>
                    Execution History
                </h1>
                <p className="text-[#6272a4] text-sm">View and analyze past tool executions</p>
            </div>

            {/* Main Content - Layout similar to Windmill */}
            <div className="flex-1 overflow-hidden flex gap-4">
                {/* Executions List - Full width when no selection */}
                <div className={`transition-all ${selectedExecution ? 'w-1/2' : 'w-full'} bg-[#0b0b11] rounded-lg overflow-hidden flex flex-col shadow-xl`}>
                    {/* Table Header Bar */}
                    <div className="bg-gradient-to-r from-[#1a1b26] to-[#282a36] px-6 py-3 flex justify-between items-center">
                        <div className="flex items-center gap-2">
                            <Clock size={16} className="text-[#bd93f9]" />
                            <h2 className="text-sm font-bold text-white uppercase tracking-wider">
                                Recent ({executions.length})
                            </h2>
                        </div>
                        <Button
                            variant="ghost"
                            size="sm"
                            onClick={fetchExecutions}
                            className="h-8 text-xs gap-1.5 hover:bg-[#282a36] text-[#6272a4] hover:text-white"
                        >
                            <RotateCcw size={12} />
                            Refresh
                        </Button>
                    </div>

                    {/* Table */}
                    <div className="flex-1 overflow-auto custom-scrollbar">
                        {loading ? (
                            <div className="flex items-center justify-center h-full text-[#6272a4]">
                                <Clock className="animate-spin mr-2" size={20} />
                                Loading executions...
                            </div>
                        ) : executions.length === 0 ? (
                            <div className="flex flex-col items-center justify-center h-full text-[#6272a4]/50">
                                <Terminal size={64} strokeWidth={1} />
                                <p className="mt-4 text-sm">No executions yet</p>
                            </div>
                        ) : (
                            <Table>
                                <TableHeader>
                                    <TableRow className="bg-[#1a1b26]/50">
                                        <TableHead className="text-[#6272a4] font-mono text-xs uppercase">Status</TableHead>
                                        <TableHead className="text-[#6272a4] font-mono text-xs uppercase">Tool</TableHead>
                                        <TableHead className="text-[#6272a4] font-mono text-xs uppercase">Target</TableHead>
                                        <TableHead className="text-[#6272a4] font-mono text-xs uppercase">Started</TableHead>
                                        <TableHead className="text-[#6272a4] font-mono text-xs uppercase text-right">Actions</TableHead>
                                    </TableRow>
                                </TableHeader>
                                <TableBody>
                                    {executions.map((exec) => (
                                        <TableRow
                                            key={exec.id}
                                            className={`cursor-pointer transition-all ${selectedExecution?.id === exec.id
                                                    ? 'bg-[#bd93f9]/10'
                                                    : 'hover:bg-[#1a1b26]/50'
                                                }`}
                                            onClick={() => setSelectedExecution(exec)}
                                        >
                                            <TableCell>{getStatusBadge(exec.status)}</TableCell>
                                            <TableCell className="font-mono text-sm text-[#8be9fd]">{exec.tool_name || 'Unknown'}</TableCell>
                                            <TableCell className="text-[#f8f8f2] text-sm truncate max-w-[200px]">{exec.target || 'N/A'}</TableCell>
                                            <TableCell className="text-[#6272a4] text-xs font-mono">{formatDate(exec.start_time)}</TableCell>
                                            <TableCell className="text-right">
                                                <Button
                                                    variant="ghost"
                                                    size="sm"
                                                    onClick={(e) => {
                                                        e.stopPropagation();
                                                        setSelectedExecution(exec);
                                                    }}
                                                    className="h-7 text-xs gap-1.5 hover:bg-[#bd93f9]/20 text-[#bd93f9]"
                                                >
                                                    <Eye size={12} />
                                                    View
                                                </Button>
                                            </TableCell>
                                        </TableRow>
                                    ))}
                                </TableBody>
                            </Table>
                        )}
                    </div>
                </div>

                {/* Details Panel - Slides in from right */}
                {selectedExecution && (
                    <div className="w-1/2 bg-[#0b0b11] rounded-lg overflow-hidden flex flex-col shadow-2xl animate-slide-in-right">
                        {/* Header */}
                        <div className="bg-gradient-to-r from-[#bd93f9]/20 to-[#8be9fd]/20 px-6 py-4 flex justify-between items-start">
                            <div className="flex-1">
                                <div className="flex items-center gap-2 mb-2">
                                    {getStatusBadge(selectedExecution.status)}
                                    <span className="text-xs font-mono text-[#6272a4]">ID: {selectedExecution.id.slice(0, 8)}</span>
                                </div>
                                <h3 className="text-xl font-bold text-white">{selectedExecution.tool_name}</h3>
                            </div>
                            <button
                                onClick={() => setSelectedExecution(null)}
                                className="text-[#6272a4] hover:text-white transition-colors p-1 hover:bg-white/10 rounded"
                            >
                                <X size={18} />
                            </button>
                        </div>

                        {/* Content */}
                        <div className="flex-1 overflow-auto custom-scrollbar p-6 space-y-6">
                            {/* Metadata */}
                            <div className="space-y-4">
                                <div>
                                    <label className="text-xs text-[#6272a4] uppercase tracking-wider block mb-1.5 font-mono">Target</label>
                                    <div className="bg-[#1a1b26] px-4 py-2.5 rounded text-sm text-white font-mono">
                                        {selectedExecution.target || 'N/A'}
                                    </div>
                                </div>
                                <div className="grid grid-cols-2 gap-3">
                                    <div>
                                        <label className="text-xs text-[#6272a4] uppercase tracking-wider block mb-1.5 font-mono">Started</label>
                                        <div className="text-xs text-[#f8f8f2]">{formatDate(selectedExecution.start_time)}</div>
                                    </div>
                                    {selectedExecution.end_time && (
                                        <div>
                                            <label className="text-xs text-[#6272a4] uppercase tracking-wider block mb-1.5 font-mono">Ended</label>
                                            <div className="text-xs text-[#f8f8f2]">{formatDate(selectedExecution.end_time)}</div>
                                        </div>
                                    )}
                                </div>
                            </div>

                            {/* Logs */}
                            <div>
                                <label className="text-xs text-[#6272a4] uppercase tracking-wider block mb-2 font-mono">Logs (STDERR)</label>
                                <div className="bg-[#050101] rounded p-4 max-h-[200px] overflow-auto custom-scrollbar">
                                    <pre className="text-xs font-mono text-[#ffb86c] whitespace-pre-wrap leading-relaxed">
                                        {selectedExecution.logs || 'No logs available'}
                                    </pre>
                                </div>
                            </div>

                            {/* Result */}
                            <div>
                                <label className="text-xs text-[#6272a4] uppercase tracking-wider block mb-2 font-mono">Result (STDOUT)</label>
                                <div className="bg-[#050101] rounded p-4 max-h-[300px] overflow-auto custom-scrollbar">
                                    <pre className="text-xs font-mono text-[#50fa7b] whitespace-pre-wrap leading-relaxed">
                                        {selectedExecution.result || 'No result available'}
                                    </pre>
                                </div>
                            </div>
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
};

export default HistoryPage;
