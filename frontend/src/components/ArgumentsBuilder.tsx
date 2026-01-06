import React from 'react';
import { Plus, Trash2, Type, Hash, ToggleLeft, FileText } from 'lucide-react';
import { Button } from "@/components/ui/Button/Button";

export interface Argument {
    name: string;
    type: 'str' | 'int' | 'bool' | 'file';
    description: string;
    required: boolean;
    default?: string;
}

interface ArgumentsBuilderProps {
    arguments: Argument[];
    onChange: (args: Argument[]) => void;
}

const ArgumentsBuilder: React.FC<ArgumentsBuilderProps> = ({ arguments: args, onChange }) => {
    const addArgument = () => {
        onChange([
            ...args,
            { name: '', type: 'str', description: '', required: false }
        ]);
    };

    const updateArgument = (index: number, field: keyof Argument, value: any) => {
        const updated = [...args];
        updated[index] = { ...updated[index], [field]: value };
        onChange(updated);
    };

    const removeArgument = (index: number) => {
        onChange(args.filter((_, i) => i !== index));
    };

    return (
        <div className="space-y-3">
            <div className="flex justify-between items-center mb-1">
                <h4 className="text-sm font-semibold text-white uppercase tracking-wider">Arguments</h4>
                <Button
                    size="sm"
                    onClick={addArgument}
                    className="bg-[#50fa7b] hover:bg-[#50fa7b]/90 text-[#050101] font-bold gap-1.5 h-8 px-3 text-xs"
                >
                    <Plus size={14} />
                    ADD ARGUMENT
                </Button>
            </div>

            {args.length === 0 ? (
                <div className="text-center py-12 text-[#6272a4] text-sm border-2 border-dashed border-[#6272a4]/30 rounded-lg bg-[#0b0b11]/30">
                    <FileText size={32} className="mx-auto mb-2 opacity-50" />
                    <p className="font-medium">No arguments defined</p>
                    <p className="text-xs mt-1 opacity-70">Click "ADD ARGUMENT" to create one</p>
                </div>
            ) : (
                <div className="space-y-4">
                    {args.map((arg, index) => (
                        <div
                            key={index}
                            className="bg-gradient-to-br from-[#1a1b26] to-[#0b0b11] rounded-lg p-4 border-2 border-[#282a36] hover:border-[#44475a] transition-all shadow-lg"
                        >
                            <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                                <div>
                                    <label className="flex items-center gap-2 text-sm font-medium text-[#8be9fd] mb-2">
                                        <Type size={14} />
                                        NAME *
                                    </label>
                                    <input
                                        type="text"
                                        value={arg.name}
                                        onChange={(e) => updateArgument(index, 'name', e.target.value)}
                                        className="w-full bg-[#0b0b11] border-2 border-[#282a36] rounded-lg px-3 py-2.5 text-white font-mono text-sm focus:outline-none focus:border-[#8be9fd] focus:ring-2 focus:ring-[#8be9fd]/20 transition-all"
                                        placeholder="target"
                                    />
                                </div>
                                <div>
                                    <label className="flex items-center gap-2 text-sm font-medium text-[#bd93f9] mb-2">
                                        {arg.type === 'str' && <Type size={14} />}
                                        {arg.type === 'int' && <Hash size={14} />}
                                        {arg.type === 'bool' && <ToggleLeft size={14} />}
                                        {arg.type === 'file' && <FileText size={14} />}
                                        TYPE
                                    </label>
                                    <select
                                        value={arg.type}
                                        onChange={(e) => updateArgument(index, 'type', e.target.value)}
                                        className="w-full bg-[#0b0b11] border-2 border-[#282a36] rounded-lg px-3 py-2.5 text-white font-mono text-sm focus:outline-none focus:border-[#bd93f9] focus:ring-2 focus:ring-[#bd93f9]/20 transition-all"
                                    >
                                        <option value="str">String</option>
                                        <option value="int">Integer</option>
                                        <option value="bool">Boolean</option>
                                        <option value="file">File</option>
                                    </select>
                                </div>
                            </div>

                            <div className="mb-4">
                                <label className="block text-sm font-medium text-[#ffb86c] mb-2">
                                    DESCRIPTION
                                </label>
                                <input
                                    type="text"
                                    value={arg.description}
                                    onChange={(e) => updateArgument(index, 'description', e.target.value)}
                                    className="w-full bg-[#0b0b11] border-2 border-[#282a36] rounded-lg px-3 py-2.5 text-white text-sm focus:outline-none focus:border-[#ffb86c] focus:ring-2 focus:ring-[#ffb86c]/20 transition-all"
                                    placeholder="Target host or IP address"
                                />
                            </div>

                            <div className="flex items-center justify-between gap-3">
                                <div className="flex-1">
                                    <label className="block text-sm font-medium text-[#50fa7b] mb-2">
                                        DEFAULT VALUE
                                    </label>
                                    <input
                                        type="text"
                                        value={arg.default || ''}
                                        onChange={(e) => updateArgument(index, 'default', e.target.value)}
                                        className="w-full bg-[#0b0b11] border-2 border-[#282a36] rounded-lg px-3 py-2.5 text-white text-sm focus:outline-none focus:border-[#50fa7b] focus:ring-2 focus:ring-[#50fa7b]/20 transition-all"
                                        placeholder="Optional"
                                    />
                                </div>
                                <div className="flex items-end gap-2">
                                    <label className="flex items-center gap-2 px-3 py-2 bg-[#0b0b11] border-2 border-[#282a36] rounded-lg cursor-pointer hover:border-[#8be9fd] transition-all">
                                        <input
                                            type="checkbox"
                                            checked={arg.required}
                                            onChange={(e) => updateArgument(index, 'required', e.target.checked)}
                                            className="w-4 h-4 rounded border-[#282a36] bg-[#0b0b11] text-[#8be9fd] focus:ring-[#8be9fd]"
                                        />
                                        <span className="text-sm font-semibold text-white whitespace-nowrap">Required</span>
                                    </label>
                                    <Button
                                        size="sm"
                                        variant="ghost"
                                        onClick={() => removeArgument(index)}
                                        className="h-10 w-10 p-0 text-[#ff5555] hover:bg-[#ff5555]/20 border-2 border-[#ff5555]/30 hover:border-[#ff5555] transition-all"
                                    >
                                        <Trash2 size={16} />
                                    </Button>
                                </div>
                            </div>
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
};

export default ArgumentsBuilder;
