import React, { useState, useEffect, useCallback, Suspense, lazy } from 'react';
import { FolderOpen, Plus, Wrench } from 'lucide-react';
import { Button } from "@/components/ui/Button/Button";
import { useToast } from './Toast';
import ToolCard from './ToolCard';
import WorkspaceItem from './WorkspaceItem';

// Lazy load dialogs
const CreateToolDialog = lazy(() => import('./CreateToolDialog'));
const EditToolDialog = lazy(() => import('./EditToolDialog'));
const CreateWorkspaceDialog = lazy(() => import('./CreateWorkspaceDialog'));
const EditWorkspaceDialog = lazy(() => import('./EditWorkspaceDialog'));
const DeleteConfirmDialog = lazy(() => import('./DeleteConfirmDialog'));

interface Workspace {
    name: string;
    path: string;
    tool_count: number;
    description?: string;
    has_logo?: boolean;
}

interface Tool {
    id: string;
    name: string;
    category: string;
    has_logo?: boolean;
}

interface WorkspaceManagerProps {
    onRefreshWorkspaces?: () => void;
}

const WorkspaceManager: React.FC<WorkspaceManagerProps> = ({ onRefreshWorkspaces }) => {
    const [workspaces, setWorkspaces] = useState<Workspace[]>([]);
    const [expandedWorkspaces, setExpandedWorkspaces] = useState<Set<string>>(new Set());
    const [workspaceTools, setWorkspaceTools] = useState<Record<string, Tool[]>>({});
    const [loading, setLoading] = useState(true);
    const [showCreateDialog, setShowCreateDialog] = useState(false);
    const [showEditDialog, setShowEditDialog] = useState(false);
    const [selectedWorkspace, setSelectedWorkspace] = useState<string | null>(null);
    const [selectedToolForEdit, setSelectedToolForEdit] = useState<{ workspace: string; toolId: string } | null>(null);
    const [showCreateWorkspaceDialog, setShowCreateWorkspaceDialog] = useState(false);
    const [selectedWorkspaceForEdit, setSelectedWorkspaceForEdit] = useState<Workspace | null>(null);
    const [showDeleteDialog, setShowDeleteDialog] = useState(false);
    const [toolToDelete, setToolToDelete] = useState<{ category: string; toolId: string } | null>(null);
    const [isDeleting, setIsDeleting] = useState(false);
    const toast = useToast();

    const fetchWorkspaces = async () => {
        setLoading(true);
        try {
            const res = await fetch('/api/workspaces');
            const data = await res.json();
            setWorkspaces(data);
        } catch (err) {
            console.error('Error fetching workspaces:', err);
        } finally {
            setLoading(false);
        }
    };

    const fetchToolsForWorkspace = async (workspaceName: string) => {
        try {
            const res = await fetch('/api/tools');
            const allTools = await res.json();

            // Filter tools for this workspace
            const tools = Object.values(allTools[workspaceName] || []) as Tool[];
            setWorkspaceTools(prev => ({ ...prev, [workspaceName]: tools }));
        } catch (err) {
            console.error(`Error fetching tools for ${workspaceName}:`, err);
        }
    };

    const toggleWorkspace = useCallback(async (workspaceName: string) => {
        setExpandedWorkspaces(prev => {
            const newExpanded = new Set(prev);
            if (newExpanded.has(workspaceName)) {
                newExpanded.delete(workspaceName);
            } else {
                newExpanded.add(workspaceName);
            }
            return newExpanded;
        });

        // Fetch tools if needed (check logic outside setState to avoid async in setState)
        if (!expandedWorkspaces.has(workspaceName) && !workspaceTools[workspaceName]) {
            await fetchToolsForWorkspace(workspaceName);
        }
    }, [expandedWorkspaces, workspaceTools]);

    const handleCreateTool = useCallback((workspaceName: string) => {
        setSelectedWorkspace(workspaceName);
        setShowCreateDialog(true);
    }, []);

    const handleEditWorkspace = useCallback((workspace: Workspace) => {
        setSelectedWorkspaceForEdit(workspace);
    }, []);

    const handleEditTool = useCallback((workspace: string, toolId: string) => {
        setSelectedToolForEdit({ workspace, toolId });
        setShowEditDialog(true);
    }, []);

    const handleDeleteTool = useCallback((category: string, toolId: string) => {
        setToolToDelete({ category, toolId });
        setShowDeleteDialog(true);
    }, []);

    const confirmDeleteTool = useCallback(async () => {
        if (!toolToDelete) return;

        setIsDeleting(true);
        try {
            const res = await fetch(`/api/tools/${toolToDelete.category}/${toolToDelete.toolId}`, { method: 'DELETE' });
            if (res.ok) {
                toast.success('Tool deletada com sucesso!');
                // Refresh tools for this workspace
                await fetchToolsForWorkspace(toolToDelete.category);
                await fetchWorkspaces(); // Update counts
                setShowDeleteDialog(false);
                setToolToDelete(null);
            } else {
                toast.error('Falha ao deletar tool');
            }
        } catch (err) {
            console.error('Error deleting tool:', err);
            toast.error('Erro ao deletar tool');
        } finally {
            setIsDeleting(false);
        }
    }, [toolToDelete, fetchWorkspaces]);

    useEffect(() => {
        fetchWorkspaces();
    }, []);

    return (
        <div className="flex flex-col h-full">
            {/* Header */}
            <div className="mb-6">
                <div className="flex justify-between items-start">
                    <div>
                        <h2 className="text-3xl font-black text-white tracking-widest uppercase mb-1 flex items-center gap-3" style={{ textShadow: "0 0 10px rgba(139,233,253,0.5)" }}>
                            <FolderOpen size={32} className="text-[#8be9fd]" />
                            WORKSPACES
                        </h2>
                        <p className="text-[#6272a4] text-sm">Gerenciar categorias e criar novas security tools</p>
                    </div>
                    <Button
                        onClick={() => setShowCreateWorkspaceDialog(true)}
                        className="bg-[#8be9fd] hover:bg-[#8be9fd] text-[#050101] font-black uppercase tracking-wider border-b-4 border-[#569cd6] hover:border-[#569cd6] active:border-b-0 active:translate-y-1 transition-all gap-2"
                    >
                        <Plus size={18} />
                        New Workspace
                    </Button>
                </div>
            </div>

            {/* Workspace Grid */}
            <div className="flex-1 overflow-auto custom-scrollbar">
                {loading ? (
                    <div className="flex items-center justify-center h-full text-[#6272a4]">
                        <div className="animate-spin mr-2">⚙️</div>
                        Loading workspaces...
                    </div>
                ) : (
                    <div className="grid grid-cols-[repeat(auto-fill,minmax(380px,1fr))] gap-6">
                        {workspaces.map((workspace) => (
                            <WorkspaceItem
                                key={workspace.name}
                                workspace={workspace}
                                isExpanded={expandedWorkspaces.has(workspace.name)}
                                onToggle={toggleWorkspace}
                                onEdit={handleEditWorkspace}
                                onAddTool={handleCreateTool}
                            >
                                {workspaceTools[workspace.name]?.length > 0 ? (
                                    <div className="grid grid-cols-1 gap-3">
                                        {workspaceTools[workspace.name].map((tool) => (
                                            <ToolCard
                                                key={tool.id}
                                                tool={tool}
                                                onEdit={handleEditTool}
                                                onDelete={handleDeleteTool}
                                            />
                                        ))}
                                    </div>
                                ) : (
                                    <div className="text-center py-6 text-[#6272a4] text-sm flex flex-col items-center">
                                        <div className="mb-2 p-3 rounded-full bg-[#1a1b26]">
                                            <Wrench size={24} className="opacity-50" />
                                        </div>
                                        Nenhuma tool nesta categoria
                                    </div>
                                )}
                            </WorkspaceItem>
                        ))}
                    </div>
                )}
            </div>

            {/* Dialogs */}
            <Suspense fallback={null}>
                {showCreateDialog && (
                    <CreateToolDialog
                        workspace={selectedWorkspace}
                        onClose={() => {
                            setShowCreateDialog(false);
                            setSelectedWorkspace(null);
                        }}
                        onSuccess={async () => {
                            setShowCreateDialog(false);

                            // Auto-expand the workspace if not already expanded
                            if (selectedWorkspace) {
                                setExpandedWorkspaces(prev => {
                                    const next = new Set(prev);
                                    next.add(selectedWorkspace);
                                    return next;
                                });

                                await fetchWorkspaces();
                                await fetchToolsForWorkspace(selectedWorkspace);

                                if (onRefreshWorkspaces) {
                                    onRefreshWorkspaces();
                                }
                            }

                            setSelectedWorkspace(null);
                        }}
                    />
                )}

                {showEditDialog && selectedToolForEdit && (
                    <EditToolDialog
                        workspace={selectedToolForEdit.workspace}
                        toolId={selectedToolForEdit.toolId}
                        onClose={() => {
                            setShowEditDialog(false);
                            setSelectedToolForEdit(null);
                        }}
                        onSuccess={async () => {
                            setShowEditDialog(false);
                            if (selectedToolForEdit) {
                                await fetchWorkspaces();
                                await fetchToolsForWorkspace(selectedToolForEdit.workspace);
                            }
                            setSelectedToolForEdit(null);
                        }}
                    />
                )}
                {/* Create Workspace Dialog */}
                {showCreateWorkspaceDialog && (
                    <CreateWorkspaceDialog
                        onClose={() => setShowCreateWorkspaceDialog(false)}
                        onSuccess={() => {
                            setShowCreateWorkspaceDialog(false);
                            fetchWorkspaces();
                            if (onRefreshWorkspaces) {
                                onRefreshWorkspaces();
                            }
                        }}
                    />
                )}

                {/* Edit Workspace Dialog */}
                {selectedWorkspaceForEdit && (
                    <EditWorkspaceDialog
                        workspaceName={selectedWorkspaceForEdit.name}
                        description={selectedWorkspaceForEdit.description}
                        onClose={() => setSelectedWorkspaceForEdit(null)}
                        onSuccess={() => {
                            setSelectedWorkspaceForEdit(null);
                            fetchWorkspaces();
                        }}
                    />
                )}

                {/* Delete Confirm Dialog */}
                {showDeleteDialog && toolToDelete && (
                    <DeleteConfirmDialog
                        isOpen={showDeleteDialog}
                        onClose={() => {
                            setShowDeleteDialog(false);
                            setToolToDelete(null);
                        }}
                        onConfirm={confirmDeleteTool}
                        itemName={toolToDelete.toolId}
                        itemType="tool"
                        isDeleting={isDeleting}
                    />
                )}
            </Suspense>
        </div>
    );
};

export default WorkspaceManager;
