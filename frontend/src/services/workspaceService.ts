import type { Workspace } from '../types/workspace';

export const workspaceService = {
    async getAllWorkspaces(cacheBust = true): Promise<Workspace[]> {
        const url = `/api/workspaces${cacheBust ? `?t=${Date.now()}` : ''}`;
        const res = await fetch(url);
        if (!res.ok) throw new Error('Failed to fetch workspaces');
        return res.json();
    },

    async createWorkspace(name: string, description: string): Promise<boolean> {
        const res = await fetch('/api/workspaces', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name, description })
        });
        return res.ok;
    },

    async updateWorkspace(oldName: string, data: Partial<Workspace>): Promise<boolean> {
        const res = await fetch(`/api/workspaces/${oldName}`, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        return res.ok;
    },

    async deleteWorkspace(name: string): Promise<boolean> {
        const res = await fetch(`/api/workspaces/${name}`, { method: 'DELETE' });
        return res.ok;
    },

    async uploadLogo(name: string, svgCode: string): Promise<boolean> {
        const res = await fetch(`/api/workspaces/${name}/logo`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ svg_code: svgCode })
        });
        return res.ok;
    },

    async getLogo(name: string): Promise<string | null> {
        const res = await fetch(`/api/workspaces/${name}/logo`);
        if (res.ok) return res.text();
        return null;
    }
};
