import React from 'react';
import { Terminal, ArrowUpRight, Cpu } from 'lucide-react';
import { Card, CardTitle, CardDescription } from "@/components/ui/Card/Card";

import GlowImage from './GlowImage';

interface Tool {
    id: string;
    name: string;
    category: string;
    has_logo?: boolean;
}

interface ToolListProps {
    tools: Tool[];
    onSelectTool: (toolId: string) => void;
}

const ToolListItem = React.memo(({ tool, onSelect }: { tool: Tool; onSelect: (id: string) => void }) => {
    const [borderColor, setBorderColor] = React.useState<string>('transparent'); // Start transparent to avoid color flash

    return (
        <Card
            className="group transition-all duration-300 hover:-translate-y-1 cursor-pointer bg-[#0b0b11]/80 backdrop-blur-sm overflow-hidden h-48 flex flex-row border-2"
            onClick={() => onSelect(tool.id)}
            // glowColor="purple" // Removed to use custom dynamic glow
            style={{
                borderColor: borderColor,
                boxShadow: `0 0 15px ${borderColor}33, 0 0 30px ${borderColor}11`, // Dynamic glow
                transition: 'border-color 300ms, box-shadow 300ms, transform 300ms'
            }}
        >
            {/* Left Side - Full Height Logo */}
            <div
                className="w-48 h-full bg-[#16161e] flex items-center justify-center border-r transition-colors duration-300 p-2 relative flex-shrink-0"
                style={{
                    borderRightColor: borderColor
                }}
            >
                {tool.has_logo ? (
                    <GlowImage
                        src={`/api/tools/${tool.category}/${tool.id.includes('/') ? tool.id.split('/').pop() : tool.id}/logo`}
                        alt={tool.name}
                        className="w-full h-full object-contain drop-shadow-md group-hover:scale-110 transition-transform duration-300"
                        radius={10}
                        onColorDetected={(color) => setBorderColor(color)}
                    />
                ) : (
                    <div className="w-16 h-16 bg-dracula-current rounded-xl flex items-center justify-center border border-dracula-comment/20 group-hover:bg-dracula-purple group-hover:text-black transition-colors">
                        <Terminal size={32} />
                    </div>
                )}

                {/* Corner decoration */}
                <div className="absolute top-0 left-0 w-8 h-8 bg-gradient-to-br from-dracula-purple/20 to-transparent opacity-0 group-hover:opacity-100 transition-opacity" />
            </div>

            {/* Right Side - Content */}
            <div className="flex-1 flex flex-col justify-between p-4 min-w-0">
                <div>
                    <div className="flex justify-between items-start gap-2">
                        <CardTitle className="text-lg group-hover:text-dracula-purple transition-colors truncate">
                            {tool.name}
                        </CardTitle>
                        <ArrowUpRight size={18} className="text-dracula-comment group-hover:text-dracula-purple opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0" />
                    </div>
                    <CardDescription className="font-mono text-xs opacity-70 truncate mt-1">
                        {tool.id}
                    </CardDescription>
                </div>

                <div className="flex items-center gap-3">
                    <div className="flex items-center gap-1.5 px-2 py-0.5 rounded-full bg-dracula-current/50 border border-dracula-comment/20">
                        <Cpu size={10} className="text-dracula-cyan" />
                        <span className="text-[10px] text-gray-400 font-mono tracking-wide uppercase">Python</span>
                    </div>
                    <div className="flex items-center gap-1.5 ml-auto">
                        <span className="relative flex h-2 w-2">
                            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-dracula-green opacity-75"></span>
                            <span className="relative inline-flex rounded-full h-2 w-2 bg-dracula-green"></span>
                        </span>
                        <span className="text-[10px] text-dracula-green font-mono uppercase">Ready</span>
                    </div>
                </div>
            </div>
        </Card>
    );
});

const ToolList: React.FC<ToolListProps> = React.memo(({ tools, onSelectTool }) => {
    return (
        <div className="grid grid-cols-[repeat(auto-fill,minmax(320px,1fr))] gap-6 stagger-children">
            {tools.map((tool) => (
                <ToolListItem key={tool.id} tool={tool} onSelect={onSelectTool} />
            ))}
        </div>
    );
});

export default ToolList;
