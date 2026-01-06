import React from 'react';
import { ChevronDown, ChevronRight, Edit, Plus } from 'lucide-react';
import { Button } from "@/components/ui/Button/Button";
import GlowImage from './GlowImage';

interface Workspace {
    name: string;
    path: string;
    tool_count: number;
    description?: string;
    has_logo?: boolean;
}

interface WorkspaceItemProps {
    workspace: Workspace;
    isExpanded: boolean;
    onToggle: (name: string) => void;
    onEdit: (workspace: Workspace) => void;
    onAddTool: (name: string) => void;
    children?: React.ReactNode;
}

const WorkspaceItem: React.FC<WorkspaceItemProps> = React.memo(({
    workspace,
    isExpanded,
    onToggle,
    onEdit,
    onAddTool,
    children
}) => {

    const renderWorkspaceIcon = (workspace: Workspace) => {
        if (workspace.has_logo) {
            return (
                <GlowImage
                    src={`/api/workspaces/${workspace.name}/logo`}
                    alt={workspace.name}
                    className="w-full h-full object-cover"
                    radius={12}
                />
            );
        }

        const iconMap: Record<string, string> = {
            'Network': '🌐',
            'Web': '🕸️',
            'Cryptography': '🔐',
            'Binary': '🔢',
            'Mobile': '📱',
            'DevSecOps': '🛠️',
            'AI_Security': '🤖',
            'SmartContract': '⛓️',
            'Security': '🛡️',
            'Test': '📝'
        };
        return <span className="text-7xl">{iconMap[workspace.name] || '📁'}</span>;
    };

    return (
        <div className="bg-[#0b0b11] rounded-lg overflow-hidden shadow-lg hover:shadow-xl transition-all border border-[#1a1b26] flex flex-col h-full">
            {/* Workspace Header - Horizontal Layout */}
            <div
                className="bg-gradient-to-r from-[#1a1b26] to-[#282a36] cursor-pointer relative group flex min-h-[140px] sm:h-[160px]"
                onClick={() => onToggle(workspace.name)}
            >
                {/* Logo Section */}
                <div className="w-28 sm:w-[160px] flex-shrink-0 bg-gradient-to-br from-[#282a36] to-[#1a1b26] border-r border-[#1a1b26] flex items-center justify-center group-hover:from-[#2a2c38] group-hover:to-[#1c1d28] transition-all overflow-hidden self-stretch">
                    <div className="w-full h-full flex items-center justify-center transition-transform duration-300 group-hover:scale-110">
                        {renderWorkspaceIcon(workspace)}
                    </div>
                </div>

                {/* Content Section - Right Side */}
                <div className="flex-1 px-3 sm:px-5 py-4 flex flex-col justify-between min-w-0">
                    {/* Top Section: Title & Edit */}
                    <div className="flex items-start justify-between gap-2 mb-2">
                        <div className="flex-1 min-w-0">
                            <h3 className="text-lg sm:text-xl font-black text-white truncate tracking-wide mb-2">
                                {workspace.name}
                            </h3>
                            <div className="flex items-center gap-2">
                                <span className="bg-[#1a1b26] px-2 py-1 rounded-md text-[#bd93f9] border border-[#bd93f9]/20 text-[10px] sm:text-xs font-bold uppercase tracking-wider whitespace-nowrap">
                                    {workspace.tool_count} {workspace.tool_count === 1 ? 'TOOL' : 'TOOLS'}
                                </span>
                            </div>
                        </div>
                        <Button
                            size="sm"
                            variant="ghost"
                            onClick={(e) => {
                                e.stopPropagation();
                                onEdit(workspace);
                            }}
                            className="h-8 w-8 p-0 text-[#6272a4] hover:text-[#8be9fd] hover:bg-[#8be9fd]/10 rounded-full flex-shrink-0"
                        >
                            <Edit size={16} />
                        </Button>
                    </div>

                    {/* Description */}
                    {workspace.description && (
                        <p className="text-xs sm:text-sm text-[#6272a4] line-clamp-2 leading-relaxed mb-3">
                            {workspace.description}
                        </p>
                    )}

                    {/* Bottom Section: Actions */}
                    <div className="flex items-center justify-between pt-3 border-t border-[#1a1b26]/50 gap-2">
                        <div className="flex items-center gap-1 sm:gap-2 text-xs text-[#6272a4] group-hover:text-[#f8f8f2] transition-colors whitespace-nowrap">
                            {isExpanded ?
                                <ChevronDown size={14} className="text-[#8be9fd] sm:w-4 sm:h-4" /> :
                                <ChevronRight size={14} className="sm:w-4 sm:h-4" />
                            }
                            <span className="font-bold tracking-wider text-[10px] sm:text-xs">VIEW</span>
                        </div>
                        <Button
                            size="sm"
                            onClick={(e) => {
                                e.stopPropagation();
                                onAddTool(workspace.name);
                            }}
                            variant="duolingoGreen"
                            className="h-7 sm:h-8 text-[10px] px-2 sm:px-3 font-black whitespace-nowrap flex-shrink-0"
                        >
                            <Plus size={12} className="mr-1" />
                            <span className="sm:hidden">ADD</span>
                            <span className="hidden sm:inline">ADD TOOL</span>
                        </Button>
                    </div>
                </div>
            </div>

            {/* Expanded Tools List (Children) */}
            {isExpanded && (
                <div className="p-4 space-y-2 flex-1 overflow-auto bg-[#0b0b11]/50 border-t border-[#1a1b26]">
                    {children}
                </div>
            )}
        </div>
    );
});

export default WorkspaceItem;
