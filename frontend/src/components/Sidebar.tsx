import React, { useState, useMemo } from 'react';
import { Shield, LayoutGrid, Clock, Server, FolderOpen, ChevronLeft, ChevronRight, Settings, User } from 'lucide-react';
import { useAuth } from '../context/AuthContext';
import { useSidebarState } from '@/hooks/useSidebarState';
import { useVisibleWorkspaces } from '@/hooks/useVisibleWorkspaces';
import WorkspaceConfigDialog from './WorkspaceConfigDialog';
import GlowImage from './GlowImage';

interface Workspace {
    name: string;
    has_logo: boolean;
    tool_count: number;
    description: string;
}

interface SidebarProps {
    categories: Workspace[];
    selectedCategory: string | null;
    onSelectCategory: (category: string) => void;
}

const WORKSPACE_ICONS: Record<string, string> = {
    'Test': '🧪',
    'Cryptography': '🔐',
    'SmartContract': '📜',
    'DevSecOps': '⚙️',
    'Web': '🌐',
    'Binary': '💾',
    'Network': '🔌',
    'AI_Security': '🤖',
    'Mobile': '📱',
};

const getWorkspaceIcon = (name: string): string => {
    return WORKSPACE_ICONS[name] || '📁';
};

const getWorkspaceInitials = (name: string): string => {
    // Remove underscores e split por espaços ou camelCase
    const words = name
        .replace(/_/g, ' ')
        .split(/(?=[A-Z])|[\s-]+/)
        .filter(word => word.length > 0);

    if (words.length === 1) {
        // Se for uma palavra só, pega as 2 primeiras letras
        return words[0].substring(0, 2).toUpperCase();
    }

    // Se for múltiplas palavras, pega a primeira letra de cada
    return words
        .slice(0, 2)
        .map(word => word[0])
        .join('')
        .toUpperCase();
};

const getWorkspaceColor = (name: string): string => {
    // Paleta de cores vibrantes estilo Discord
    const colors = [
        '#50fa7b', // green
        '#8be9fd', // cyan
        '#bd93f9', // purple
        '#ff79c6', // pink
        '#ffb86c', // orange
        '#f1fa8c', // yellow
        '#ff5555', // red
        '#6272a4', // blue-gray
    ];

    // Gera um hash simples do nome
    let hash = 0;
    for (let i = 0; i < name.length; i++) {
        hash = name.charCodeAt(i) + ((hash << 5) - hash);
    }

    // Usa o hash para selecionar uma cor
    return colors[Math.abs(hash) % colors.length];
};

const AppSidebar: React.FC<SidebarProps> = ({ categories, selectedCategory, onSelectCategory }) => {
    const { user } = useAuth();
    const { isCollapsed, toggleSidebar } = useSidebarState();
    // usage of hook requires string names
    const workspaceNames = useMemo(() => categories.map(c => c.name), [categories]);
    const { visibleWorkspaces, toggleWorkspace, isVisible, showAll, hideAll } = useVisibleWorkspaces(categories);
    const [showConfigDialog, setShowConfigDialog] = useState(false);

    const visibleCategories = categories.filter(cat => isVisible(cat.name));

    return (
        <>
            <div className={`
                bg-[#0b0b11] border-r border-[#1a1b26] 
                flex flex-col h-full
                transition-all duration-300 ease-in-out
                ${isCollapsed ? 'w-[60px]' : 'w-[200px]'}
            `}>
                {/* Header */}
                <div className={`p-4 border-b border-[#1a1b26] flex items-center ${isCollapsed ? 'justify-center' : 'justify-between'}`}>
                    {!isCollapsed && (
                        <div className="flex items-center gap-2">
                            <div className="bg-[#bd93f9] p-1.5 rounded-lg">
                                <Shield className="text-black fill-current" size={16} />
                            </div>
                            <h1 className="text-xs font-black text-white tracking-widest uppercase">
                                Context<span className="text-[#bd93f9]">Works</span>
                            </h1>
                        </div>
                    )}
                    <button
                        onClick={toggleSidebar}
                        className="p-1.5 hover:bg-[#1a1b26] rounded transition-colors"
                        title={isCollapsed ? "Expand sidebar" : "Collapse sidebar"}
                    >
                        {isCollapsed ? (
                            <ChevronRight size={18} className="text-[#6272a4]" />
                        ) : (
                            <ChevronLeft size={18} className="text-[#6272a4]" />
                        )}
                    </button>
                </div>

                {/* Content */}
                <div className="flex-1 overflow-y-auto custom-scrollbar">
                    {/* Main Navigation */}
                    <div className="py-4">
                        {!isCollapsed && (
                            <div className="px-4 mb-2">
                                <span className="text-[#6272a4] text-[10px] font-mono uppercase tracking-wider">
                                    Dashboards
                                </span>
                            </div>
                        )}

                        <NavItem
                            icon={LayoutGrid}
                            label="Overview"
                            isActive={selectedCategory === null}
                            isCollapsed={isCollapsed}
                            onClick={() => onSelectCategory("overview")}
                        />
                        <NavItem
                            icon={Clock}
                            label="History"
                            isActive={selectedCategory === "history"}
                            isCollapsed={isCollapsed}
                            onClick={() => onSelectCategory("history")}
                        />
                        <NavItem
                            icon={FolderOpen}
                            label="Workspaces"
                            isActive={selectedCategory === "workspaces"}
                            isCollapsed={isCollapsed}
                            onClick={() => onSelectCategory("workspaces")}
                        />
                        <NavItem
                            icon={Server}
                            label="MCP Servers"
                            isActive={selectedCategory === "mcp-servers"}
                            isCollapsed={isCollapsed}
                            onClick={() => onSelectCategory("mcp-servers")}
                        />
                        <NavItem
                            icon={Settings}
                            label="Settings"
                            isActive={selectedCategory === "settings"}
                            isCollapsed={isCollapsed}
                            onClick={() => onSelectCategory("settings")}
                        />
                    </div>

                    {/* Workspaces Section */}
                    <div className="py-4 border-t border-[#1a1b26]">
                        {!isCollapsed && (
                            <div className="px-4 mb-2 flex items-center justify-between">
                                <span className="text-[#6272a4] text-[10px] font-mono uppercase tracking-wider">
                                    Workspaces
                                </span>
                                <button
                                    onClick={() => setShowConfigDialog(true)}
                                    className="p-1 hover:bg-[#1a1b26] rounded transition-colors"
                                    title="Configure workspaces"
                                >
                                    <Settings size={12} className="text-[#6272a4] hover:text-[#8be9fd]" />
                                </button>
                            </div>
                        )}

                        {visibleCategories.length === 0 && !isCollapsed && (
                            <div className="px-4 py-2 text-[#6272a4] text-xs text-center">
                                No workspaces visible
                            </div>
                        )}

                        {visibleCategories.map((workspace) => (
                            <WorkspaceItem
                                key={workspace.name}
                                workspace={workspace}
                                icon={getWorkspaceIcon(workspace.name)}
                                isActive={selectedCategory === workspace.name}
                                isCollapsed={isCollapsed}
                                onClick={() => onSelectCategory(workspace.name)}
                            />
                        ))}

                        {isCollapsed && categories.length > 0 && (
                            <button
                                onClick={() => setShowConfigDialog(true)}
                                className="w-full p-2 hover:bg-[#1a1b26] transition-colors flex justify-center"
                                title="Configure workspaces"
                            >
                                <Settings size={16} className="text-[#6272a4] hover:text-[#8be9fd]" />
                            </button>
                        )}
                    </div>
                </div>

                {/* Footer */}
                <div className="p-4 border-t border-[#1a1b26] space-y-4">
                    <button
                        onClick={() => window.location.href = '/profile'}
                        className={`w-full flex items-center gap-3 hover:bg-[#1a1b26] rounded-lg p-2 transition-colors ${isCollapsed ? 'justify-center' : ''}`}
                    >
                        <div className={`${isCollapsed ? 'w-10 h-10' : 'w-8 h-8'} rounded-lg bg-gradient-to-br from-[#50fa7b] to-[#8be9fd] flex items-center justify-center flex-shrink-0 transition-all`}>
                            <User size={isCollapsed ? 20 : 16} className="text-[#282a36]" />
                        </div>

                        {!isCollapsed && (
                            <div className="text-left overflow-hidden">
                                <p className="text-[#f8f8f2] text-xs font-bold truncate">{user?.email?.split('@')[0]}</p>
                                <p className="text-[#6272a4] text-[10px] truncate">{user?.email}</p>
                            </div>
                        )}
                    </button>
                </div>
            </div>

            {/* Config Dialog */}
            {showConfigDialog && (
                <WorkspaceConfigDialog
                    workspaces={workspaceNames}
                    visibleWorkspaces={visibleWorkspaces}
                    onToggle={toggleWorkspace}
                    onShowAll={showAll}
                    onHideAll={hideAll}
                    onClose={() => setShowConfigDialog(false)}
                />
            )}
        </>
    );
};

// Helper Components
interface NavItemProps {
    icon: React.ComponentType<{ size?: number; className?: string }>;
    label: string;
    isActive: boolean;
    isCollapsed: boolean;
    onClick: () => void;
}

const NavItem: React.FC<NavItemProps> = ({ icon: Icon, label, isActive, isCollapsed, onClick }) => {
    return (
        <button
            onClick={onClick}
            className={`
                w-full px-4 py-2 flex items-center gap-3
                transition-all cursor-pointer
                ${isCollapsed ? 'justify-center' : 'justify-start'}
                ${isActive
                    ? 'bg-[#8be9fd]/20 text-[#8be9fd] border-l-2 border-[#8be9fd]'
                    : 'text-[#6272a4] hover:bg-[#1a1b26] hover:text-white border-l-2 border-transparent'
                }
            `}
            title={isCollapsed ? label : undefined}
        >
            <Icon size={isCollapsed ? 24 : 18} />
            {!isCollapsed && (
                <span className="text-sm font-mono">{label}</span>
            )}
        </button>
    );
};

interface WorkspaceItemProps {
    workspace: Workspace;
    icon: string;
    isActive: boolean;
    isCollapsed: boolean;
    onClick: () => void;
}

const WorkspaceItem: React.FC<WorkspaceItemProps> = ({ workspace, icon, isActive, isCollapsed, onClick }) => {
    const initials = getWorkspaceInitials(workspace.name);
    const color = getWorkspaceColor(workspace.name);

    return (
        <button
            onClick={onClick}
            className={`
                w-full px-4 py-2 flex items-center gap-3
                transition-all cursor-pointer
                ${isCollapsed ? 'justify-center' : 'justify-start'}
                ${isActive
                    ? 'bg-[#8be9fd]/20 text-[#8be9fd] border-l-2 border-[#8be9fd]'
                    : 'text-[#6272a4] hover:bg-[#1a1b26] hover:text-white border-l-2 border-transparent'
                }
            `}
            title={isCollapsed ? workspace.name : undefined}
        >
            {isCollapsed ? (
                // Quando retraída: mostrar iniciais em círculo com cor única
                <div
                    className={`
                        w-10 h-10 rounded-full flex items-center justify-center font-black text-xs
                        transition-all
                        ${isActive
                            ? 'text-[#0b0b11]'
                            : 'bg-[#1a1b26] text-[#6272a4] hover:text-[#0b0b11]'
                        }
                    `}
                    style={{
                        backgroundColor: isActive ? color : undefined,
                    }}
                    onMouseEnter={(e) => {
                        if (!isActive) {
                            e.currentTarget.style.backgroundColor = color;
                        }
                    }}
                    onMouseLeave={(e) => {
                        if (!isActive) {
                            e.currentTarget.style.backgroundColor = '';
                        }
                    }}
                >
                    {initials}
                </div>
            ) : (
                // Quando expandida: mostrar logo ou ícone + nome
                <>
                    {workspace.has_logo ? (
                        <GlowImage
                            src={`/api/workspaces/${workspace.name}/logo`}
                            alt={workspace.name}
                            className="w-6 h-6 object-contain flex-shrink-0"
                            radius={4}
                        />
                    ) : (
                        <span className="text-base">{icon}</span>
                    )}
                    <span className="text-sm font-mono truncate">{workspace.name}</span>
                </>
            )}
        </button>
    );
};

export default AppSidebar;
