import React, { useState, useEffect } from 'react';
import { X, Loader2, Check, Plus, Trash2, Filter } from 'lucide-react';
import { Button } from "@/components/ui/Button/Button";
import LogoUploader from './LogoUploader';

interface MCPFormDialogProps {
    mcp?: any;
    onClose: () => void;
    onSuccess: () => void;
}

interface Tool {
    id: string;
    name: string;
    description: string;
    category: string;
}

const MCPFormDialog: React.FC<MCPFormDialogProps> = ({ mcp, onClose, onSuccess }) => {
    const [name, setName] = useState(mcp?.name || '');
    const [description, setDescription] = useState(mcp?.description || '');
    const [selectedToolIds, setSelectedToolIds] = useState<string[]>(mcp?.tool_ids || []);
    const [allTools, setAllTools] = useState<Tool[]>([]);
    const [loading, setLoading] = useState(false);
    const [loadingTools, setLoadingTools] = useState(true);
    const [newApiKey, setNewApiKey] = useState<string | null>(null);
    const [logoSVG, setLogoSVG] = useState<string | null>(null);

    // Initialize env vars from mcp object
    // Handle migration from old dict format to new list format transparently
    const [envVars, setEnvVars] = useState<{ name: string; description: string; default_value: string; required: boolean; tool_ids: string[] }[]>(() => {
        if (!mcp?.env_vars) return [];
        if (Array.isArray(mcp.env_vars)) {
            // Already new format (ensure tool_ids exists)
            return mcp.env_vars.map((e: any) => ({ ...e, tool_ids: e.tool_ids || [] }));
        } else {
            // Legacy dict format - migrate
            return Object.entries(mcp.env_vars).map(([key, value]) => ({
                name: key,
                description: '',
                default_value: String(value),
                required: false,
                tool_ids: []
            }));
        }
    });

    // Temp state for scope modal
    const [scopeModalIndex, setScopeModalIndex] = useState<number | null>(null);

    useEffect(() => {
        if (mcp?.id && mcp?.has_logo) {
            // Fetch existing logo
            fetch(`/api/mcps/${mcp.id}/logo`)
                .then(async (res) => {
                    if (res.ok) {
                        const text = await res.text();
                        setLogoSVG(text);
                    }
                })
                .catch(console.error);
        }
    }, [mcp]);

    useEffect(() => {
        fetchTools();
    }, []);

    const fetchTools = async () => {
        setLoadingTools(true);
        try {
            const res = await fetch('/api/tools');
            const data = await res.json();

            // Flatten tools from categories
            const tools: Tool[] = [];
            Object.entries(data).forEach(([category, categoryTools]: [string, any]) => {
                categoryTools.forEach((tool: any) => {
                    tools.push({
                        id: tool.id,
                        name: tool.name,
                        description: tool.description,
                        category: category
                    });
                });
            });

            setAllTools(tools);
        } catch (err) {
            console.error('Error fetching tools:', err);
        } finally {
            setLoadingTools(false);
        }
    };

    const handleToggleTool = (toolId: string) => {
        if (selectedToolIds.includes(toolId)) {
            setSelectedToolIds(selectedToolIds.filter(id => id !== toolId));
        } else {
            setSelectedToolIds([...selectedToolIds, toolId]);
        }
    };

    const handleSelectCategory = (category: string) => {
        const categoryToolIds = allTools
            .filter(tool => tool.category === category)
            .map(tool => tool.id);

        const allSelected = categoryToolIds.every(id => selectedToolIds.includes(id));

        if (allSelected) {
            // Deselect all from category
            setSelectedToolIds(selectedToolIds.filter(id => !categoryToolIds.includes(id)));
        } else {
            // Select all from category
            const newSelection = [...new Set([...selectedToolIds, ...categoryToolIds])];
            setSelectedToolIds(newSelection);
        }
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();

        if (!name.trim() || selectedToolIds.length === 0) {
            alert('Please fill in all fields and select at least one tool');
            return;
        }

        setLoading(true);

        try {
            const method = mcp ? 'PUT' : 'POST';
            const endpoint = mcp ? `/api/mcps/${mcp.id}` : '/api/mcps';

            const res = await fetch(endpoint, {
                method,
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    name: name.trim(),
                    description: description.trim(),
                    tool_ids: selectedToolIds,
                    // Send full rich list of env vars
                    env_vars: envVars.filter(e => e.name.trim() !== '')
                })
            });

            if (res.ok) {
                const data = await res.json();

                // If creating new MCP, show API key
                if (!mcp && data.api_key) {
                    setNewApiKey(data.api_key);
                } else {
                    onSuccess();
                }

                // Upload logo if provided
                if (logoSVG) {
                    try {
                        const mcpId = mcp ? mcp.id : data.id;
                        await fetch(`/api/mcps/${mcpId}/logo`, {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({ svg_code: logoSVG })
                        });
                    } catch (err) {
                        console.error('Failed to upload logo:', err);
                    }
                }
            } else {
                const error = await res.json();
                alert(`Failed to ${mcp ? 'update' : 'create'} MCP: ${error.detail}`);
            }
        } catch (err) {
            console.error('Error submitting MCP:', err);
            alert(`Failed to ${mcp ? 'update' : 'create'} MCP`);
        } finally {
            setLoading(false);
        }
    };

    const handleCopyKey = () => {
        if (newApiKey) {
            navigator.clipboard.writeText(newApiKey);
            alert('API key copied to clipboard!');
        }
    };

    // Group tools by category
    const toolsByCategory = allTools.reduce((acc, tool) => {
        if (!acc[tool.category]) {
            acc[tool.category] = [];
        }
        acc[tool.category].push(tool);
        return acc;
    }, {} as Record<string, Tool[]>);

    // Filter tools actually selected in the MCP for the scope selector
    const enabledTools = allTools.filter(t => selectedToolIds.includes(t.id));

    // If showing API key after creation
    if (newApiKey) {
        return (
            <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4">
                <div className="bg-[#0b0b11] rounded-lg max-w-2xl w-full shadow-2xl border border-[#1a1b26] max-h-[90vh] overflow-hidden">
                    <div className="bg-gradient-to-r from-[#50fa7b]/20 to-[#8be9fd]/20 px-6 py-4 flex justify-between items-center border-b border-[#1a1b26]">
                        <h3 className="text-xl font-bold text-white uppercase tracking-wider">✅ MCP Created Successfully!</h3>
                    </div>

                    <div className="p-6 space-y-4">
                        <div className="bg-[#ff5555]/10 border border-[#ff5555]/40 rounded p-4">
                            <p className="text-[#ff5555] font-bold mb-2">⚠️ IMPORTANT: Save your API key now!</p>
                            <p className="text-sm text-[#f8f8f2]">This is the only time you'll see this key. Store it securely.</p>
                        </div>

                        <div>
                            <label className="text-xs text-[#6272a4] uppercase tracking-wider block mb-2 font-mono">API Key</label>
                            <div className="bg-[#1a1b26] rounded p-4 font-mono text-sm text-[#50fa7b] break-all">
                                {newApiKey}
                            </div>
                        </div>

                        <div className="flex gap-3">
                            <Button
                                onClick={handleCopyKey}
                                className="flex-1 bg-[#8be9fd] hover:bg-[#8be9fd] text-[#050101] font-bold"
                            >
                                📋 Copy to Clipboard
                            </Button>
                            <Button
                                onClick={onSuccess}
                                variant="outline"
                                className="border-[#50fa7b] text-[#50fa7b] hover:bg-[#50fa7b]/10"
                            >
                                Done
                            </Button>
                        </div>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4">
            <div className="bg-[#0b0b11] rounded-lg max-w-4xl w-full shadow-2xl border border-[#1a1b26] max-h-[90vh] overflow-hidden flex flex-col relative">

                {/* Scope Selection Modal */}
                {scopeModalIndex !== null && (
                    <div className="absolute inset-0 z-50 bg-black/90 flex flex-col p-6 animate-in fade-in duration-200">
                        <div className="flex justify-between items-center mb-4">
                            <div>
                                <h3 className="text-lg font-bold text-white">
                                    Tools Scope for <span className="text-[#50fa7b] font-mono">{envVars[scopeModalIndex].name || 'VARIABLE'}</span>
                                </h3>
                                <p className="text-sm text-[#6272a4]">Select which tools should receive this environment variable.</p>
                            </div>
                            <button
                                onClick={() => setScopeModalIndex(null)}
                                className="text-[#6272a4] hover:text-white"
                            >
                                <X size={24} />
                            </button>
                        </div>

                        <div className="flex mb-4 gap-2">
                            <Button
                                size="sm"
                                variant="outline"
                                onClick={() => {
                                    const newEnvVars = [...envVars];
                                    newEnvVars[scopeModalIndex].tool_ids = []; // Empty = All (Global)
                                    setEnvVars(newEnvVars);
                                }}
                                className={`border-${envVars[scopeModalIndex].tool_ids.length === 0 ? '[#50fa7b] bg-[#50fa7b]/10' : '[#6272a4]'}`}
                            >
                                🌍 Global (All Tools)
                            </Button>
                            <Button
                                size="sm"
                                variant="outline"
                                onClick={() => {
                                    // Just a label/container for the list below
                                }}
                                className="cursor-default border-transparent text-[#6272a4]"
                            >
                                Or Select Specific:
                            </Button>
                        </div>

                        <div className="flex-1 overflow-auto custom-scrollbar border border-[#282a36] rounded bg-[#0b0b11] p-2">
                            {enabledTools.length === 0 ? (
                                <p className="text-center text-[#6272a4] py-8">No tools enabled for this MCP yet. Select tools in the main form first.</p>
                            ) : (
                                <div className="space-y-1">
                                    {enabledTools.map(tool => {
                                        const isSelected = envVars[scopeModalIndex].tool_ids.includes(tool.id);
                                        // Specific selection logic

                                        return (
                                            <div key={tool.id} className="flex items-center gap-3 p-2 hover:bg-[#1a1b26] rounded cursor-pointer" onClick={() => {
                                                const currentIds = envVars[scopeModalIndex].tool_ids;
                                                const newEnvVars = [...envVars];

                                                if (isSelected) {
                                                    // Remove
                                                    newEnvVars[scopeModalIndex].tool_ids = currentIds.filter(id => id !== tool.id);
                                                } else {
                                                    // Add
                                                    newEnvVars[scopeModalIndex].tool_ids = [...currentIds, tool.id];
                                                }
                                                setEnvVars(newEnvVars);
                                            }}>
                                                <div className={`w-4 h-4 rounded border flex items-center justify-center transition-colors ${isSelected ? 'bg-[#50fa7b] border-[#50fa7b]' : 'border-[#6272a4]'}`}>
                                                    {isSelected && <Check size={12} className="text-black" />}
                                                </div>
                                                <div className="flex-1">
                                                    <span className={isSelected ? 'text-white font-medium' : 'text-[#aeb1b7]'}>{tool.name}</span>
                                                    <span className="text-[#6272a4] text-xs ml-2">({tool.id})</span>
                                                </div>
                                            </div>
                                        )
                                    })}
                                </div>
                            )}
                        </div>

                        <div className="mt-4 flex justify-end">
                            <Button
                                onClick={() => setScopeModalIndex(null)}
                                className="bg-[#50fa7b] hover:bg-[#50fa7b] text-black font-bold"
                            >
                                Done
                            </Button>
                        </div>
                    </div>
                )}

                {/* Header */}
                <div className="bg-gradient-to-r from-[#1a1b26] to-[#282a36] px-6 py-4 flex justify-between items-center border-b border-[#1a1b26]">
                    <h3 className="text-xl font-bold text-white uppercase tracking-wider">
                        {mcp ? 'Edit MCP Server' : 'Create New MCP Server'}
                    </h3>
                    <button
                        onClick={onClose}
                        className="text-[#6272a4] hover:text-white transition-colors"
                    >
                        <X size={24} />
                    </button>
                </div>

                {/* Form */}
                <form onSubmit={handleSubmit} className="flex-1 overflow-auto custom-scrollbar p-6 space-y-6">
                    {/* Name */}
                    <div>
                        <label className="text-xs text-[#6272a4] uppercase tracking-wider block mb-2 font-mono">
                            MCP Name <span className="text-[#ff5555]">*</span>
                        </label>
                        <input
                            type="text"
                            value={name}
                            onChange={(e) => setName(e.target.value)}
                            placeholder="e.g., Security Toolbox"
                            className="w-full bg-[#1a1b26] text-white rounded px-4 py-3 focus:outline-none focus:ring-1 focus:ring-[#8be9fd] transition-all placeholder-[#6272a4] text-sm"
                            required
                        />
                    </div>

                    {/* Description */}
                    <div>
                        <label className="text-xs text-[#6272a4] uppercase tracking-wider block mb-2 font-mono">
                            Description
                        </label>
                        <textarea
                            value={description}
                            onChange={(e) => setDescription(e.target.value)}
                            placeholder="Brief description of this MCP server..."
                            rows={3}
                            className="w-full bg-[#1a1b26] text-white rounded px-4 py-3 focus:outline-none focus:ring-1 focus:ring-[#8be9fd] transition-all placeholder-[#6272a4] text-sm resize-none"
                        />
                    </div>

                    {/* Logo Uploader */}
                    <LogoUploader
                        currentLogo={logoSVG || undefined}
                        onLogoChange={setLogoSVG}
                        label="MCP Server Logo"
                    />

                    {/* Env Vars Configuration (Global Contract) */}
                    <div className="bg-[#1a1b26] rounded-lg p-4">
                        <div className="flex justify-between items-center mb-4">
                            <div>
                                <h3 className="text-xs font-bold uppercase tracking-wider text-[#8be9fd] mb-1">Environment Variables Contract</h3>
                                <p className="text-xs text-[#6272a4]">Define expected variables. Clients (Claude) will see "Required" or descriptions.</p>
                            </div>
                            <button
                                type="button"
                                onClick={() => setEnvVars([...envVars, { name: '', description: '', default_value: '', required: false, tool_ids: [] }])}
                                className="p-1 hover:bg-[#282a36] rounded text-[#50fa7b] transition-colors"
                                title="Add Variable"
                            >
                                <Plus size={16} />
                            </button>
                        </div>

                        <div className="space-y-4">
                            {envVars.map((env, index) => (
                                <div key={index} className="bg-[#0b0b11] p-3 rounded border border-[#282a36] flex flex-col gap-2 relative group">
                                    <div className="flex gap-2">
                                        <div className="flex-1">
                                            <input
                                                type="text"
                                                placeholder="VARIABLE_NAME (e.g. GITHUB_TOKEN)"
                                                value={env.name}
                                                onChange={(e) => {
                                                    const newEnvVars = [...envVars];
                                                    newEnvVars[index].name = e.target.value.toUpperCase().replace(/[^A-Z0-9_]/g, '');
                                                    setEnvVars(newEnvVars);
                                                }}
                                                className="w-full bg-[#1a1b26] text-[#50fa7b] rounded px-3 py-2 text-xs font-mono font-bold focus:outline-none focus:ring-1 focus:ring-[#8be9fd] placeholder-[#6272a4]"
                                            />
                                        </div>
                                        <div className="flex-1">
                                            <input
                                                type="text"
                                                placeholder="Description (visible to client)"
                                                value={env.description}
                                                onChange={(e) => {
                                                    const newEnvVars = [...envVars];
                                                    newEnvVars[index].description = e.target.value;
                                                    setEnvVars(newEnvVars);
                                                }}
                                                className="w-full bg-[#1a1b26] text-white rounded px-3 py-2 text-xs focus:outline-none focus:ring-1 focus:ring-[#8be9fd] border border-[#282a36] placeholder-[#6272a4]"
                                            />
                                        </div>

                                        {/* Scope Button */}
                                        <button
                                            type="button"
                                            onClick={() => setScopeModalIndex(index)}
                                            className={`p-2 rounded transition-colors flex items-center gap-1 border ${env.tool_ids.length > 0 ? 'bg-[#ff79c6]/10 border-[#ff79c6] text-[#ff79c6]' : 'border-[#282a36] text-[#6272a4] hover:text-white'}`}
                                            title="Configure Scope"
                                        >
                                            <Filter size={14} />
                                            <span className="text-[10px] font-bold uppercase">
                                                {env.tool_ids.length > 0 ? `${env.tool_ids.length} Tools` : 'Global'}
                                            </span>
                                        </button>

                                        <button
                                            type="button"
                                            onClick={() => {
                                                const newEnvVars = envVars.filter((_, i) => i !== index);
                                                setEnvVars(newEnvVars);
                                            }}
                                            className="p-2 text-[#ff5555] hover:bg-[#ff5555]/10 rounded transition-colors self-start"
                                        >
                                            <Trash2 size={14} />
                                        </button>
                                    </div>
                                    <div className="flex gap-4 items-center pl-1">
                                        <div className="flex-1">
                                            <input
                                                type="text"
                                                placeholder="Default Value (Optional Secret)"
                                                value={env.default_value}
                                                onChange={(e) => {
                                                    const newEnvVars = [...envVars];
                                                    newEnvVars[index].default_value = e.target.value;
                                                    setEnvVars(newEnvVars);
                                                }}
                                                className="w-full bg-[#1a1b26] text-[#f1fa8c] rounded px-3 py-2 text-xs font-mono focus:outline-none focus:ring-1 focus:ring-[#f1fa8c] border border-[#282a36] placeholder-[#6272a4]"
                                            />
                                        </div>
                                        <label className="flex items-center gap-2 cursor-pointer select-none">
                                            <input
                                                type="checkbox"
                                                checked={env.required}
                                                onChange={(e) => {
                                                    const newEnvVars = [...envVars];
                                                    newEnvVars[index].required = e.target.checked;
                                                    setEnvVars(newEnvVars);
                                                }}
                                                className="appearance-none h-4 w-4 bg-[#1a1b26] border border-[#6272a4] rounded cursor-pointer checked:bg-[#ff5555] checked:border-[#ff5555] transition-all"
                                            />
                                            {env.required && <Check size={12} className="absolute text-white pointer-events-none ml-0.5" />}
                                            <span className={`text-xs font-bold ${env.required ? 'text-[#ff5555]' : 'text-[#6272a4]'}`}>REQUIRED</span>
                                        </label>
                                    </div>
                                </div>
                            ))}
                            {envVars.length === 0 && (
                                <p className="text-xs text-[#6272a4] italic text-center py-4 border border-dashed border-[#282a36] rounded hover:border-[#8be9fd] cursor-pointer" onClick={() => setEnvVars([...envVars, { name: '', description: '', default_value: '', required: false, tool_ids: [] }])}>
                                    + Add Contract Variable
                                </p>
                            )}
                        </div>
                    </div>

                    {/* Tools Selection */}
                    <div>
                        <label className="text-xs text-[#6272a4] uppercase tracking-wider block mb-3 font-mono">
                            Select Tools <span className="text-[#ff5555]">*</span>
                            <span className="ml-3 text-[#8be9fd] font-normal">({selectedToolIds.length} selected)</span>
                        </label>

                        {loadingTools ? (
                            <div className="flex items-center justify-center p-8 text-[#6272a4]">
                                <Loader2 className="animate-spin mr-2" size={20} />
                                Loading tools...
                            </div>
                        ) : (
                            <div className="space-y-4">
                                {Object.entries(toolsByCategory).map(([category, tools]) => {
                                    const allSelected = tools.every(tool => selectedToolIds.includes(tool.id));
                                    const someSelected = tools.some(tool => selectedToolIds.includes(tool.id));

                                    return (
                                        <div key={category} className="bg-[#1a1b26] rounded-lg p-4">
                                            {/* Category Header */}
                                            <div
                                                onClick={() => handleSelectCategory(category)}
                                                className="flex items-center gap-3 mb-3 cursor-pointer hover:bg-[#282a36] p-2 rounded transition-colors"
                                            >
                                                <div className="relative flex items-center justify-center p-0.5">
                                                    <input
                                                        type="checkbox"
                                                        checked={allSelected}
                                                        onChange={() => { }}
                                                        className="appearance-none h-5 w-5 bg-[#0b0b11] border border-[#6272a4] rounded cursor-pointer checked:bg-[#8be9fd] checked:border-[#8be9fd] transition-all"
                                                        style={{
                                                            opacity: someSelected && !allSelected ? 0.5 : 1
                                                        }}
                                                    />
                                                    {allSelected && <Check size={14} className="absolute text-[#050101] pointer-events-none" />}
                                                    {someSelected && !allSelected && <div className="absolute w-2.5 h-2.5 bg-[#8be9fd] rounded-sm pointer-events-none" />}
                                                </div>
                                                <span className="text-sm font-bold text-[#8be9fd] uppercase tracking-wider">{category}</span>
                                                <span className="text-xs text-[#6272a4]">({tools.length} tools)</span>
                                            </div>

                                            {/* Tools */}
                                            <div className="pl-10 space-y-2">
                                                {tools.map(tool => (
                                                    <label
                                                        key={tool.id}
                                                        className="flex items-start gap-3 p-2 hover:bg-[#282a36] rounded cursor-pointer transition-colors"
                                                    >
                                                        <div className="relative flex items-center justify-center p-0.5">
                                                            <input
                                                                type="checkbox"
                                                                checked={selectedToolIds.includes(tool.id)}
                                                                onChange={() => handleToggleTool(tool.id)}
                                                                className="appearance-none h-4 w-4 bg-[#0b0b11] border border-[#6272a4] rounded cursor-pointer checked:bg-[#50fa7b] checked:border-[#50fa7b] transition-all"
                                                            />
                                                            {selectedToolIds.includes(tool.id) && <Check size={12} className="absolute text-[#050101] pointer-events-none" />}
                                                        </div>
                                                        <div className="flex-1">
                                                            <div className="text-sm text-white font-medium">{tool.name}</div>
                                                            <div className="text-xs text-[#6272a4] mt-0.5">{tool.description}</div>
                                                        </div>
                                                    </label>
                                                ))}
                                            </div>
                                        </div>
                                    );
                                })}
                            </div>
                        )}
                    </div>
                </form>

                {/* Footer */}
                <div className="bg-gradient-to-r from-[#1a1b26] to-[#282a36] px-6 py-4 border-t border-[#1a1b26] flex justify-end gap-3">
                    <Button
                        type="button"
                        variant="ghost"
                        onClick={onClose}
                        disabled={loading}
                    >
                        Cancel
                    </Button>
                    <Button
                        type="submit"
                        onClick={handleSubmit}
                        disabled={loading || !name.trim() || selectedToolIds.length === 0}
                        className="bg-[#50fa7b] hover:bg-[#50fa7b] text-[#050101] font-black uppercase tracking-wider border-b-4 border-[#2aa34a] hover:border-[#2aa34a] active:border-b-0 active:translate-y-1 transition-all"
                    >
                        {loading ? (
                            <>
                                <Loader2 className="animate-spin mr-2" size={16} />
                                {mcp ? 'Updating...' : 'Creating...'}
                            </>
                        ) : (
                            mcp ? 'Update MCP' : 'Create MCP'
                        )}
                    </Button>
                </div>
            </div>
        </div>
    );
};

export default MCPFormDialog;
