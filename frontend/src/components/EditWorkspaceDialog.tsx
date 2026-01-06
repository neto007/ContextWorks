import React, { useState, useEffect } from 'react';
import { X, FolderCog, Trash2, AlertTriangle, Upload } from 'lucide-react';
import { Button } from "@/components/ui/Button/Button";
import { useToast } from './Toast';

interface EditWorkspaceDialogProps {
    workspaceName: string;
    description?: string;
    onClose: () => void;
    onSuccess: () => void;
}

const EditWorkspaceDialog: React.FC<EditWorkspaceDialogProps> = ({
    workspaceName: initialName,
    description: initialDescription = '',
    onClose,
    onSuccess
}) => {
    const [name, setName] = useState(initialName);
    const [description, setDescription] = useState(initialDescription);
    const [svgCode, setSvgCode] = useState('');
    const [loading, setLoading] = useState(false);
    const [confirmDelete, setConfirmDelete] = useState(false);
    const toast = useToast();

    useEffect(() => {
        // Fetch existing logo
        const fetchLogo = async () => {
            try {
                const res = await fetch(`/api/workspaces/${initialName}/logo`);
                if (res.ok) {
                    const text = await res.text();
                    setSvgCode(text);
                }
            } catch (err) {
                console.error('Error fetching logo:', err);
            } finally {
                // loading done
            }
        };

        fetchLogo();
    }, [initialName]);

    const handleUpdate = async () => {
        if (!name.trim()) {
            toast.error('Workspace name is required');
            return;
        }

        setLoading(true);
        try {
            // 1. Update metadata (Name/Description)
            const res = await fetch(`/api/workspaces/${initialName}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    name: name,
                    description: description
                })
            });

            if (!res.ok) {
                let errorDetails = 'Unknown error';
                try {
                    const error = await res.json();
                    errorDetails = error.detail || JSON.stringify(error);
                } catch (e) {
                    errorDetails = `HTTP ${res.status}`;
                }
                toast.error(`Failed to update workspace metadata: ${errorDetails}`);
                return;
            }

            // 2. Update Logo if changed (we send it anyway if it supports idempotent updates)
            // Use the NEW name if the update succeeded, as the folder might have moved.
            const targetWorkspace = name.trim();

            if (svgCode.trim()) {
                try {
                    const logoRes = await fetch(`/api/workspaces/${targetWorkspace}/logo`, {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({ svg_code: svgCode })
                    });

                    if (!logoRes.ok) {
                        console.warn('Logo upload failed', logoRes.status);
                        toast.warning('Workspace updated, but logo upload failed. Try a smaller file?');
                        // Do not return, treat as success for the main action
                    }
                } catch (logoErr) {
                    console.error('Network error uploading logo:', logoErr);
                    toast.warning('Workspace updated, but logo upload failed due to network error.');
                }
            }

            toast.success('Workspace updated successfully');
            onSuccess();
        } catch (err) {
            console.error('Error updating workspace:', err);
            toast.error('Failed to update workspace due to network error');
        } finally {
            setLoading(false);
        }
    };

    const handleDelete = async () => {
        setLoading(true);
        try {
            const res = await fetch(`/api/workspaces/${initialName}`, {
                method: 'DELETE'
            });

            if (!res.ok) {
                throw new Error('Failed to delete');
            }

            toast.success('Workspace deleted successfully');
            onSuccess();
        } catch (err) {
            console.error('Error deleting workspace:', err);
            toast.error('Failed to delete workspace');
            setLoading(false);
        }
    };

    if (confirmDelete) {
        return (
            <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4">
                <div className="bg-[#0b0b11] rounded-lg shadow-2xl border border-[#ff5555] w-full max-w-sm p-6 text-center">
                    <AlertTriangle size={48} className="text-[#ff5555] mx-auto mb-4" />
                    <h3 className="text-xl font-bold text-white mb-2">Delete Workspace?</h3>
                    <p className="text-[#6272a4] mb-6">
                        Are you sure you want to delete <strong>{initialName}</strong>?
                        <br />
                        This will delete all tools and files within this workspace. This action cannot be undone.
                    </p>
                    <div className="flex gap-3 justify-center">
                        <Button variant="outline" onClick={() => setConfirmDelete(false)}>
                            Cancel
                        </Button>
                        <Button
                            className="bg-[#ff5555] hover:bg-[#ff5555]/90 text-white font-bold"
                            onClick={handleDelete}
                            disabled={loading}
                        >
                            {loading ? 'Deleting...' : 'Yes, Delete'}
                        </Button>
                    </div>
                </div>
            </div>
        );
    }

    return (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4">
            <div className="bg-[#0b0b11] rounded-lg shadow-2xl border border-[#1a1b26] w-full max-w-md max-h-[90vh] overflow-y-auto">
                {/* Header */}
                <div className="bg-gradient-to-r from-[#1a1b26] to-[#282a36] px-6 py-4 flex justify-between items-center rounded-t-lg sticky top-0 z-10">
                    <div className="flex items-center gap-3">
                        <FolderCog size={24} className="text-[#8be9fd]" />
                        <div>
                            <h3 className="text-xl font-bold text-white">Edit Workspace</h3>
                            <p className="text-sm text-[#6272a4]">Manage workspace settings</p>
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
                            value={name}
                            onChange={(e) => setName(e.target.value)}
                            className="w-full bg-[#1a1b26] border border-[#282a36] rounded px-4 py-3 text-white font-mono focus:outline-none focus:border-[#8be9fd]"
                        />
                    </div>

                    {/* Description */}
                    <div>
                        <label className="block text-sm font-mono text-[#6272a4] uppercase mb-2">
                            Description
                        </label>
                        <textarea
                            value={description}
                            onChange={(e) => setDescription(e.target.value)}
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
                                    onClick={() => document.getElementById('edit-logo-upload')?.click()}
                                    className="border-dashed border-[#6272a4] text-[#6272a4] hover:text-[#8be9fd] hover:border-[#8be9fd] w-full h-24 flex flex-col gap-2"
                                >
                                    <Upload size={24} />
                                    <span>Click to upload new SVG</span>
                                </Button>
                                <input
                                    id="edit-logo-upload"
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
                                        <span className="text-xs text-[#8be9fd] font-mono">Current Logo</span>
                                    </div>
                                    <Button
                                        size="sm"
                                        variant="ghost"
                                        onClick={() => setSvgCode('')}
                                        className="text-[#ff5555] hover:bg-[#ff5555]/10 h-8 w-8 p-0"
                                    >
                                        <Trash2 size={16} />
                                    </Button>
                                </div>
                            )}
                        </div>
                    </div>
                </div>

                {/* Footer */}
                <div className="px-6 py-4 bg-[#1a1b26] rounded-b-lg flex justify-between items-center sticky bottom-0 z-10 border-t border-[#282a36]">
                    <Button
                        variant="ghost"
                        onClick={() => setConfirmDelete(true)}
                        className="text-[#ff5555] hover:bg-[#ff5555]/10 px-0"
                    >
                        <Trash2 size={16} className="mr-2" />
                        Delete Workspace
                    </Button>

                    <div className="flex gap-3">
                        <Button
                            variant="outline"
                            onClick={onClose}
                            disabled={loading}
                            className="border-[#6272a4]/40"
                        >
                            Cancel
                        </Button>
                        <Button
                            onClick={handleUpdate}
                            disabled={loading || !name.trim()}
                            className="bg-[#8be9fd] hover:bg-[#8be9fd]/90 text-[#050101] font-bold"
                        >
                            {loading ? 'Saving...' : 'Save Changes'}
                        </Button>
                    </div>
                </div>
            </div>
        </div>
    );
};

export default EditWorkspaceDialog;
