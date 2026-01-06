import React, { useState } from 'react';
import { X, Settings, ListTree, Eye } from 'lucide-react';
import { Button } from "@/components/ui/Button/Button";
import ArgumentsBuilder from './ArgumentsBuilder';
import { useToast } from './Toast';
import { generateYAML, getCodePreview } from '@/lib/preview-utils';
import LogoUploader from './LogoUploader';
import { BuildProgress } from './BuildProgress';
import { useToolForm, TEMPLATES } from '../hooks/useToolForm';
import DockerConfigSection from './DockerConfigSection';
import ScriptEditorSection from './ScriptEditorSection';
import TestToolDialog from './TestToolDialog';

interface CreateToolDialogProps {
    workspace: string | null;
    onClose: () => void;
    onSuccess: () => void;
}

const CreateToolDialog: React.FC<CreateToolDialogProps> = ({ workspace, onClose, onSuccess }) => {
    const [activeTab, setActiveTab] = useState<'metadata' | 'script' | 'arguments' | 'docker' | 'preview'>('metadata');
    const [showTestDialog, setShowTestDialog] = useState(false);

    // Async Build State
    const [buildJobId, setBuildJobId] = useState<string | null>(null);
    const [showBuildProgress, setShowBuildProgress] = useState(false);

    const {
        toolName, setToolName,
        description, setDescription,
        scriptCode, setScriptCode,
        arguments_, setArguments,
        selectedTemplate,
        submitting, validation,
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
        handleTemplateChange,
        submitTool
    } = useToolForm();

    const toast = useToast();

    const handleCreate = async () => {
        if (!workspace) {
            toast.error('Workspace is required');
            return;
        }

        const response = await submitTool(workspace) as any;
        if (response) {
            const buildResult = response.tool?.build_result || response.build_result;
            if (buildResult && buildResult.status === 'pending') {
                setBuildJobId(buildResult.job_id || null);
                setShowBuildProgress(true);
            } else {
                toast.success('Tool created successfully!');
                onSuccess();
                onClose();
            }
        }
    };

    return (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4">
            <div className="bg-[#0b0b11] rounded-lg shadow-2xl border border-[#1a1b26] w-full max-w-5xl max-h-[90vh] flex flex-col">
                {/* Header */}
                <div className="bg-gradient-to-r from-[#1a1b26] to-[#282a36] px-6 py-4 flex justify-between items-center rounded-t-lg flex-shrink-0">
                    <div>
                        <h3 className="text-xl font-bold text-white">Create New Tool</h3>
                        <p className="text-sm text-[#6272a4]">Workspace: {workspace}</p>
                    </div>
                    <Button variant="ghost" size="sm" onClick={onClose}>
                        <X size={20} />
                    </Button>
                </div>

                {/* Tabs */}
                <div className="flex gap-1 px-6 pt-4 border-b border-[#1a1b26] flex-shrink-0">
                    <TabButton active={activeTab === 'metadata'} onClick={() => setActiveTab('metadata')} icon={<Settings size={16} />} label="Metadata" />
                    <TabButton active={activeTab === 'script'} onClick={() => setActiveTab('script')} icon={<Settings size={16} />} label="Script" />
                    <TabButton active={activeTab === 'arguments'} onClick={() => setActiveTab('arguments')} icon={<ListTree size={16} />} label="Arguments" />
                    <TabButton active={activeTab === 'docker'} onClick={() => setActiveTab('docker')} icon={<Settings size={16} />} label="Docker & Resources" />
                    <TabButton active={activeTab === 'preview'} onClick={() => setActiveTab('preview')} icon={<Eye size={16} />} label="Preview" />
                </div>

                {/* Content */}
                <div className="flex-1 overflow-auto p-6 custom-scrollbar">
                    {activeTab === 'metadata' && (
                        <div className="space-y-4">
                            <div>
                                <label className="block text-sm font-mono text-[#6272a4] uppercase mb-2">Tool Name *</label>
                                <input
                                    type="text"
                                    value={toolName}
                                    onChange={(e) => setToolName(e.target.value)}
                                    className="w-full bg-[#1a1b26] border border-[#282a36] rounded px-4 py-2 text-white font-mono focus:outline-none focus:border-[#8be9fd]"
                                    placeholder="e.g., Port Scanner"
                                />
                            </div>
                            <div>
                                <label className="block text-sm font-mono text-[#6272a4] uppercase mb-2">Description</label>
                                <textarea
                                    value={description}
                                    onChange={(e) => setDescription(e.target.value)}
                                    className="w-full bg-[#1a1b26] border border-[#282a36] rounded px-4 py-2 text-white font-mono focus:outline-none focus:border-[#8be9fd] resize-none"
                                    rows={3}
                                    placeholder="Descreva a funcionalidade da tool..."
                                />
                            </div>
                            <LogoUploader currentLogo={logoSVG || undefined} onLogoChange={(svg) => setLogoSVG(svg || null)} label="Tool Logo (optional)" />
                            <div>
                                <label className="block text-sm font-mono text-[#6272a4] uppercase mb-2">Template</label>
                                <select
                                    value={selectedTemplate}
                                    onChange={(e) => handleTemplateChange(e.target.value as keyof typeof TEMPLATES)}
                                    className="w-full bg-[#1a1b26] border border-[#282a36] rounded px-4 py-2 text-white font-mono focus:outline-none focus:border-[#8be9fd]"
                                >
                                    {Object.entries(TEMPLATES).map(([key, t]) => (
                                        <option key={key} value={key}>{t.name}</option>
                                    ))}
                                </select>
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
                        <ArgumentsBuilder arguments={arguments_} onChange={setArguments} />
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
                        <PreviewSection
                            toolName={toolName}
                            description={description}
                            workspace={workspace!}
                            arguments_={arguments_}
                            selectedTemplate={selectedTemplate}
                            scriptCode={scriptCode}
                        />
                    )}
                </div>

                {/* Footer */}
                <div className="px-6 py-4 bg-[#1a1b26] rounded-b-lg flex justify-end gap-3 flex-shrink-0">
                    <Button variant="outline" onClick={onClose} className="border-[#6272a4]/40">Cancel</Button>
                    <Button
                        onClick={handleCreate}
                        disabled={submitting || !toolName.trim()}
                        className="bg-[#50fa7b] hover:bg-[#50fa7b]/90 text-[#050101] font-bold"
                    >
                        {submitting ? 'Creating...' : 'Create Tool'}
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

            {/* Test Tool Dialog */}
            {showTestDialog && (
                <TestToolDialog
                    scriptCode={scriptCode}
                    arguments={arguments_}
                    toolName={toolName}
                    onClose={() => setShowTestDialog(false)}
                />
            )}
        </div>
    );
};

const TabButton = ({ active, onClick, icon, label }: any) => (
    <button
        className={`px-4 py-2 font-mono text-sm rounded-t transition-all flex items-center gap-2 ${active
            ? 'bg-[#1a1b26] text-[#8be9fd] border-b-2 border-[#8be9fd]'
            : 'text-[#6272a4] hover:text-white'
            }`}
        onClick={onClick}
    >
        {icon}
        {label}
    </button>
);

const PreviewSection = ({ toolName, description, workspace, arguments_, selectedTemplate, scriptCode }: any) => (
    <div className="space-y-6">
        <div className="bg-[#1a1b26] rounded-lg p-4 space-y-2">
            <PreviewRow label="Name" value={toolName || '(not set)'} />
            <PreviewRow label="Workspace" value={workspace} />
            <PreviewRow label="Arguments" value={arguments_.length.toString()} />
            <PreviewRow label="Template" value={TEMPLATES[selectedTemplate as keyof typeof TEMPLATES].name} />
            <PreviewRow label="Script Lines" value={scriptCode.split('\n').length.toString()} />
        </div>
        <PreviewBlock title="Generated YAML" content={generateYAML(toolName, description, arguments_)} />
        <PreviewBlock title="Python Script Preview" content={getCodePreview(scriptCode, 20)} />
    </div>
);

const PreviewRow = ({ label, value }: any) => (
    <div className="flex justify-between">
        <span className="text-[#6272a4] text-sm">{label}:</span>
        <span className="text-white font-mono text-sm">{value}</span>
    </div>
);

const PreviewBlock = ({ title, content }: any) => (
    <div>
        <h4 className="text-sm font-mono text-[#8be9fd] uppercase mb-3">{title}</h4>
        <div className="bg-[#1a1b26] rounded-lg p-4">
            <pre className="text-white font-mono text-xs whitespace-pre-wrap overflow-x-auto custom-scrollbar">{content}</pre>
        </div>
    </div>
);

export default CreateToolDialog;
