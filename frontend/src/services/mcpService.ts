export interface MCPServer {
    id: string;
    name: string;
    url: string;
    description?: string;
    status: 'active' | 'inactive' | 'error';
    config?: any;
}

export const mcpService = {
    async getAllMCPs(cacheBust = true): Promise<MCPServer[]> {
        const url = `/api/mcps${cacheBust ? `?t=${Date.now()}` : ''}`;
        const res = await fetch(url);
        if (!res.ok) throw new Error('Failed to fetch MCP servers');
        return res.json();
    },

    async createMCP(data: any): Promise<boolean> {
        const res = await fetch('/api/mcps', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(data)
        });
        return res.ok;
    },

    async deleteMCP(id: string): Promise<boolean> {
        const res = await fetch(`/api/mcps/${id}`, { method: 'DELETE' });
        return res.ok;
    }
};
