export interface PlatformStats {
    mcp_servers: {
        total: number;
        active: number;
        connections: number;
    };
    builds: {
        total: number;
        success: number;
        failed: number;
        pending: number;
    };
    workspaces: number;
    tools: number;
}

export interface ExecutionStats {
    total: number;
    by_status: {
        success: number;
        failed: number;
        running: number;
        stopped: number;
    };
    top_tools: Array<{
        tool_name: string;
        count: number;
    }>;
    avg_durations: Array<{
        tool_name: string;
        execution_count: number;
        avg_duration_seconds: number;
    }>;
}

export interface DashboardData {
    platform: PlatformStats;
    executions: ExecutionStats;
}
