import type { Tool, BuildResult } from '../types/tool';

export const toolService = {
    async getAllTools(cacheBust = true): Promise<Record<string, Tool[]>> {
        const url = `/api/tools${cacheBust ? `?t=${Date.now()}` : ''}`;
        const res = await fetch(url);
        if (!res.ok) throw new Error('Failed to fetch tools');
        return res.json();
    },

    async getToolById(category: string, toolId: string): Promise<Tool> {
        const url = `/api/tools/${category}/${toolId}`;
        const res = await fetch(url);
        if (!res.ok) throw new Error(`Failed to fetch tool ${toolId}`);
        return res.json();
    },

    async createTool(toolData: any): Promise<{ tool: Tool; build_result?: BuildResult; id?: string }> {
        const res = await fetch('/api/tools', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(toolData)
        });
        if (!res.ok) {
            const error = await res.json();
            throw new Error(error.detail || 'Failed to create tool');
        }
        return res.json();
    },

    async updateTool(category: string, toolId: string, toolData: Partial<Tool>): Promise<{ tool: Tool; status: string; build_result?: BuildResult }> {
        const url = `/api/tools/${category}/${toolId}`;
        const res = await fetch(url, {
            method: 'PUT',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(toolData)
        });
        if (!res.ok) {
            const error = await res.json();
            throw new Error(error.detail || 'Failed to update tool');
        }
        return res.json();
    },

    async deleteTool(category: string, toolId: string): Promise<boolean> {
        const url = `/api/tools/${category}/${toolId}`;
        const res = await fetch(url, { method: 'DELETE' });
        return res.ok;
    },

    async uploadLogo(category: string, toolId: string, svgCode: string): Promise<boolean> {
        const url = `/api/tools/${category}/${toolId}/logo`;
        const res = await fetch(url, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ svg_code: svgCode })
        });
        return res.ok;
    },

    async getLogo(category: string, toolId: string): Promise<string | null> {
        const url = `/api/tools/${category}/${toolId}/logo`;
        const res = await fetch(url);
        if (res.ok) return res.text();
        return null;
    }
};
