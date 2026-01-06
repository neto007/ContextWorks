import React, { useState, useEffect } from 'react';
import { Server, Plus, Trash2, RefreshCw, Key, Copy, Check, Users, Edit, Eye } from 'lucide-react';
import { Button } from "@/components/ui/Button/Button";
import { Badge } from "@/components/ui/Badge";
import MCPFormDialog from './MCPFormDialog';
import RegenerateKeyDialog from './RegenerateKeyDialog';
import MCPIntegrationGuide from './MCPIntegrationGuide';

interface MCP {
    id: string;
    name: string;
    description: string;
    tool_ids: string[];
    created_at: string;
    updated_at: string;
    status: 'active' | 'disabled';
    active_connections: number;
    has_logo?: boolean;
}

const MCPManager: React.FC = () => {
    const [mcps, setMcps] = useState<MCP[]>([]);
    const [loading, setLoading] = useState(true);
    const [showCreateDialog, setShowCreateDialog] = useState(false);
    const [selectedMCP, setSelectedMCP] = useState<MCP | null>(null);
    const [selectedMcpForRegen, setSelectedMcpForRegen] = useState<{ id: string; name: string } | null>(null);
    const [showGuide, setShowGuide] = useState(false);
    const [copiedKey, setCopiedKey] = useState<string | null>(null);

    const fetchMCPs = async (silent = false) => {
        if (!silent) setLoading(true);
        try {
            const res = await fetch(`/api/mcps?t=${Date.now()}`);

            if (!res.ok) {
                throw new Error(`HTTP ${res.status}: ${res.statusText}`);
            }

            const data = await res.json();
            setMcps(data);
        } catch (err) {
            // Only alert on initial load failure to avoid spamming
            if (!silent) {
                // In enterprise apps, we might want to log this to a monitoring service instead of console
            }
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        fetchMCPs();
        const interval = setInterval(() => fetchMCPs(true), 10000); // Refresh every 10s silently
        return () => clearInterval(interval);
    }, []);

    const handleDelete = async (mcpId: string) => {
        if (!confirm('Are you sure you want to delete this MCP server?')) return;

        try {
            const res = await fetch(`/api/mcps/${mcpId}`, { method: 'DELETE' });
            if (res.ok) {
                fetchMCPs();
            } else {
                alert('Failed to delete MCP');
            }
        } catch (err) {
            console.error('Error deleting MCP:', err);
            alert('Failed to delete MCP');
        }
    };

    const handleEdit = (mcp: MCP) => {
        setSelectedMCP(mcp);
        setShowCreateDialog(true);
    };

    const handleRegenerateKey = (mcpId: string, mcpName: string) => {
        setSelectedMcpForRegen({ id: mcpId, name: mcpName });
    };

    const handleCopy = (text: string, mcpId: string) => {
        navigator.clipboard.writeText(text);
        setCopiedKey(mcpId);
        setTimeout(() => setCopiedKey(null), 2000);
    };

    const getStatusBadge = (status: string) => {
        if (status === 'active') {
            return <Badge variant="success" className="bg-[#50fa7b]/20 text-[#50fa7b] border-[#50fa7b]/40">Active</Badge>;
        }
        return <Badge variant="secondary" className="bg-[#6272a4]/20 text-[#6272a4] border-[#6272a4]/40">Disabled</Badge>;
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

    if (showGuide) {
        return <MCPIntegrationGuide onBack={() => setShowGuide(false)} />;
    }

    return (
        <div className="h-full flex flex-col p-6 space-y-6">
            {/* Header */}
            <div className="flex justify-between items-center">
                <div>
                    <h2 className="text-2xl font-bold text-white flex items-center gap-2">
                        <Server className="text-[#8be9fd]" />
                        MCP SERVERS
                    </h2>
                    <p className="text-[#6272a4] text-sm mt-1">
                        Expose security tools as Model Context Protocol servers
                    </p>
                </div>
                <div className="flex gap-3">
                    <Button
                        variant="ghost"
                        onClick={() => setShowGuide(true)}
                        className="text-[#6272a4] hover:text-white"
                    >
                        <Eye size={16} className="mr-2" />
                        SHOW INTEGRATION GUIDE
                    </Button>
                    <Button
                        onClick={() => setShowCreateDialog(true)}
                        className="bg-[#8be9fd] hover:bg-[#8be9fd] text-[#050101] font-black uppercase tracking-wider border-b-4 border-[#569cd6] hover:border-[#569cd6] active:border-b-0 active:translate-y-1 transition-all gap-2"
                    >
                        <Plus size={18} />
                        New MCP Server
                    </Button>
                </div>
            </div>

            {/* MCP List */}
            <div className="flex-1 overflow-auto custom-scrollbar">
                {loading ? (
                    <div className="flex items-center justify-center h-full text-[#6272a4]">
                        <RefreshCw className="animate-spin mr-2" size={20} />
                        Loading MCPs...
                    </div>
                ) : mcps.length === 0 ? (
                    <div className="flex flex-col items-center justify-center h-full text-[#6272a4]/50">
                        <Server size={64} strokeWidth={1} />
                        <p className="mt-4 text-lg font-mono">No MCP servers created yet</p>
                        <p className="text-sm mt-2">Create your first MCP to expose tools to LLMs</p>
                    </div>
                ) : (
                    <div className="grid grid-cols-[repeat(auto-fill,minmax(450px,1fr))] gap-4">
                        {mcps.map((mcp) => (
                            <div
                                key={mcp.id}
                                className="bg-[#0b0b11] rounded-lg overflow-hidden shadow-xl hover:shadow-2xl transition-all border border-[#1a1b26]"
                            >
                                {/* Card Header */}
                                <div className="bg-gradient-to-r from-[#1a1b26] to-[#282a36] px-6 py-4 flex justify-between items-start">
                                    <div className="flex-1 flex items-start gap-4">
                                        {mcp.has_logo ? (
                                            <div className="w-16 h-16 flex items-center justify-center shrink-0">
                                                <img
                                                    src={`/api/mcps/${mcp.id}/logo?t=${Date.now()}`}
                                                    alt={mcp.name}
                                                    className="w-full h-full object-contain"
                                                />
                                            </div>
                                        ) : (
                                            <div className="w-16 h-16 flex items-center justify-center shrink-0 bg-[#0b0b11] rounded-lg border border-[#1a1b26]">
                                                <Server size={32} className="text-[#8be9fd]" />
                                            </div>
                                        )}
                                        <div className="flex-1 min-w-0">
                                            <div className="flex items-center gap-3 mb-1">
                                                <h3 className="text-xl font-bold text-white truncate">{mcp.name}</h3>
                                                {getStatusBadge(mcp.status)}
                                            </div>
                                            <p className="text-sm text-[#6272a4] line-clamp-2">{mcp.description}</p>
                                        </div>
                                    </div>
                                </div>

                                {/* Card Body */}
                                <div className="p-6 space-y-4">
                                    {/* Stats */}
                                    <div className="grid grid-cols-2 gap-4">
                                        <div className="bg-[#1a1b26] rounded p-3">
                                            <div className="text-xs text-[#6272a4] uppercase tracking-wider mb-1 font-mono">Tools</div>
                                            <div className="text-2xl font-bold text-[#8be9fd]">{mcp.tool_ids.length}</div>
                                        </div>
                                        <div className="bg-[#1a1b26] rounded p-3">
                                            <div className="text-xs text-[#6272a4] uppercase tracking-wider mb-1 font-mono flex items-center gap-1">
                                                <Users size={12} />
                                                Connections
                                            </div>
                                            <div className="text-2xl font-bold text-[#50fa7b]">{mcp.active_connections || 0}</div>
                                        </div>
                                    </div>

                                    {/* MCP ID */}
                                    <div>
                                        <label className="text-xs text-[#6272a4] uppercase tracking-wider block mb-1.5 font-mono">MCP ID</label>
                                        <div className="flex gap-2">
                                            <div className="flex-1 bg-[#1a1b26] px-3 py-2 rounded text-xs text-white font-mono truncate">
                                                {mcp.id}
                                            </div>
                                            <Button
                                                variant="ghost"
                                                size="sm"
                                                onClick={() => handleCopy(mcp.id, mcp.id)}
                                                className="h-auto px-3"
                                            >
                                                {copiedKey === mcp.id ? <Check size={14} className="text-[#50fa7b]" /> : <Copy size={14} />}
                                            </Button>
                                        </div>
                                    </div>

                                    {/* MCP URLs */}
                                    <div className="space-y-2">
                                        <div>
                                            <label className="text-xs text-[#6272a4] uppercase tracking-wider block mb-1.5 font-mono">SSE Endpoint</label>
                                            <div className="flex gap-2">
                                                <div className="flex-1 bg-[#1a1b26] px-3 py-2 rounded text-xs text-[#8be9fd] font-mono truncate">
                                                    {`${window.location.protocol}//${window.location.hostname}:8000/mcp/${mcp.id}/sse`}
                                                </div>
                                                <Button
                                                    variant="ghost"
                                                    size="sm"
                                                    onClick={() => handleCopy(`${window.location.protocol}//${window.location.hostname}:8000/mcp/${mcp.id}/sse`, `sse-${mcp.id}`)}
                                                    className="h-auto px-3"
                                                >
                                                    {copiedKey === `sse-${mcp.id}` ? <Check size={14} className="text-[#50fa7b]" /> : <Copy size={14} />}
                                                </Button>
                                            </div>
                                        </div>
                                        <div>
                                            <label className="text-xs text-[#6272a4] uppercase tracking-wider block mb-1.5 font-mono">Message Endpoint</label>
                                            <div className="flex gap-2">
                                                <div className="flex-1 bg-[#1a1b26] px-3 py-2 rounded text-xs text-[#8be9fd] font-mono truncate">
                                                    {`${window.location.protocol}//${window.location.hostname}:8000/mcp/${mcp.id}/message`}
                                                </div>
                                                <Button
                                                    variant="ghost"
                                                    size="sm"
                                                    onClick={() => handleCopy(`${window.location.protocol}//${window.location.hostname}:8000/mcp/${mcp.id}/message`, `msg-${mcp.id}`)}
                                                    className="h-auto px-3"
                                                >
                                                    {copiedKey === `msg-${mcp.id}` ? <Check size={14} className="text-[#50fa7b]" /> : <Copy size={14} />}
                                                </Button>
                                            </div>
                                        </div>
                                    </div>

                                    {/* Created */}
                                    <div>
                                        <label className="text-xs text-[#6272a4] uppercase tracking-wider block mb-1 font-mono">Created</label>
                                        <div className="text-sm text-white font-mono">{formatDate(mcp.created_at)}</div>
                                    </div>

                                    {/* Actions */}
                                    <div className="flex gap-2 pt-4 border-t border-[#1a1b26]">
                                        <Button
                                            className="flex-1 gap-2 text-[#bd93f9] border-[#bd93f9]/40 hover:bg-[#bd93f9]/10"
                                            variant="outline"
                                            size="sm"
                                            onClick={() => handleEdit(mcp)}
                                        >
                                            <Edit size={14} />
                                            EDIT
                                        </Button>
                                        <Button
                                            className="flex-1 gap-2 text-[#8be9fd] border-[#8be9fd]/40 hover:bg-[#8be9fd]/10"
                                            variant="outline"
                                            size="sm"
                                            onClick={() => handleRegenerateKey(mcp.id, mcp.name)}
                                        >
                                            <Key size={14} />
                                            REGENERATE
                                        </Button>
                                        <Button
                                            className="gap-2 text-[#ff5555] border-[#ff5555]/40 hover:bg-[#ff5555]/10"
                                            variant="outline"
                                            size="sm"
                                            onClick={() => handleDelete(mcp.id)}
                                        >
                                            <Trash2 size={14} />
                                            DELETE
                                        </Button>
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </div>

            {/* Dialogs */}
            {showCreateDialog && (
                <MCPFormDialog
                    mcp={selectedMCP}
                    onClose={() => {
                        setShowCreateDialog(false);
                        setSelectedMCP(null);
                    }}
                    onSuccess={() => {
                        setShowCreateDialog(false);
                        setSelectedMCP(null);
                        fetchMCPs();
                    }}
                />
            )}

            {/* Regenerate Key Dialog */}
            {selectedMcpForRegen && (
                <RegenerateKeyDialog
                    mcpId={selectedMcpForRegen.id}
                    mcpName={selectedMcpForRegen.name}
                    onClose={() => setSelectedMcpForRegen(null)}
                    onSuccess={() => {
                        // Keep dialog open for user to copy key, refresh happens in background or next open
                        fetchMCPs();
                    }}
                />
            )}
        </div>
    );
};

export default MCPManager;
