import React, { useEffect, useState, useRef } from 'react';
import Editor from '@monaco-editor/react';
import { Save, FileCode, FileType, Circle, AlertCircle, Check, Hammer } from 'lucide-react';
import { Button } from "@/components/ui/Button/Button";
import { draculaTheme } from '@/lib/monaco-dracula-theme';
import { BuildProgress } from './BuildProgress';

interface CodeEditorProps {
    toolId?: string;
    filePath: string;
    onSave?: (filePath: string) => void;
}

interface FileTab {
    path: string;
    toolId?: string;
    name: string;
    language: string;
    content: string;
    originalContent: string;
    hasChanges: boolean;
}

const CodeEditor: React.FC<CodeEditorProps> = ({ toolId, filePath, onSave }) => {
    const [tabs, setTabs] = useState<FileTab[]>([]);
    const [activeTabIndex, setActiveTabIndex] = useState(0);
    const [status, setStatus] = useState<string>("");
    const [cursorPosition, setCursorPosition] = useState({ line: 1, column: 1 });
    const editorRef = useRef<any>(null);
    const [buildJobId, setBuildJobId] = useState<string | null>(null);

    // Initialize tabs when filePath or toolId changes
    useEffect(() => {
        const initializeTabs = async () => {
            const pythonPath = filePath;
            const yamlPath = filePath.replace('.py', '.yaml');

            const tabsToLoad: FileTab[] = [
                {
                    path: pythonPath,
                    toolId: toolId,
                    name: pythonPath.split('/').pop() || 'script.py',
                    language: 'python',
                    content: '',
                    originalContent: '',
                    hasChanges: false,
                },
                {
                    path: yamlPath,
                    toolId: toolId,
                    name: yamlPath.split('/').pop() || 'metadata.yaml',
                    language: 'yaml',
                    content: '',
                    originalContent: '',
                    hasChanges: false,
                },
            ];

            // Load content for both files
            const loadedTabs = await Promise.all(
                tabsToLoad.map(async (tab) => {
                    try {
                        const baseUrl = '/api/tools/content';
                        const params = new URLSearchParams();

                        if (tab.toolId) {
                            params.append('tool_id', tab.toolId);
                            params.append('file_type', tab.language === 'python' ? 'py' : 'yaml');
                        } else {
                            params.append('path', tab.path);
                        }

                        const res = await fetch(`${baseUrl}?${params.toString()}`);
                        const data = await res.json();
                        return {
                            ...tab,
                            content: data.content || '',
                            originalContent: data.content || '',
                        };
                    } catch (err) {
                        console.error(`Error loading ${tab.path}:`, err);
                        return {
                            ...tab,
                            content: '// Error loading file from database',
                            originalContent: '',
                        };
                    }
                })
            );

            setTabs(loadedTabs);
            setActiveTabIndex(0);
        };

        initializeTabs();
    }, [filePath, toolId]);

    const activeTab = tabs[activeTabIndex];

    const handleSave = async () => {
        if (!activeTab) return;

        setStatus("saving");
        try {
            const res = await fetch('/api/tools/content', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    path: activeTab.path,
                    content: activeTab.content
                }),
            });

            if (res.ok) {
                setStatus("saved");
                // Update originalContent and reset hasChanges
                setTabs(tabs.map((tab, idx) =>
                    idx === activeTabIndex
                        ? { ...tab, originalContent: tab.content, hasChanges: false }
                        : tab
                ));
                setTimeout(() => setStatus(""), 2000);

                // Notify parent component if callback provided
                if (onSave && activeTab.path.endsWith('.yaml')) {
                    onSave(activeTab.path);
                }
            } else {
                setStatus("error");
            }
        } catch (err: any) {
            setStatus("error");
        }
    };

    const handleSaveAll = async () => {
        setStatus("saving");
        const changedTabs = tabs.filter(tab => tab.hasChanges);

        try {
            await Promise.all(
                changedTabs.map(tab =>
                    fetch('/api/tools/content', {
                        method: 'POST',
                        headers: { 'Content-Type': 'application/json' },
                        body: JSON.stringify({
                            path: tab.path,
                            content: tab.content
                        }),
                    })
                )
            );

            setStatus("saved");
            setTabs(tabs.map(tab => ({
                ...tab,
                originalContent: tab.content,
                hasChanges: false
            })));
            setTimeout(() => setStatus(""), 2000);

            // Notify parent if any YAML was saved
            if (onSave && changedTabs.some(tab => tab.path.endsWith('.yaml'))) {
                const yamlTab = changedTabs.find(tab => tab.path.endsWith('.yaml'));
                if (yamlTab) onSave(yamlTab.path);
            }
        } catch (err) {
            setStatus("error");
        }
    };

    const handleSaveAndBuild = async () => {
        if (!activeTab) return;

        setStatus("saving");
        try {
            // First save the file
            const res = await fetch('/api/tools/content', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    path: activeTab.path,
                    content: activeTab.content
                }),
            });

            if (res.ok) {
                // Update originalContent and reset hasChanges
                setTabs(tabs.map((tab, idx) =>
                    idx === activeTabIndex
                        ? { ...tab, originalContent: tab.content, hasChanges: false }
                        : tab
                ));

                // Trigger build if toolId is available
                if (toolId) {
                    setStatus("building");
                    const buildRes = await fetch(`/api/tools/${toolId}/build`, {
                        method: 'POST'
                    });

                    if (buildRes.ok) {
                        const buildData = await buildRes.json();
                        // A resposta retorna job_id diretamente
                        if (buildData.job_id) {
                            setBuildJobId(buildData.job_id);
                        }

                        setStatus("saved");
                        setTimeout(() => setStatus(""), 2000);
                    } else {
                        const errorText = await buildRes.text();
                        console.error('Build failed:', buildRes.status, errorText);
                        setStatus("error");
                    }
                } else {
                    setStatus("saved");
                    setTimeout(() => setStatus(""), 2000);
                }

                // Notify parent component if callback provided
                if (onSave && activeTab.path.endsWith('.yaml')) {
                    onSave(activeTab.path);
                }
            } else {
                setStatus("error");
            }
        } catch (err: any) {
            setStatus("error");
        }
    };

    const handleEditorDidMount = (editor: any) => {
        editorRef.current = editor;

        editor.onDidChangeCursorPosition((e: any) => {
            setCursorPosition({
                line: e.position.lineNumber,
                column: e.position.column,
            });
        });
    };

    const handleCodeChange = (value: string | undefined) => {
        const newContent = value || "";
        setTabs(tabs.map((tab, idx) =>
            idx === activeTabIndex
                ? {
                    ...tab,
                    content: newContent,
                    hasChanges: newContent !== tab.originalContent
                }
                : tab
        ));
    };

    const getStatusIcon = () => {
        switch (status) {
            case "saving": return <Circle className="animate-spin" size={14} />;
            case "saved": return <Check size={14} className="text-dracula-green" />;
            case "error": return <AlertCircle size={14} className="text-dracula-red" />;
            default: return null;
        }
    };

    const getStatusText = () => {
        switch (status) {
            case "saving": return "Saving...";
            case "building": return "Building...";
            case "saved": return "All changes saved";
            case "error": return "Error saving";
            default: return "";
        }
    };

    const hasAnyChanges = tabs.some(tab => tab.hasChanges);
    const pathParts = activeTab?.path.split('/') || [];
    const fileDir = pathParts.length >= 2 ? pathParts[pathParts.length - 2] : '/';

    if (!activeTab) {
        return (
            <div className="h-full flex items-center justify-center bg-[#1e1e1e] text-[#858585]">
                Loading files...
            </div>
        );
    }

    return (
        <div className="h-full flex flex-col bg-[#282a36] overflow-hidden">
            {/* Tab Bar - Dracula style */}
            <div className="flex items-center bg-[#191a21] border-b border-[#282a36]">
                {/* File tabs */}
                {tabs.map((tab, idx) => (
                    <div
                        key={tab.path}
                        onClick={() => setActiveTabIndex(idx)}
                        className={`flex items-center gap-2 px-4 py-2 border-r border-[#282a36] min-w-[180px] cursor-pointer group transition-colors ${idx === activeTabIndex
                            ? 'bg-[#282a36] text-[#f8f8f2] border-t-2 border-t-[#bd93f9]'
                            : 'bg-[#191a21] text-[#6272a4] hover:bg-[#21222c]'
                            }`}
                    >
                        {tab.language === 'python' ? (
                            <FileCode size={16} className={idx === activeTabIndex ? "text-[#8be9fd]" : "text-[#858585]"} />
                        ) : (
                            <FileType size={16} className={idx === activeTabIndex ? "text-[#f1fa8c]" : "text-[#858585]"} />
                        )}
                        <span className="text-sm font-normal truncate flex-1">{tab.name}</span>
                        {tab.hasChanges && (
                            <div className="w-2 h-2 rounded-full bg-[#8be9fd] flex-shrink-0" />
                        )}
                    </div>
                ))}

                {/* Action buttons */}
                <div className="flex items-center gap-2 px-3 ml-auto">
                    {hasAnyChanges && (
                        <Button
                            variant="ghost"
                            size="sm"
                            onClick={handleSaveAll}
                            disabled={status === "saving"}
                            className="h-7 text-xs gap-1.5 hover:bg-[#2a2d2e] text-[#cccccc]"
                        >
                            <Save size={12} />
                            Save All
                        </Button>
                    )}
                    <Button
                        variant="ghost"
                        size="sm"
                        onClick={handleSave}
                        disabled={!activeTab.hasChanges || status === "saving" || status === "building"}
                        className="h-7 text-xs gap-1.5 hover:bg-[#2a2d2e] text-[#cccccc] disabled:opacity-50"
                    >
                        <Save size={12} />
                        Save
                    </Button>
                    <Button
                        variant="ghost"
                        size="sm"
                        onClick={handleSaveAndBuild}
                        disabled={!activeTab.hasChanges || status === "saving" || status === "building"}
                        className="h-7 text-xs gap-1.5 hover:bg-[#2a2d2e] text-[#50fa7b] disabled:opacity-50"
                    >
                        <Hammer size={12} />
                        Save & Build
                    </Button>
                </div>
            </div>

            {/* Breadcrumb */}
            <div className="flex items-center gap-1 px-4 py-1.5 bg-[#191a21] border-b border-[#282a36]">
                <span className="text-[#858585] text-xs font-mono">{fileDir}</span>
                <span className="text-[#858585] text-xs">/</span>
                <span className="text-[#cccccc] text-xs font-mono font-semibold">{activeTab.name.replace('.script', '')}</span>
            </div>

            {/* Editor */}
            <div className="flex-1 relative">
                <Editor
                    height="100%"
                    language={activeTab.language}
                    value={activeTab.content}
                    theme="dracula"
                    onChange={handleCodeChange}
                    onMount={handleEditorDidMount}
                    options={{
                        minimap: { enabled: true, scale: 1 },
                        fontSize: 14,
                        fontFamily: "'Fira Code', 'Cascadia Code', 'Consolas', monospace",
                        fontLigatures: true,
                        scrollBeyondLastLine: false,
                        padding: { top: 16, bottom: 16 },
                        lineNumbers: "on",
                        renderLineHighlight: "all",
                        automaticLayout: true,
                        cursorBlinking: 'smooth',
                        cursorSmoothCaretAnimation: 'on',
                        smoothScrolling: true,
                        colorDecorators: true,
                        bracketPairColorization: { enabled: true },
                        guides: {
                            indentation: true,
                            bracketPairs: true,
                        },
                        scrollbar: {
                            vertical: 'visible',
                            horizontal: 'visible',
                            useShadows: false,
                            verticalScrollbarSize: 10,
                            horizontalScrollbarSize: 10,
                        },
                    }}
                    beforeMount={(monaco) => {
                        monaco.editor.defineTheme('dracula', draculaTheme);
                        monaco.editor.setTheme('dracula');
                    }}
                />
            </div>

            {/* Status Bar - Dracula style */}
            <div className="flex items-center justify-between px-3 py-1 bg-[#bd93f9] text-[#282a36] text-xs font-bold">
                <div className="flex items-center gap-4">
                    <div className="flex items-center gap-2">
                        {getStatusIcon()}
                        <span className="font-medium">{getStatusText()}</span>
                    </div>
                    <div className="flex items-center gap-1">
                        <span className="opacity-90">Ln {cursorPosition.line}, Col {cursorPosition.column}</span>
                    </div>
                </div>
                <div className="flex items-center gap-4">
                    <span className="opacity-90 capitalize">{activeTab.language}</span>
                    <span className="opacity-90">UTF-8</span>
                    <span className="opacity-90">LF</span>
                </div>
            </div>

            <BuildProgress
                isOpen={!!buildJobId}
                onClose={() => setBuildJobId(null)}
                jobId={buildJobId}
                toolName={activeTab?.name || 'Tool'}
            />
        </div>
    );
};

export default CodeEditor;
