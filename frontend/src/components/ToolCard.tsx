import React from 'react';
import { Edit, Trash2, Wrench } from 'lucide-react';
import { Button } from "@/components/ui/Button/Button";

interface Tool {
    id: string;
    name: string;
    category: string;
    has_logo?: boolean;
}

interface ToolCardProps {
    tool: Tool;
    onEdit: (category: string, toolId: string) => void;
    onDelete: (category: string, toolId: string) => void;
}

import GlowImage from './GlowImage';

const ToolCard: React.FC<ToolCardProps> = React.memo(({ tool, onEdit, onDelete }) => {
    return (
        <div
            className="bg-[#16161e] border border-[#282a36] hover:border-[#6272a4] rounded-xl p-0 transition-all group flex items-stretch h-40 overflow-hidden shadow-lg hover:shadow-cyan-500/10"
            style={{ isolation: 'isolate' }}
        >
            {/* Tool Logo/Icon - Isolated to contain glow effect */}
            <div
                className={`flex-shrink-0 w-40 h-full flex items-center justify-center relative overflow-hidden ${!tool.has_logo ? 'bg-[#0b0b11] border-r border-[#282a36]' : ''}`}
                style={{ isolation: 'isolate' }}
            >
                {tool.has_logo ? (
                    <GlowImage
                        src={`/api/tools/${tool.category}/${tool.id.includes('/') ? tool.id.split('/').pop() : tool.id}/logo`}
                        alt={tool.name}
                        className="w-full h-full p-0 object-contain transform transition-transform duration-500 group-hover:scale-110"
                        loading="lazy"
                    />
                ) : (
                    <Wrench size={48} className="text-[#6272a4] opacity-50" />
                )}
            </div>

            {/* Tool Info */}
            <div className="flex-1 min-w-0 p-4 flex flex-col justify-between bg-gradient-to-br from-transparent to-[#1a1b26]/30">
                <div className="min-w-0">
                    <h4 className="text-white font-black text-base group-hover:text-[#8be9fd] transition-colors leading-tight mb-1 uppercase tracking-tight">
                        {tool.name}
                    </h4>
                    <div className="text-[10px] text-[#6272a4] font-mono truncate opacity-60">
                        {tool.id}
                    </div>
                </div>

                <div className="flex justify-end gap-2 opacity-0 group-hover:opacity-100 transition-all transform translate-y-2 group-hover:translate-y-0">
                    <Button
                        size="sm"
                        variant="ghost"
                        onClick={(e) => {
                            e.stopPropagation();
                            onEdit(tool.category, tool.id);
                        }}
                        className="h-8 px-3 text-[#8be9fd] hover:bg-[#8be9fd]/10 bg-[#1e1e2e] border border-[#8be9fd]/20 rounded-md font-bold text-[10px] flex items-center gap-1.5"
                    >
                        <Edit size={12} />
                        EDIT
                    </Button>
                    <Button
                        size="sm"
                        variant="ghost"
                        onClick={(e) => {
                            e.stopPropagation();
                            onDelete(tool.category, tool.id);
                        }}
                        className="h-8 px-3 text-[#ff5555] hover:bg-[#ff5555]/10 bg-[#1e1e2e] border border-[#ff5555]/20 rounded-md font-bold text-[10px] flex items-center gap-1.5"
                    >
                        <Trash2 size={12} />
                        DELETE
                    </Button>
                </div>
            </div>
        </div>
    );
});

export default ToolCard;
