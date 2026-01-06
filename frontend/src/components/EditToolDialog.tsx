import React, { useState, useEffect, useCallback } from 'react';
import { Settings, Code, Layers, Shield, Play, Save, X, Eye, ListTree } from 'lucide-react';
import { Button } from "@/components/ui/Button/Button";
import { useToast } from './Toast';
import { toolService } from '../services/toolService';
import { useToolForm } from '../hooks/useToolForm';
import DockerConfigSection from './DockerConfigSection';
import ScriptEditorSection from './ScriptEditorSection';
import TestToolDialog from './TestToolDialog';
import { BuildProgress } from './BuildProgress';
import { generateYAML, getCodePreview } from '../lib/preview-utils';
import type { Argument } from '../types/tool';
import ArgumentsBuilder from './ArgumentsBuilder';
import LogoUploader from './LogoUploader';

interface EditToolDialogProps {
    workspace: string;
    toolId: string;
    onClose: () => void;
    onSuccess: () => void;
}

const EditToolDialog: React.FC<EditToolDialogProps> = ({ workspace, toolId, onClose, onSuccess }) => {
    const [activeTab, setActiveTab] = useState<'metadata' | 'script' | 'arguments' | 'docker' | 'preview'>('metadata');
    const [showTestDialog, setShowTestDialog] = useState(false);
    const [buildJobId, setBuildJobId] = useState<string | null>(null);
    const [showBuildProgress, setShowBuildProgress] = useState(false);

    const [isInitLoading, setIsInitLoading] = useState(true);
    const hasLoaded = React.useRef(false);

    const {
        toolName, setToolName,
        description, setDescription,
        scriptCode, setScriptCode,
        arguments_, setArguments,
        submitting, loading, setLoading,
        validation,
        logoSVG, setLogoSVG,
        dockerMode, setDockerMode,
        preexistingImage, setPreexistingImage,
        baseImage, setBaseImage,
        aptPackages, setAptPackages,
        pipPackages, setPipPackages,
        cpuRequest, setCpuRequest,
        cpuLimit, setCpuLimit,
        memoryRequest, setMemoryRequest,
        memoryLimit, setMemoryLimit,
        populateFromTool,
        submitTool
    } = useToolForm();

    const { error: toastError, success: toastSuccess } = useToast();

    const loadData = useCallback(async (isMounted: boolean) => {
        // Prevent double loading if already done
        if (hasLoaded.current && !isInitLoading) return;

        setIsInitLoading(true);
        try {
            const parts = toolId.split('/');
            const cat = parts.length > 1 ? parts[0] : workspace;
            const name = parts.length > 1 ? parts[1] : toolId;

            const data = await toolService.getToolById(cat, name);
            if (!isMounted) return;

            populateFromTool(data);

            const logo = await toolService.getLogo(cat, name);
            if (isMounted) {
                if (logo) {
                    setLogoSVG(logo);
                } else {
                    setLogoSVG(null);
                }
            }
        } catch (err) {
            if (isMounted) toastError('Failed to load tool data');
        } finally {
            if (isMounted) {
                setIsInitLoading(false);
                hasLoaded.current = true;
                setLoading(false);
            }
        }
    }, [workspace, toolId, populateFromTool, setLoading, setLogoSVG, toastError, isInitLoading]);

    useEffect(() => {
        let isMounted = true;
        loadData(isMounted);
        return () => { isMounted = false; };
    }, [loadData]);

    const handleSave = async () => {
        const response = await submitTool(workspace, toolId);
        if (response) {
            const buildResult = response.build_result;
            if (buildResult && buildResult.status === 'pending') {
                setBuildJobId(buildResult.job_id || null);
                setShowBuildProgress(true);
            } else {
                toastSuccess('Tool updated successfully!');
                onSuccess();
                onClose();
            }
        }
    };

    if (isInitLoading) {
        return (
            <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50">
                <div className="animate-spin text-[#8be9fd]">
                    <Settings size={48} />
                </div>
            </div>
        );
    }

    return (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4">
            <div className="bg-[#1a1b26] w-full max-w-5xl h-[90vh] rounded-xl flex flex-col border border-[#44475a] shadow-2xl overflow-hidden mt-8">
                {/* Header */}
                <div className="px-6 py-4 border-b border-[#44475a] flex items-center justify-between bg-[#1f2937]/50 flex-shrink-0">
                    <div className="flex items-center gap-3">
                        <div className="p-2 bg-[#bd93f9]/20 rounded-lg">
                            <Settings className="text-[#bd93f9]" size={20} />
                        </div>
                        <div>
                            <h2 className="text-xl font-bold text-white">Edit Tool</h2>
                            <p className="text-sm text-[#6272a4]">{toolId}</p>
                        </div>
                    </div>
                    <button onClick={onClose} className="p-2 hover:bg-white/10 rounded-full transition-colors">
                        <X size={20} className="text-[#6272a4]" />
                    </button>
                </div>

                {/* Tabs Navigation */}
                <div className="flex bg-[#16161e] px-6 border-b border-[#44475a] flex-shrink-0">
                    <TabButton active={activeTab === 'metadata'} onClick={() => setActiveTab('metadata')} icon={<Settings size={14} />} label="General" />
                    <TabButton active={activeTab === 'script'} onClick={() => setActiveTab('script')} icon={<Code size={14} />} label="Python Script" />
                    <TabButton active={activeTab === 'arguments'} onClick={() => setActiveTab('arguments')} icon={<ListTree size={14} />} label="Arguments" />
                    <TabButton active={activeTab === 'docker'} onClick={() => setActiveTab('docker')} icon={<Layers size={14} />} label="Docker & Resources" />
                    <TabButton active={activeTab === 'preview'} onClick={() => setActiveTab('preview')} icon={<Eye size={14} />} label="Preview" />
                </div>

                {/* Content Area */}
                <div className="flex-1 overflow-y-auto custom-scrollbar p-6">
                    {activeTab === 'metadata' && (
                        <div className="space-y-6 max-w-2xl mx-auto">
                            <div>
                                <label className="block text-sm font-bold text-[#8be9fd] mb-2 uppercase tracking-wider">Tool Name</label>
                                <input
                                    type="text"
                                    value={toolName}
                                    onChange={(e) => setToolName(e.target.value)}
                                    className="w-full bg-[#1a1b26] border border-[#44475a] rounded-lg p-3 text-white focus:outline-none focus:border-[#bd93f9] transition-colors font-mono"
                                    placeholder="my_awesome_tool"
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-bold text-[#8be9fd] mb-2 uppercase tracking-wider">Description</label>
                                <textarea
                                    value={description}
                                    onChange={(e) => setDescription(e.target.value)}
                                    rows={4}
                                    className="w-full bg-[#1a1b26] border border-[#44475a] rounded-lg p-3 text-white focus:outline-none focus:border-[#bd93f9] transition-colors resize-none"
                                    placeholder="What does this tool do?"
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-bold text-[#8be9fd] mb-2 uppercase tracking-wider">Tool Logo</label>
                                <LogoUploader
                                    currentLogo={logoSVG === 'loading' ? undefined : (logoSVG || undefined)}
                                    onLogoChange={setLogoSVG}
                                    label="Icon"
                                />
                            </div>
                        </div>
                    )}

                    {activeTab === 'script' && (
                        <ScriptEditorSection
                            scriptCode={scriptCode}
                            setScriptCode={setScriptCode}
                            setShowTestDialog={setShowTestDialog}
                            validation={validation}
                        />
                    )}

                    {activeTab === 'arguments' && (
                        <div className="space-y-6 max-w-4xl mx-auto">
                            <div className="flex items-center justify-between mb-4">
                                <div>
                                    <h3 className="text-lg font-bold text-white italic">Tool Interface</h3>
                                    <p className="text-sm text-[#6272a4]">Define how users will interact with your tool.</p>
                                </div>
                            </div>
                            <ArgumentsBuilder arguments={arguments_} onChange={setArguments} />
                        </div>
                    )}

                    {activeTab === 'docker' && (
                        <DockerConfigSection
                            dockerMode={dockerMode} setDockerMode={setDockerMode}
                            preexistingImage={preexistingImage} setPreexistingImage={setPreexistingImage}
                            baseImage={baseImage} setBaseImage={setBaseImage}
                            aptPackages={aptPackages} setAptPackages={setAptPackages}
                            pipPackages={pipPackages} setPipPackages={setPipPackages}
                            cpuRequest={cpuRequest} setCpuRequest={setCpuRequest}
                            cpuLimit={cpuLimit} setCpuLimit={setCpuLimit}
                            memoryRequest={memoryRequest} setMemoryRequest={setMemoryRequest}
                            memoryLimit={memoryLimit} setMemoryLimit={setMemoryLimit}
                        />
                    )}

                    {activeTab === 'preview' && (
                        <div className="max-w-4xl mx-auto">
                            <div className="flex items-center justify-between mb-6">
                                <h3 className="text-lg font-bold text-white flex items-center gap-2">
                                    <Shield className="text-[#50fa7b]" size={20} />
                                    Review & Test
                                </h3>
                                <Button onClick={() => setShowTestDialog(true)} className="bg-[#bd93f9] hover:bg-[#bd93f9]/90 text-black font-bold flex items-center gap-2">
                                    <Play size={16} /> Run Test
                                </Button>
                            </div>
                            <PreviewSection
                                toolName={toolName}
                                description={description}
                                workspace={workspace}
                                arguments_={arguments_}
                                scriptCode={scriptCode}
                            />
                        </div>
                    )}
                </div>

                {/* Footer */}
                <div className="px-6 py-4 bg-[#1a1b26] rounded-b-lg flex justify-end gap-3 flex-shrink-0 border-t border-[#44475a]">
                    <Button variant="outline" onClick={onClose} className="border-[#6272a4]/40 text-[#6272a4] hover:text-white hover:bg-white/5">Cancel</Button>
                    <Button
                        onClick={handleSave}
                        disabled={submitting || !toolName.trim()}
                        className="bg-[#50fa7b] hover:bg-[#50fa7b]/90 text-[#1a1b26] font-bold"
                    >
                        {submitting ? 'Saving...' : 'Save Changes'}
                        <Save size={16} className="ml-2" />
                    </Button>
                </div>
            </div>

            <BuildProgress
                isOpen={showBuildProgress}
                onClose={() => {
                    setShowBuildProgress(false);
                    onSuccess();
                    onClose();
                }}
                jobId={buildJobId}
                toolName={toolName}
            />

            {showTestDialog && (
                <TestToolDialog
                    scriptCode={scriptCode}
                    arguments={arguments_}
                    toolName={toolName}
                    toolId={toolId}
                    onClose={() => setShowTestDialog(false)}
                />
            )}
        </div>
    );
};

interface TabButtonProps { active: boolean; onClick: () => void; icon: React.ReactNode; label: string; }
const TabButton: React.FC<TabButtonProps> = ({ active, onClick, icon, label }) => (
    <button
        onClick={onClick}
        className={`px-4 py-3 font-mono text-sm border-b-2 transition-all flex items-center gap-2 ${active ? 'bg-[#1a1b26] text-[#8be9fd] border-[#8be9fd]' : 'text-[#6272a4] border-transparent hover:text-white'}`}
    >
        {icon} {label}
    </button>
);

interface PreviewSectionProps { toolName: string; description: string; workspace: string; arguments_: Argument[]; scriptCode: string; }
const PreviewSection: React.FC<PreviewSectionProps> = ({ toolName, description, workspace, arguments_, scriptCode }) => (
    <div className="space-y-6">
        <div className="bg-[#1a1b26] rounded-lg p-4 space-y-2 border border-[#44475a]">
            <PreviewRow label="Name" value={toolName || '(not set)'} />
            <PreviewRow label="Workspace" value={workspace} />
            <PreviewRow label="Arguments" value={arguments_.length.toString()} />
            <PreviewRow label="Script Lines" value={scriptCode.split('\n').length.toString()} />
        </div>
        <PreviewBlock label="Generated YAML">
            <pre className="text-white font-mono text-xs whitespace-pre-wrap overflow-x-auto custom-scrollbar">
                {generateYAML(toolName, description, arguments_)}
            </pre>
        </PreviewBlock>
        <PreviewBlock label="Python Script Preview">
            <pre className="text-white font-mono text-xs whitespace-pre-wrap overflow-x-auto custom-scrollbar">
                {getCodePreview(scriptCode, 20)}
            </pre>
        </PreviewBlock>
    </div>
);

interface PreviewRowProps { label: string; value: React.ReactNode; }
const PreviewRow: React.FC<PreviewRowProps> = ({ label, value }) => (
    <div className="flex justify-between">
        <span className="text-[#6272a4] text-sm">{label}:</span>
        <span className="text-white font-mono text-sm">{value}</span>
    </div>
);

interface PreviewBlockProps { label: string; children: React.ReactNode; }
const PreviewBlock: React.FC<PreviewBlockProps> = ({ label, children }) => (
    <div>
        <h4 className="text-sm font-mono text-[#8be9fd] uppercase mb-3">{label}</h4>
        <div className="bg-[#1a1b26] rounded-lg p-4 border border-[#44475a]">
            {children}
        </div>
    </div>
);

export default EditToolDialog;
