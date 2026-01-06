import React, { useEffect } from 'react';
import Editor, { useMonaco } from '@monaco-editor/react';
import { Play, AlertCircle, AlertTriangle, CheckCircle } from 'lucide-react';
import { Button } from "@/components/ui/Button/Button";
import { draculaTheme } from '@/lib/monaco-dracula-theme';
import type { ValidationResult } from '@/lib/python-validator';
import { getValidationMessage } from '@/lib/python-validator';

interface ScriptEditorSectionProps {
    scriptCode: string;
    setScriptCode: (code: string) => void;
    setShowTestDialog: (show: boolean) => void;
    validation: ValidationResult;
}

const ScriptEditorSection: React.FC<ScriptEditorSectionProps> = ({
    scriptCode,
    setScriptCode,
    setShowTestDialog,
    validation
}) => {
    const monaco = useMonaco();

    useEffect(() => {
        if (monaco) {
            monaco.editor.defineTheme('dracula', draculaTheme);
            monaco.editor.setTheme('dracula');
        }
    }, [monaco]);

    return (
        <div className="space-y-4">
            <div>
                <label className="block text-sm font-mono text-[#6272a4] uppercase mb-2">
                    Python Script
                </label>
                <div className="border border-[#282a36] rounded overflow-hidden">
                    <Editor
                        height="500px"
                        language="python"
                        theme="dracula"
                        value={scriptCode}
                        onChange={(value) => setScriptCode(value || '')}
                        options={{
                            minimap: { enabled: true },
                            fontSize: 13,
                            fontFamily: 'JetBrains Mono, Consolas, Monaco, Courier New, monospace',
                            scrollBeyondLastLine: false,
                            automaticLayout: true,
                            tabSize: 4,
                            wordWrap: 'on'
                        }}
                    />
                </div>
                <div className="mt-3">
                    <Button
                        onClick={() => setShowTestDialog(true)}
                        className="bg-[#8be9fd] hover:bg-[#8be9fd]/90 text-[#050101] font-bold gap-2"
                    >
                        <Play size={16} />
                        Test Script
                    </Button>
                </div>
            </div>

            {/* Validation Feedback */}
            <div className={`rounded-lg p-4 border ${!validation.valid
                ? 'bg-[#ff5555]/10 border-[#ff5555]/30'
                : validation.warnings.length > 0
                    ? 'bg-[#ffb86c]/10 border-[#ffb86c]/30'
                    : 'bg-[#50fa7b]/10 border-[#50fa7b]/30'
                }`}>
                <div className="flex items-center gap-2 mb-2">
                    {!validation.valid ? (
                        <>
                            <AlertCircle size={18} className="text-[#ff5555]" />
                            <span className="text-[#ff5555] font-mono text-sm font-bold">
                                {getValidationMessage(validation)}
                            </span>
                        </>
                    ) : validation.warnings.length > 0 ? (
                        <>
                            <AlertTriangle size={18} className="text-[#ffb86c]" />
                            <span className="text-[#ffb86c] font-mono text-sm font-bold">
                                {getValidationMessage(validation)}
                            </span>
                        </>
                    ) : (
                        <>
                            <CheckCircle size={18} className="text-[#50fa7b]" />
                            <span className="text-[#50fa7b] font-mono text-sm font-bold">
                                {getValidationMessage(validation)}
                            </span>
                        </>
                    )}
                </div>

                {validation.errors.length > 0 && (
                    <div className="space-y-1 mb-2">
                        {validation.errors.map((error, idx) => (
                            <div key={idx} className="flex items-start gap-2 text-xs text-[#ff5555] font-mono">
                                <span>❌</span>
                                <span>{error}</span>
                            </div>
                        ))}
                    </div>
                )}

                {validation.warnings.length > 0 && (
                    <div className="space-y-1">
                        {validation.warnings.map((warning, idx) => (
                            <div key={idx} className="flex items-start gap-2 text-xs text-[#ffb86c] font-mono">
                                <span>⚠️</span>
                                <span>{warning}</span>
                            </div>
                        ))}
                    </div>
                )}
            </div>
        </div>
    );
};

export default ScriptEditorSection;
