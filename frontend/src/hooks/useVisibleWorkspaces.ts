import { useState, useEffect } from 'react';

interface Workspace {
    name: string;
    is_visible?: boolean;
}

export function useVisibleWorkspaces(allWorkspaces: Workspace[]) {
    const [visibleWorkspaces, setVisibleWorkspaces] = useState<Set<string>>(new Set());

    // Sync com os workspaces vindos das props (enviadas pelo backend)
    useEffect(() => {
        const visible = allWorkspaces
            .filter(ws => ws.is_visible !== false)
            .map(ws => ws.name);
        setVisibleWorkspaces(new Set(visible));
    }, [allWorkspaces]);

    const toggleWorkspace = async (workspaceName: string) => {
        const currentlyVisible = visibleWorkspaces.has(workspaceName);
        const nextVisibility = !currentlyVisible;

        // Otimistic update
        setVisibleWorkspaces(prev => {
            const next = new Set(prev);
            if (currentlyVisible) next.delete(workspaceName);
            else next.add(workspaceName);
            return next;
        });

        try {
            const response = await fetch(`/api/workspaces/${workspaceName}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ is_visible: nextVisibility })
            });

            if (!response.ok) throw new Error('Failed to update visibility');
        } catch (error) {
            console.error('Error toggling workspace visibility:', error);
            // Revert on error
            setVisibleWorkspaces(prev => {
                const next = new Set(prev);
                if (currentlyVisible) next.add(workspaceName);
                else next.delete(workspaceName);
                return next;
            });
        }
    };

    const isVisible = (workspaceName: string) => visibleWorkspaces.has(workspaceName);

    const showAll = async () => {
        // Atualiza todos para visível no backend
        const promises = allWorkspaces.map(ws =>
            fetch(`/api/workspaces/${ws.name}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ is_visible: true })
            })
        );

        const next = new Set(allWorkspaces.map(ws => ws.name));
        setVisibleWorkspaces(next);

        try {
            await Promise.all(promises);
        } catch (e) {
            console.error('Error showing all workspaces:', e);
        }
    };

    const hideAll = async () => {
        const promises = allWorkspaces.map(ws =>
            fetch(`/api/workspaces/${ws.name}`, {
                method: 'PUT',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ is_visible: false })
            })
        );

        setVisibleWorkspaces(new Set());

        try {
            await Promise.all(promises);
        } catch (e) {
            console.error('Error hiding all workspaces:', e);
        }
    };

    return {
        visibleWorkspaces,
        toggleWorkspace,
        isVisible,
        showAll,
        hideAll
    };
}
