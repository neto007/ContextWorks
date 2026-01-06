import React, { useState, useEffect } from 'react';
import { Play, Code, Terminal, AlertCircle, Clock, ArrowLeft } from 'lucide-react';
import CodeEditor from './CodeEditor';
import { Button } from "@/components/ui/Button/Button";
import GlowImage from './GlowImage';
import { useExecution } from '../hooks/useExecution';
import ExecutionLogs from './ExecutionLogs';
import ExecutionHistory from './ExecutionHistory';
import type { Argument } from '../types/tool';

interface ToolDetails {
    id: string;
    full_id: string;
    name: string;
    path: string;
    description: string;
    arguments: Argument[];
    has_logo?: boolean;
}

interface ToolRunnerProps {
    tool: ToolDetails;
    onBack: () => void;
}

const ToolRunner: React.FC<ToolRunnerProps> = ({ tool, onBack }) => {
    const [activeTab, setActiveTab] = useState<'run' | 'code' | 'history'>('run');
    const [outputTab, setOutputTab] = useState<'output' | 'logs'>('output');
    const [formValues, setFormValues] = useState<Record<string, any>>({});

    const {
        executing,
        executionId,
        output,
        setOutput,
        setExecutionId,
        runTool,
        followExecution,
        stopTool,
        setExecuting
    } = useExecution();

    useEffect(() => {
        const defaults: Record<string, any> = {};
        tool.arguments?.forEach(arg => {
            if (arg.default !== undefined) {
                defaults[arg.name] = arg.default;
            } else if (arg.type === 'bool') {
                defaults[arg.name] = false;
            } else {
                defaults[arg.name] = '';
            }
        });
        setFormValues(defaults);

        // Only reset execution state if we don't have an active execution 
        // OR if the tool itself has changed.
        if (!executing) {
            setExecutionId(null);
            setOutput(null);
            setExecuting(false);
        }
    }, [tool.full_id, setExecutionId, setOutput, setExecuting]); // Use tool.full_id here

    const handleRun = async () => {
        setOutputTab('logs');
        await runTool(tool.full_id, tool.path, formValues);
    };

    const handleHistoryRestore = (execution: any) => {
        setActiveTab('run');
        setOutputTab('logs');

        // Populate the execution state with data from history
        setExecutionId(execution.id);
        const isRunning = execution.status === 'running';
        setExecuting(isRunning);
        setOutput({
            result: execution.result || "",
            logs: execution.logs || "",
            exitCode: execution.status === 'success' ? 0 : (execution.status === 'failed' ? 1 : undefined)
        });

        // If it's still running, re-attach to the live log stream
        if (isRunning) {
            followExecution(tool.full_id, tool.path, execution.id);
        }
    };

    return (
        <div className="flex flex-col h-full bg-[#0b0b11]">
            {/* Header */}
            <div className="flex items-center justify-between p-6 border-b border-[#1a1b26] bg-[#0b0b11]/80 backdrop-blur-md sticky top-0 z-10">
                <div className="flex items-center gap-6">
                    <button
                        onClick={onBack}
                        className="text-[#6272a4] hover:text-white transition-colors"
                    >
                        <ArrowLeft size={20} />
                    </button>
                    <div className="flex items-center gap-4">
                        <div className="flex items-center justify-center -ml-4">
                            {tool.has_logo ? (
                                <GlowImage
                                    src={`/api/tools/${tool.full_id}/logo`}
                                    alt={tool.name}
                                    className="w-32 h-32 object-contain drop-shadow-[0_0_15px_rgba(0,0,0,0.5)]"
                                />
                            ) : (
                                <div className="w-16 h-16 bg-[#1a1b26] rounded-2xl flex items-center justify-center border border-[#282a36] shadow-xl">
                                    <Terminal size={32} className="text-[#8be9fd]" />
                                </div>
                            )}
                        </div>
                        <div>
                            <h2 className="text-xl font-bold text-white tracking-tight">{tool.name}</h2>
                            <p className="text-sm text-[#6272a4] font-mono">{tool.full_id}</p>
                        </div>
                    </div>
                </div>

                <div className="flex items-center gap-2 bg-[#1a1b26] p-1 rounded-lg border border-[#282a36]">
                    <TabButton
                        active={activeTab === 'run'}
                        onClick={() => setActiveTab('run')}
                        icon={
                            <div className="relative">
                                <Play size={16} />
                                {executing && (
                                    <span className="absolute -top-1 -right-1 w-2 h-2 bg-[#50fa7b] rounded-full animate-ping" />
                                )}
                            </div>
                        }
                        label="Run"
                        color="#50fa7b"
                    />
                    <TabButton
                        active={activeTab === 'code'}
                        onClick={() => setActiveTab('code')}
                        icon={<Code size={16} />}
                        label="Code"
                        color="#bd93f9"
                    />
                    <TabButton
                        active={activeTab === 'history'}
                        onClick={() => setActiveTab('history')}
                        icon={<div className="relative">
                            <Clock size={16} />
                            {executing && (
                                <span className="absolute -top-1 -right-1 w-2 h-2 bg-[#bd93f9] rounded-full animate-pulse" />
                            )}
                        </div>}
                        label="History"
                        color="#ffb86c"
                    />
                </div>
            </div>

            <div className="flex-1 flex overflow-hidden">
                {/* Left Panel: Inputs */}
                {activeTab === 'run' && (
                    <div className="w-[450px] border-r border-[#1a1b26] flex flex-col bg-[#0b0b11]">
                        <div className="p-6 border-b border-[#1a1b26]">
                            <div className="flex justify-between items-start mb-1">
                                <h3 className="text-sm font-bold uppercase tracking-wider text-[#8be9fd]">Configuration</h3>
                                {executionId && (
                                    <span className="text-[10px] font-mono bg-[#bd93f9]/20 text-[#bd93f9] px-2 py-0.5 rounded border border-[#bd93f9]/30">
                                        ID: {executionId.slice(0, 8)}
                                    </span>
                                )}
                            </div>
                            <p className="text-xs text-[#6272a4] leading-relaxed">{tool.description || 'No description provided'}</p>
                        </div>

                        <div className="flex-1 overflow-y-auto custom-scrollbar p-6">
                            {(!tool.arguments || tool.arguments.length === 0) ? (
                                <div className="flex items-center gap-2 p-4 bg-[#1a1b26] rounded text-[#6272a4] text-sm">
                                    <AlertCircle size={16} /> No arguments required
                                </div>
                            ) : (
                                <div className="space-y-5">
                                    {tool.arguments.map((arg) => (
                                        <div key={arg.name}>
                                            <label className="block text-xs font-bold uppercase tracking-wider text-[#6272a4] mb-2">
                                                {arg.name} {arg.required && <span className="text-[#ff5555]">*</span>}
                                            </label>
                                            {arg.type === 'bool' ? (
                                                <button
                                                    onClick={() => setFormValues({ ...formValues, [arg.name]: !formValues[arg.name] })}
                                                    className={`w-12 h-6 rounded-full transition-colors relative ${formValues[arg.name] ? 'bg-[#50fa7b]' : 'bg-[#44475a]'}`}
                                                >
                                                    <span className={`absolute left-1 top-1 w-4 h-4 rounded-full bg-white transition-transform ${formValues[arg.name] ? 'translate-x-6' : 'translate-x-0'}`} />
                                                </button>
                                            ) : (
                                                <input
                                                    type="text"
                                                    value={formValues[arg.name] || ''}
                                                    onChange={(e) => setFormValues(prev => ({ ...prev, [arg.name]: e.target.value }))}
                                                    className="w-full bg-[#1a1b26] text-white rounded px-4 py-3 focus:outline-none focus:ring-1 focus:ring-[#bd93f9] transition-all placeholder-[#6272a4] text-sm font-mono"
                                                    placeholder={arg.description}
                                                />
                                            )}
                                            <p className="text-[10px] text-[#6272a4] mt-1.5">{arg.description}</p>
                                        </div>
                                    ))}
                                </div>
                            )}
                        </div>

                        <div className="p-6 pt-0">
                            <Button
                                onClick={executing ? () => stopTool(executionId || '') : handleRun}
                                className={`w-full py-6 font-black text-lg rounded-xl shadow-lg transition-all transform active:scale-[0.98] flex items-center justify-center gap-3 uppercase tracking-wider ${executing
                                    ? 'bg-[#ff5555] hover:bg-[#ff5555] text-white shadow-[#ff5555]/20 border-b-4 border-[#cc4444] hover:border-[#cc4444] active:border-b-0 active:translate-y-1'
                                    : 'bg-[#50fa7b] hover:bg-[#50fa7b] text-[#050101] shadow-[#50fa7b]/20 border-b-4 border-[#3ec95f] hover:border-[#3ec95f] active:border-b-0 active:translate-y-1'
                                    }`}
                            >
                                {executing ? (
                                    <>
                                        <div className="w-2 h-2 bg-white rounded-full animate-ping" />
                                        Stop Execution
                                    </>
                                ) : (
                                    <>
                                        <Play size={20} fill="currentColor" />
                                        Execute Tool
                                    </>
                                )}
                            </Button>
                        </div>
                    </div>
                )}

                {/* Main Content: Output / Code / History */}
                <div className="flex-1 flex flex-col bg-[#16161e]/30 overflow-hidden">
                    {activeTab === 'run' && (
                        <>
                            <div className="flex border-b border-[#1a1b26] bg-[#0b0b11]/50">
                                <button
                                    onClick={() => setOutputTab('output')}
                                    className={`px-6 py-3 text-xs font-bold uppercase tracking-widest transition-all border-b-2 ${outputTab === 'output' ? 'text-[#8be9fd] border-[#8be9fd] bg-[#8be9fd]/5' : 'text-[#6272a4] border-transparent hover:text-white'}`}
                                >
                                    Result
                                </button>
                                <button
                                    onClick={() => setOutputTab('logs')}
                                    className={`px-6 py-3 text-xs font-bold uppercase tracking-widest transition-all border-b-2 ${outputTab === 'logs' ? 'text-[#ff79c6] border-[#ff79c6] bg-[#ff79c6]/5' : 'text-[#6272a4] border-transparent hover:text-white'}`}
                                >
                                    Real-time Logs
                                </button>
                            </div>

                            <div className="flex-1 overflow-hidden relative">
                                {outputTab === 'output' ? (
                                    <div className="h-full overflow-auto p-6 custom-scrollbar font-mono text-sm">
                                        {output ? (
                                            <div className="animate-in fade-in slide-in-from-bottom-2 duration-300">
                                                {output.result ? (
                                                    <pre className="text-[#50fa7b] whitespace-pre-wrap leading-relaxed">
                                                        {typeof output.result === 'string' ? output.result : JSON.stringify(output.result, null, 2)}
                                                    </pre>
                                                ) : executing ? (
                                                    <div className="flex flex-col items-center justify-center h-48 gap-4 text-[#6272a4]">
                                                        <div className="w-12 h-12 border-4 border-[#bd93f9]/20 border-t-[#bd93f9] rounded-full animate-spin" />
                                                        <p className="animate-pulse">Executing... waiting for output</p>
                                                    </div>
                                                ) : (
                                                    <div className="text-[#6272a4] italic">No result produced by this execution.</div>
                                                )}
                                            </div>
                                        ) : executing ? (
                                            <div className="flex flex-col items-center justify-center h-full gap-4 text-[#6272a4]">
                                                <div className="w-12 h-12 border-4 border-[#bd93f9]/20 border-t-[#bd93f9] rounded-full animate-spin" />
                                                <p className="animate-pulse">Waiting for result...</p>
                                            </div>
                                        ) : (
                                            <div className="flex flex-col items-center justify-center h-full text-[#6272a4] opacity-50">
                                                <Terminal size={48} className="mb-4" />
                                                <p>Execute the tool to see results</p>
                                            </div>
                                        )}
                                    </div>
                                ) : (
                                    <ExecutionLogs logs={output?.logs || ""} />
                                )}
                            </div>
                        </>
                    )}

                    {activeTab === 'code' && (
                        <div className="flex-1 overflow-hidden flex flex-col">
                            <CodeEditor
                                toolId={tool.full_id}
                                filePath={tool.path}
                            />
                        </div>
                    )}

                    {activeTab === 'history' && (
                        <div className="flex-1 overflow-hidden">
                            <ExecutionHistory
                                toolPath={tool.path}
                                onHistoryRestore={handleHistoryRestore}
                            />
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

interface TabButtonProps {
    active: boolean;
    onClick: () => void;
    icon: React.ReactNode;
    label: string;
    color: string;
}

const TabButton: React.FC<TabButtonProps> = ({ active, onClick, icon, label, color }) => (
    <button
        onClick={onClick}
        className={`pb-3 px-1 text-sm font-bold uppercase tracking-wider transition-all relative ${active ? 'text-[white]' : 'text-[#6272a4] hover:text-white'}`}
        style={{ color: active ? color : undefined } as any}
    >
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-md transition-colors hover:bg-white/5">
            {icon}
            {label}
        </div>
        {active && (
            <div
                className="absolute bottom-0 left-0 right-0 h-0.5 rounded-full shadow-[0_0_10px_rgba(0,0,0,0.5)]"
                style={{ backgroundColor: color }}
            />
        )}
    </button>
);

export default ToolRunner;
