import { useState, useCallback, useRef } from 'react';

export interface ExecutionState {
    result: string | null;
    logs: string;
    exitCode?: number;
}

export const useExecution = () => {
    const [executing, setExecuting] = useState(false);
    const [executionId, setExecutionId] = useState<string | null>(null);
    const [output, setOutput] = useState<ExecutionState | null>(null);
    const abortControllerRef = useRef<AbortController | null>(null);

    const runTool = useCallback(async (fullId: string, path: string, args: Record<string, any>, env?: Record<string, string>) => {
        setExecuting(true);
        setOutput({ result: "", logs: "", exitCode: undefined });
        setExecutionId(null);

        const abortController = new AbortController();
        abortControllerRef.current = abortController;

        try {
            const response = await fetch('/api/executions/execute/stream', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    tool_id: fullId,
                    path: path,
                    arguments: args,
                    env: env
                }),
                signal: abortController.signal
            });

            if (!response.ok) {
                const data = await response.json();
                setOutput({
                    result: null,
                    logs: `Error: ${data.detail || 'Failed to start execution'}`,
                    exitCode: -1
                });
                return null;
            }

            if (!response.body) {
                throw new Error('No response body');
            }

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = '';

            try {
                while (true) {
                    const { done, value } = await reader.read();
                    if (done) break;

                    const chunk = decoder.decode(value, { stream: true });
                    buffer += chunk;

                    const lines = buffer.split('\n');
                    buffer = lines.pop() || '';

                    for (const line of lines) {
                        if (!line.trim()) continue;
                        try {
                            const event = JSON.parse(line);
                            if (event.type === 'start') {
                                setExecutionId(event.id);
                            } else if (event.type === 'stdout') {
                                setOutput(prev => ({
                                    ...prev!,
                                    result: (prev?.result || "") + event.data
                                }));
                            } else if (event.type === 'stderr') {
                                setOutput(prev => ({
                                    ...prev!,
                                    logs: (prev?.logs || "") + event.data
                                }));
                            } else if (event.type === 'exit') {
                                setOutput(prev => ({
                                    ...prev!,
                                    exitCode: event.code
                                }));
                            }
                        } catch (e) {
                            console.error('Error parsing JSON chunk', e);
                        }
                    }
                }
            } finally {
                reader.releaseLock();
            }
        } catch (e: any) {
            if (e.name === 'AbortError') {
                setOutput(prev => ({
                    ...prev!,
                    logs: (prev?.logs || "") + "\n[EXECUTION ABORTED]",
                    exitCode: 130
                }));
            } else {
                setOutput(prev => ({
                    ...prev!,
                    logs: (prev?.logs || "") + `\nError: ${e.message}`,
                    exitCode: -1
                }));
            }
        } finally {
            setExecuting(false);
            abortControllerRef.current = null;
        }
    }, []);

    const stopTool = useCallback(async (id: string) => {
        if (abortControllerRef.current) {
            abortControllerRef.current.abort();
        }

        try {
            await fetch(`/api/executions/execute/stop/${id}`, { method: 'POST' });
        } catch (e) {
            console.error("Failed to stop via API", e);
        }
    }, []);

    const followExecution = useCallback(async (fullId: string, path: string, existingJobId: string) => {
        setExecuting(true);
        setExecutionId(existingJobId);
        // We don't reset output here to allowed partial logs already loaded from DB to be augmented

        const abortController = new AbortController();
        abortControllerRef.current = abortController;

        try {
            const response = await fetch('/api/executions/execute/stream', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    tool_id: fullId,
                    path: path,
                    job_id: existingJobId,
                    arguments: {}
                }),
                signal: abortController.signal
            });

            if (!response.ok) return;
            if (!response.body) throw new Error('No response body');

            const reader = response.body.getReader();
            const decoder = new TextDecoder();
            let buffer = '';
            let firstChunk = true;

            try {
                while (true) {
                    const { done, value } = await reader.read();
                    if (done) break;

                    const chunk = decoder.decode(value, { stream: true });
                    buffer += chunk;
                    const lines = buffer.split('\n');
                    buffer = lines.pop() || '';

                    for (const line of lines) {
                        if (!line.trim()) continue;
                        try {
                            const event = JSON.parse(line);
                            if (event.type === 'stdout') {
                                setOutput(prev => ({
                                    ...prev!,
                                    result: (firstChunk ? "" : (prev?.result || "")) + event.data
                                }));
                                firstChunk = false;
                            } else if (event.type === 'stderr') {
                                setOutput(prev => ({
                                    ...prev!,
                                    logs: (firstChunk ? "" : (prev?.logs || "")) + event.data
                                }));
                                firstChunk = false;
                            } else if (event.type === 'exit') {
                                setOutput(prev => ({
                                    ...prev!,
                                    exitCode: event.code
                                }));
                            }
                        } catch (e) {
                            console.error('Error parsing JSON chunk', e);
                        }
                    }
                }
            } finally {
                reader.releaseLock();
            }
        } catch (e: any) {
            console.error("Follow execution error:", e);
        } finally {
            setExecuting(false);
            abortControllerRef.current = null;
        }
    }, []);

    return {
        executing,
        executionId,
        output,
        setOutput,
        setExecutionId,
        runTool,
        followExecution,
        stopTool,
        setExecuting
    };
};
