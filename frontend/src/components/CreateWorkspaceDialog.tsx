import React, { useState } from 'react';
import { X, FolderPlus, Upload } from 'lucide-react';
import { Button } from "@/components/ui/Button/Button";
import { useToast } from './Toast';

interface CreateWorkspaceDialogProps {
    onClose: () => void;
    onSuccess: () => void;
}

const CreateWorkspaceDialog: React.FC<CreateWorkspaceDialogProps> = ({ onClose, onSuccess }) => {
    const [workspaceName, setWorkspaceName] = useState('');
    const [description, setDescription] = useState('');
    const [svgCode, setSvgCode] = useState('');
    const [creating, setCreating] = useState(false);
    const toast = useToast();

    const handleCreate = async () => {
        if (!workspaceName.trim()) {
            toast.error('Workspace name is required');
            return;
        }

        // Validate name (alphanumeric, underscores, hyphens)
        if (!/^[a-zA-Z0-9_-]+$/.test(workspaceName)) {
            toast.error('Workspace name can only contain letters, numbers, underscores and hyphens');
            return;
        }

        setCreating(true);
        try {
            // 1. Create Workspace
            const res = await fetch('/api/workspaces', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    name: workspaceName,
                    description: description
                })
            });

            if (!res.ok) {
                const error = await res.json();
                toast.error(`Failed to create workspace: ${error.detail || 'Unknown error'}`);
                return;
            }

            // 2. Upload Logo if provided
            if (svgCode.trim()) {
                const logoRes = await fetch(`/api/workspaces/${workspaceName}/logo`, {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ svg_code: svgCode })
                });

                if (!logoRes.ok) {
                    console.error('Failed to upload logo');
                    toast.warning('Workspace created but logo upload failed');
                }
            }

            toast.success(`Workspace "${workspaceName}" created successfully!`);
            onSuccess();
        } catch (err) {
            console.error('Error creating workspace:', err);
            toast.error('Failed to create workspace');
        } finally {
            setCreating(false);
        }
    };

    return (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4">
            <div className="bg-[#0b0b11] rounded-lg shadow-2xl border border-[#1a1b26] w-full max-w-md max-h-[90vh] overflow-y-auto">
                {/* Header */}
                <div className="bg-gradient-to-r from-[#1a1b26] to-[#282a36] px-6 py-4 flex justify-between items-center rounded-t-lg sticky top-0 z-10">
                    <div className="flex items-center gap-3">
                        <FolderPlus size={24} className="text-[#8be9fd]" />
                        <div>
                            <h3 className="text-xl font-bold text-white">Create New Workspace</h3>
                            <p className="text-sm text-[#6272a4]">Add a new category for tools</p>
                        </div>
                    </div>
                    <Button variant="ghost" size="sm" onClick={onClose}>
                        <X size={20} />
                    </Button>
                </div>

                {/* Content */}
                <div className="p-6 space-y-4">
                    {/* Name */}
                    <div>
                        <label className="block text-sm font-mono text-[#6272a4] uppercase mb-2">
                            Workspace Name
                        </label>
                        <input
                            type="text"
                            value={workspaceName}
                            onChange={(e) => setWorkspaceName(e.target.value)}
                            placeholder="e.g., Network, Web, Mobile"
                            className="w-full bg-[#1a1b26] border border-[#282a36] rounded px-4 py-3 text-white font-mono focus:outline-none focus:border-[#8be9fd]"
                            autoFocus
                        />
                        <p className="text-xs text-[#6272a4] mt-2">
                            Use letters, numbers, underscores (_) and hyphens (-) only
                        </p>
                    </div>

                    {/* Description */}
                    <div>
                        <label className="block text-sm font-mono text-[#6272a4] uppercase mb-2">
                            Description (Optional)
                        </label>
                        <textarea
                            value={description}
                            onChange={(e) => setDescription(e.target.value)}
                            placeholder="Brief description of this workspace..."
                            className="w-full bg-[#1a1b26] border border-[#282a36] rounded px-4 py-3 text-white font-mono focus:outline-none focus:border-[#8be9fd] min-h-[80px]"
                        />
                    </div>

                    {/* Logo (Upload) */}
                    <div>
                        <label className="block text-sm font-mono text-[#6272a4] uppercase mb-2">
                            Workspace Logo
                        </label>
                        <div className="flex flex-col gap-3">
                            <div className="flex items-center gap-3">
                                <Button
                                    variant="outline"
                                    onClick={() => document.getElementById('logo-upload')?.click()}
                                    className="border-dashed border-[#6272a4] text-[#6272a4] hover:text-[#8be9fd] hover:border-[#8be9fd] w-full h-24 flex flex-col gap-2"
                                >
                                    <Upload size={24} />
                                    <span>Click to upload SVG</span>
                                </Button>
                                <input
                                    id="logo-upload"
                                    type="file"
                                    accept=".svg"
                                    className="hidden"
                                    onChange={(e) => {
                                        const file = e.target.files?.[0];
                                        if (file) {
                                            const reader = new FileReader();
                                            reader.onload = (e) => setSvgCode(e.target?.result as string);
                                            reader.readAsText(file);
                                        }
                                    }}
                                />
                            </div>

                            {svgCode && (
                                <div className="bg-[#1a1b26] border border-[#282a36] rounded p-3 flex items-center justify-between">
                                    <div className="flex items-center gap-3">
                                        <div className="w-10 h-10 p-1 bg-[#0b0b11] rounded border border-[#282a36] [&>svg]:w-full [&>svg]:h-full" dangerouslySetInnerHTML={{ __html: svgCode }} />
                                        <span className="text-xs text-[#8be9fd] font-mono">Logo uploaded</span>
                                    </div>
                                    <Button
                                        size="sm"
                                        variant="ghost"
                                        onClick={() => setSvgCode('')}
                                        className="text-[#ff5555] hover:bg-[#ff5555]/10 h-8 w-8 p-0"
                                    >
                                        <X size={16} />
                                    </Button>
                                </div>
                            )}
                        </div>
                    </div>

                    {/* Examples */}
                    <div className="bg-[#1a1b26] border border-[#282a36]/50 rounded p-3">
                        <p className="text-xs text-[#6272a4] mb-2">💡 Examples:</p>
                        <div className="flex flex-wrap gap-2">
                            {['Network', 'Web', 'Mobile', 'Cloud', 'Crypto', 'AI_Security'].map(example => (
                                <button
                                    key={example}
                                    onClick={() => setWorkspaceName(example)}
                                    className="px-2 py-1 bg-[#282a36] hover:bg-[#383a46] text-[#8be9fd] text-xs rounded transition-colors"
                                >
                                    {example}
                                </button>
                            ))}
                        </div>
                    </div>
                </div>

                {/* Footer */}
                <div className="px-6 py-4 bg-[#1a1b26] rounded-b-lg flex justify-end gap-3 sticky bottom-0 z-10 border-t border-[#282a36]">
                    <Button
                        variant="outline"
                        onClick={onClose}
                        disabled={creating}
                        className="border-[#6272a4]/40"
                    >
                        Cancel
                    </Button>
                    <Button
                        onClick={handleCreate}
                        disabled={creating || !workspaceName.trim()}
                        className="bg-[#8be9fd] hover:bg-[#8be9fd]/90 text-[#050101] font-bold gap-2"
                    >
                        <FolderPlus size={16} />
                        {creating ? 'Creating...' : 'Create Workspace'}
                    </Button>
                </div>
            </div>
        </div>
    );
};

export default CreateWorkspaceDialog;
