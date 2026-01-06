import React, { useEffect, useRef, useState } from 'react';
import { X, Terminal, CheckCircle, AlertCircle, Loader2 } from 'lucide-react';
import * as Dialog from '@radix-ui/react-dialog';

interface BuildProgressProps {
    isOpen: boolean;
    onClose: () => void;
    jobId: string | null;
    toolName: string;
}

export const BuildProgress: React.FC<BuildProgressProps> = ({ isOpen, onClose, jobId, toolName }) => {
    const [logs, setLogs] = useState<string[]>([]);
    const [status, setStatus] = useState<'PENDING' | 'RUNNING' | 'SUCCESS' | 'FAILED'>('PENDING');
    const logsEndRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (!isOpen || !jobId) return;

        setLogs([]);
        setStatus('RUNNING');

        const eventSource = new EventSource(`/api/settings/registry/build/${jobId}/logs`);

        eventSource.onmessage = (event) => {
            if (event.data === 'closed') {
                eventSource.close();
                return;
            }
            setLogs(prev => [...prev, event.data]);
        };

        eventSource.addEventListener('success', () => {
            setStatus('SUCCESS');
            eventSource.close();
        });

        eventSource.addEventListener('failed', () => {
            setStatus('FAILED');
            eventSource.close();
        });

        eventSource.addEventListener('error', (e) => {
            console.error('SSE Error:', e);
            // Verify if complete
            if (eventSource.readyState === EventSource.CLOSED) {
                return;
            }
        });

        return () => {
            eventSource.close();
        };
    }, [isOpen, jobId]);

    // Auto-scroll
    useEffect(() => {
        logsEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, [logs]);

    return (
        <Dialog.Root open={isOpen} onOpenChange={onClose}>
            <Dialog.Portal>
                <Dialog.Overlay className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 animate-fade-in" />
                <Dialog.Content className="fixed left-[50%] top-[50%] translate-x-[-50%] translate-y-[-50%] w-full max-w-3xl bg-[#1e1e2e] rounded-xl shadow-2xl border border-[#313244] p-6 z-50 animate-fade-in-up">
                    <div className="flex justify-between items-center mb-4">
                        <div className="flex items-center gap-3">
                            <div className="p-2 bg-[#bd93f9]/10 rounded-lg">
                                <Terminal className="w-5 h-5 text-[#bd93f9]" />
                            </div>
                            <div>
                                <Dialog.Title className="text-lg font-bold text-[#f8f8f2]">
                                    Building {toolName}
                                </Dialog.Title>
                                <Dialog.Description className="text-sm text-[#6272a4]">
                                    {status === 'RUNNING' && 'Compiling and pushing container image...'}
                                    {status === 'SUCCESS' && 'Build completed successfully'}
                                    {status === 'FAILED' && 'Build failed'}
                                </Dialog.Description>
                            </div>
                        </div>

                        <div className="flex items-center gap-4">
                            {status === 'RUNNING' && <Loader2 className="w-5 h-5 text-[#bd93f9] animate-spin" />}
                            {status === 'SUCCESS' && <CheckCircle className="w-6 h-6 text-[#50fa7b]" />}
                            {status === 'FAILED' && <AlertCircle className="w-6 h-6 text-[#ff5555]" />}

                            <button
                                onClick={onClose}
                                className="p-1 hover:bg-[#313244] rounded-lg transition-colors"
                            >
                                <X className="w-5 h-5 text-[#6272a4]" />
                            </button>
                        </div>
                    </div>

                    <div className="bg-[#0f0f14] rounded-lg p-4 font-mono text-xs md:text-sm h-[400px] overflow-y-auto border border-[#313244] shadow-inner">
                        {logs.map((log, i) => (
                            <div key={i} className="text-[#f8f8f2] whitespace-pre-wrap leading-relaxed border-l-2 border-transparent hover:border-[#bd93f9]/50 pl-2 transition-colors">
                                {log}
                            </div>
                        ))}
                        {logs.length === 0 && (
                            <div className="text-[#6272a4] italic flex items-center gap-2">
                                <Loader2 className="w-4 h-4 animate-spin" />
                                Initializes build environment...
                            </div>
                        )}
                        <div ref={logsEndRef} />
                    </div>
                </Dialog.Content>
            </Dialog.Portal>
        </Dialog.Root>
    );
};
