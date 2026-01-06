import React, { useState } from 'react';
import { X, AlertTriangle, Key, Copy, Check } from 'lucide-react';
import { Button } from "@/components/ui/Button/Button";
import { useToast } from './Toast';

interface RegenerateKeyDialogProps {
    mcpId: string;
    mcpName: string;
    onClose: () => void;
    onSuccess: () => void;
}

const RegenerateKeyDialog: React.FC<RegenerateKeyDialogProps> = ({
    mcpId,
    mcpName,
    onClose,
    onSuccess
}) => {
    const [step, setStep] = useState<'confirm' | 'success'>('confirm');
    const [loading, setLoading] = useState(false);
    const [newKey, setNewKey] = useState('');
    const [copied, setCopied] = useState(false);
    const toast = useToast();

    const handleConfirm = async () => {
        setLoading(true);
        try {
            const res = await fetch(`/api/mcps/${mcpId}/regenerate-key`, { method: 'POST' });
            if (res.ok) {
                const data = await res.json();
                setNewKey(data.api_key);
                setStep('success');
                onSuccess(); // Trigger refresh in parent
            } else {
                const error = await res.json();
                toast.error(`Failed: ${error.detail || 'Unknown error'}`);
                onClose();
            }
        } catch (err) {
            console.error('Error generating key:', err);
            toast.error('Failed to generate key');
            onClose();
        } finally {
            setLoading(false);
        }
    };

    const handleCopy = () => {
        navigator.clipboard.writeText(newKey);
        setCopied(true);
        toast.success('API Key copied to clipboard');
        setTimeout(() => setCopied(false), 2000);
    };

    return (
        <div className="fixed inset-0 bg-black/80 flex items-center justify-center z-50 p-4">
            <div className="bg-[#0b0b11] rounded-lg shadow-2xl border border-[#1a1b26] w-full max-w-md animate-in fade-in zoom-in duration-200">
                {/* Header */}
                <div className="bg-gradient-to-r from-[#1a1b26] to-[#282a36] px-6 py-4 flex justify-between items-center rounded-t-lg border-b border-[#282a36]">
                    <div className="flex items-center gap-3">
                        <Key size={20} className="text-[#8be9fd]" />
                        <h3 className="text-lg font-bold text-white">Regenerate API Key</h3>
                    </div>
                    <Button variant="ghost" size="sm" onClick={onClose} disabled={loading && step === 'confirm'}>
                        <X size={20} />
                    </Button>
                </div>

                {/* Content */}
                <div className="p-6">
                    {step === 'confirm' ? (
                        <div className="text-center">
                            <div className="w-16 h-16 bg-[#ff5555]/10 rounded-full flex items-center justify-center mx-auto mb-4 border border-[#ff5555]/20">
                                <AlertTriangle size={32} className="text-[#ff5555]" />
                            </div>
                            <h4 className="text-xl font-bold text-white mb-2">Are you sure?</h4>
                            <p className="text-[#6272a4] mb-6">
                                This will invalidate the current API key for <strong>{mcpName}</strong>.
                                Any applications using the old key will stop working immediately.
                            </p>

                            <div className="flex gap-3 justify-center">
                                <Button
                                    variant="outline"
                                    onClick={onClose}
                                    disabled={loading}
                                    className="border-[#6272a4]/40 hover:bg-[#6272a4]/10"
                                >
                                    Cancel
                                </Button>
                                <Button
                                    onClick={handleConfirm}
                                    disabled={loading}
                                    className="bg-[#ff5555] hover:bg-[#ff5555]/90 text-white font-bold border-b-4 border-[#cf143d] active:border-b-0 active:translate-y-1"
                                >
                                    {loading ? 'Regenerating...' : 'Yes, Regenerate Key'}
                                </Button>
                            </div>
                        </div>
                    ) : (
                        <div>
                            <div className="text-center mb-6">
                                <div className="w-16 h-16 bg-[#50fa7b]/10 rounded-full flex items-center justify-center mx-auto mb-4 border border-[#50fa7b]/20">
                                    <Check size={32} className="text-[#50fa7b]" />
                                </div>
                                <h4 className="text-xl font-bold text-white mb-2">Key Generated!</h4>
                                <p className="text-[#6272a4] text-sm">
                                    This key will only be shown once. Please save it in a secure location.
                                </p>
                            </div>

                            <div className="bg-[#1a1b26] p-4 rounded-lg border border-[#282a36] relative mb-6">
                                <code className="text-[#50fa7b] font-mono break-all text-sm block pr-10">
                                    {newKey}
                                </code>
                                <Button
                                    size="sm"
                                    variant="ghost"
                                    className="absolute top-2 right-2 text-[#6272a4] hover:text-white"
                                    onClick={handleCopy}
                                >
                                    {copied ? <Check size={16} /> : <Copy size={16} />}
                                </Button>
                            </div>

                            <Button
                                onClick={onClose}
                                className="w-full bg-[#8be9fd] hover:bg-[#8be9fd]/90 text-[#050101] font-bold border-b-4 border-[#41a0b3] active:border-b-0 active:translate-y-1"
                            >
                                Done
                            </Button>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default RegenerateKeyDialog;
