import React from 'react';
import { X, Settings } from 'lucide-react';
import { Button } from "@/components/ui/Button/Button";

interface WorkspaceConfigDialogProps {
    workspaces: string[];
    visibleWorkspaces: Set<string>;
    onToggle: (workspace: string) => void;
    onShowAll: () => void;
    onHideAll: () => void;
    onClose: () => void;
}

const WorkspaceConfigDialog: React.FC<WorkspaceConfigDialogProps> = ({
    workspaces,
    visibleWorkspaces,
    onToggle,
    onShowAll,
    onHideAll,
    onClose
}) => {
    const visibleCount = visibleWorkspaces.size;
    const totalCount = workspaces.length;

    return (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-[70] p-4">
            <div className="bg-[#0b0b11] rounded-lg shadow-2xl border border-[#1a1b26] w-full max-w-md">
                {/* Header */}
                <div className="bg-gradient-to-r from-[#1a1b26] to-[#282a36] px-6 py-4 flex justify-between items-center rounded-t-lg">
                    <div>
                        <h3 className="text-xl font-bold text-white flex items-center gap-2">
                            <Settings size={20} className="text-[#8be9fd]" />
                            Configure Workspaces
                        </h3>
                        <p className="text-sm text-[#6272a4]">
                            {visibleCount} of {totalCount} visible
                        </p>
                    </div>
                    <Button variant="ghost" size="sm" onClick={onClose}>
                        <X size={20} />
                    </Button>
                </div>

                {/* Content */}
                <div className="p-6">
                    {/* Quick actions */}
                    <div className="flex gap-2 mb-4">
                        <Button
                            onClick={onShowAll}
                            size="sm"
                            className="bg-[#50fa7b] hover:bg-[#50fa7b]/90 text-[#050101] font-black uppercase tracking-wider text-xs border-b-2 border-[#38b359] hover:border-[#38b359] active:border-b-0 active:translate-y-0.5"
                        >
                            Show All
                        </Button>
                        <Button
                            onClick={onHideAll}
                            size="sm"
                            className="bg-[#ff5555] hover:bg-[#ff5555]/90 text-[#050101] font-black uppercase tracking-wider text-xs border-b-2 border-[#b33b3b] hover:border-[#b33b3b] active:border-b-0 active:translate-y-0.5"
                        >
                            Hide All
                        </Button>
                    </div>

                    {/* Workspace list */}
                    <div className="space-y-2 max-h-[400px] overflow-y-auto custom-scrollbar">
                        {workspaces.length === 0 ? (
                            <div className="text-center py-8 text-[#6272a4]">
                                No workspaces found
                            </div>
                        ) : (
                            workspaces.map(workspace => {
                                const isVisible = visibleWorkspaces.has(workspace);
                                return (
                                    <label
                                        key={workspace}
                                        className={`
                      flex items-center gap-3 cursor-pointer 
                      p-3 rounded transition-all
                      ${isVisible
                                                ? 'bg-[#8be9fd]/10 hover:bg-[#8be9fd]/20 border border-[#8be9fd]/30'
                                                : 'bg-[#1a1b26] hover:bg-[#282a36] border border-transparent'
                                            }
                    `}
                                    >
                                        <input
                                            type="checkbox"
                                            checked={isVisible}
                                            onChange={() => onToggle(workspace)}
                                            className="w-4 h-4 accent-[#8be9fd]"
                                        />
                                        <span className={`font-mono text-sm ${isVisible ? 'text-white' : 'text-[#6272a4]'}`}>
                                            # {workspace}
                                        </span>
                                        {!isVisible && (
                                            <span className="ml-auto text-xs text-[#6272a4]">(hidden)</span>
                                        )}
                                    </label>
                                );
                            })
                        )}
                    </div>
                </div>

                {/* Footer */}
                <div className="px-6 py-4 bg-[#1a1b26] rounded-b-lg flex justify-end">
                    <Button
                        onClick={onClose}
                        className="bg-[#8be9fd] hover:bg-[#8be9fd]/90 text-[#050101] font-bold"
                    >
                        Done
                    </Button>
                </div>
            </div>
        </div>
    );
};

export default WorkspaceConfigDialog;
