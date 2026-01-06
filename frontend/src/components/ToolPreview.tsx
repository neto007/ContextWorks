import React, { useState } from 'react';
import { FileCode, Settings, Package, Server, Code, Eye } from 'lucide-react';
import type { Argument } from './ArgumentsBuilder';

interface ToolPreviewProps {
    toolName: string;
    description: string;
    arguments: Argument[];
    dockerConfig?: {
        mode?: string;
        baseImage?: string;
        aptPackages?: string;
        pipPackages?: string;
    };
}

const ToolPreview: React.FC<ToolPreviewProps> = ({
    toolName,
    description,
    arguments: args,
    dockerConfig
}) => {
    const [activeView, setActiveView] = useState<'visual' | 'yaml'>('visual');

    const generateYAML = () => {
        const yamlObj: any = {
            name: toolName || 'Untitled Tool',
            description: description || 'No description provided',
        };

        if (args.length > 0) {
            yamlObj.arguments = args.map(arg => ({
                name: arg.name,
                type: arg.type,
                description: arg.description,
                required: arg.required,
                ...(arg.default && { default: arg.default })
            }));
        }

        if (dockerConfig) {
            yamlObj.docker = {
                ...(dockerConfig.baseImage && { base_image: dockerConfig.baseImage }),
                ...(dockerConfig.aptPackages && { apt_packages: dockerConfig.aptPackages.split(',').map(p => p.trim()) }),
                ...(dockerConfig.pipPackages && { pip_packages: dockerConfig.pipPackages.split(',').map(p => p.trim()) })
            };
        }

        return JSON.stringify(yamlObj, null, 2);
    };

    const isVisual = activeView === 'visual';
    const isYAML = activeView === 'yaml';

    return (
        <div className="space-y-4">
            {/* View Toggle */}
            <div className="flex gap-2 border-b border-[#282a36] pb-2">
                <button
                    onClick={() => setActiveView('visual')}
                    className={isVisual
                        ? 'flex items-center gap-2 px-4 py-2 rounded-t font-mono text-sm transition-all bg-gradient-to-b from-[#8be9fd]/20 to-transparent text-[#8be9fd] border-b-2 border-[#8be9fd]'
                        : 'flex items-center gap-2 px-4 py-2 rounded-t font-mono text-sm transition-all text-[#6272a4] hover:text-white hover:bg-[#282a36]/50'
                    }
                >
                    <Eye size={16} />
                    Visual Preview
                </button>
                <button
                    onClick={() => setActiveView('yaml')}
                    className={isYAML
                        ? 'flex items-center gap-2 px-4 py-2 rounded-t font-mono text-sm transition-all bg-gradient-to-b from-[#50fa7b]/20 to-transparent text-[#50fa7b] border-b-2 border-[#50fa7b]'
                        : 'flex items-center gap-2 px-4 py-2 rounded-t font-mono text-sm transition-all text-[#6272a4] hover:text-white hover:bg-[#282a36]/50'
                    }
                >
                    <Code size={16} />
                    Generated YAML
                </button>
            </div>

            {isVisual ? (
                <div className="space-y-4">
                    {/* Metadata Section */}
                    <div className="bg-gradient-to-br from-[#1a1b26] to-[#0b0b11] rounded-lg p-5 border-2 border-[#8be9fd]/30 shadow-lg">
                        <div className="flex items-center gap-2 mb-4">
                            <Settings size={18} className="text-[#8be9fd]" />
                            <h3 className="text-lg font-bold text-white uppercase tracking-wide">Metadata</h3>
                        </div>
                        <div className="space-y-3">
                            <div>
                                <div className="text-xs font-mono text-[#6272a4] uppercase mb-1">Tool Name</div>
                                <div className="text-white font-semibold text-lg">
                                    {toolName || <span className="text-[#6272a4] italic">Untitled</span>}
                                </div>
                            </div>
                            <div>
                                <div className="text-xs font-mono text-[#6272a4] uppercase mb-1">Description</div>
                                <div className="text-[#f8f8f2]">
                                    {description || <span className="text-[#6272a4] italic">No description</span>}
                                </div>
                            </div>
                        </div>
                    </div>

                    {/* Arguments Section */}
                    {args.length > 0 && (
                        <div className="bg-gradient-to-br from-[#1a1b26] to-[#0b0b11] rounded-lg p-5 border-2 border-[#bd93f9]/30 shadow-lg">
                            <div className="flex items-center gap-2 mb-4">
                                <FileCode size={18} className="text-[#bd93f9]" />
                                <h3 className="text-lg font-bold text-white uppercase tracking-wide">Arguments</h3>
                                <span className="text-xs bg-[#bd93f9]/20 text-[#bd93f9] px-2 py-1 rounded-full font-mono">{args.length}</span>
                            </div>
                            <div className="space-y-3">
                                {args.map((arg, idx) => (
                                    <div key={idx} className="bg-[#0b0b11] rounded-lg p-4 border border-[#282a36]">
                                        <div className="flex items-start justify-between mb-2">
                                            <div className="flex items-baseline gap-2">
                                                <span className="font-mono font-bold text-white">
                                                    {arg.name || <span className="text-[#6272a4] italic">unnamed</span>}
                                                </span>
                                                <span className="text-xs bg-[#44475a] text-[#f8f8f2] px-2 py-0.5 rounded font-mono">{arg.type}</span>
                                                {arg.required && (
                                                    <span className="text-xs bg-[#ff5555]/20 text-[#ff5555] px-2 py-0.5 rounded font-mono">REQUIRED</span>
                                                )}
                                            </div>
                                        </div>
                                        <div className="text-sm text-[#6272a4] mb-2">
                                            {arg.description || <span className="italic">No description</span>}
                                        </div>
                                        {arg.default && (
                                            <div className="flex items-center gap-2 text-xs">
                                                <span className="text-[#6272a4]">Default:</span>
                                                <span className="font-mono bg-[#282a36] px-2 py-1 rounded text-[#50fa7b]">{arg.default}</span>
                                            </div>
                                        )}
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}

                    {/* Docker Configuration */}
                    {dockerConfig && (dockerConfig.baseImage || dockerConfig.aptPackages || dockerConfig.pipPackages) && (
                        <div className="bg-gradient-to-br from-[#1a1b26] to-[#0b0b11] rounded-lg p-5 border-2 border-[#50fa7b]/30 shadow-lg">
                            <div className="flex items-center gap-2 mb-4">
                                <Server size={18} className="text-[#50fa7b]" />
                                <h3 className="text-lg font-bold text-white uppercase tracking-wide">Docker Configuration</h3>
                            </div>
                            <div className="space-y-3">
                                {dockerConfig.baseImage && (
                                    <div>
                                        <div className="text-xs font-mono text-[#6272a4] uppercase mb-1">Base Image</div>
                                        <div className="font-mono bg-[#0b0b11] px-3 py-2 rounded border border-[#282a36] text-[#50fa7b]">{dockerConfig.baseImage}</div>
                                    </div>
                                )}
                                {dockerConfig.aptPackages && (
                                    <div>
                                        <div className="text-xs font-mono text-[#6272a4] uppercase mb-2">APT Packages</div>
                                        <div className="flex flex-wrap gap-2">
                                            {dockerConfig.aptPackages.split(',').map((pkg, idx) => (
                                                <span key={idx} className="inline-flex items-center gap-1 bg-[#ffb86c]/20 text-[#ffb86c] px-2 py-1 rounded text-xs font-mono">
                                                    <Package size={12} />
                                                    {pkg.trim()}
                                                </span>
                                            ))}
                                        </div>
                                    </div>
                                )}
                                {dockerConfig.pipPackages && (
                                    <div>
                                        <div className="text-xs font-mono text-[#6272a4] uppercase mb-2">PIP Packages</div>
                                        <div className="flex flex-wrap gap-2">
                                            {dockerConfig.pipPackages.split(',').map((pkg, idx) => (
                                                <span key={idx} className="inline-flex items-center gap-1 bg-[#8be9fd]/20 text-[#8be9fd] px-2 py-1 rounded text-xs font-mono">
                                                    <Package size={12} />
                                                    {pkg.trim()}
                                                </span>
                                            ))}
                                        </div>
                                    </div>
                                )}
                            </div>
                        </div>
                    )}
                </div>
            ) : (
                <div className="bg-[#0b0b11] rounded-lg border-2 border-[#50fa7b]/30 overflow-hidden">
                    <div className="bg-gradient-to-r from-[#1a1b26] to-[#282a36] px-4 py-2 border-b border-[#50fa7b]/30">
                        <span className="font-mono text-sm text-[#50fa7b]">tool_config.yaml</span>
                    </div>
                    <pre className="p-6 overflow-auto max-h-96 custom-scrollbar">
                        <code className="text-sm font-mono text-[#f8f8f2] leading-relaxed">
                            {generateYAML()}
                        </code>
                    </pre>
                </div>
            )}
        </div>
    );
};

export default ToolPreview;
