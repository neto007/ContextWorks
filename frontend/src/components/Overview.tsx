import React, { useEffect, useState } from 'react';
import { Activity, CheckCircle, XCircle, Clock, BarChart3, Server, Package, FolderOpen, Wrench } from 'lucide-react';
import type { DashboardData } from '../types/dashboard.types';
import PlatformCard from './dashboard/PlatformCard';
import StatCard from './dashboard/StatCard';
import TopToolsCard from './dashboard/TopToolsCard';
import PerformanceCard from './dashboard/PerformanceCard';

const Overview: React.FC = () => {
    const [data, setData] = useState<DashboardData | null>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        fetch('/api/executions/stats')
            .then(res => res.json())
            .then(responseData => {
                setData(responseData);
                setLoading(false);
            })
            .catch(err => {
                console.error("Failed to fetch stats:", err);
                setLoading(false);
            });
    }, []);

    if (loading) {
        return (
            <div className="max-w-7xl mx-auto space-y-6">
                <div className="flex items-center justify-center py-12">
                    <Activity className="text-[#8be9fd] animate-spin" size={32} />
                </div>
            </div>
        );
    }

    if (!data) {
        return (
            <div className="max-w-7xl mx-auto space-y-6">
                <div className="text-center text-[#6272a4] py-8">
                    Não foi possível carregar as estatísticas.
                </div>
            </div>
        );
    }

    const { platform, executions } = data;

    return (
        <div className="max-w-7xl mx-auto space-y-8 animate-in fade-in duration-500">
            {/* Platform Overview Section */}
            <section>
                <h2 className="text-2xl font-bold text-white mb-6 flex items-center gap-2">
                    <BarChart3 className="text-[#8be9fd]" />
                    Visão Geral da Plataforma
                </h2>

                <div className="grid grid-cols-[repeat(auto-fill,minmax(220px,1fr))] gap-4">
                    <PlatformCard
                        icon={Server}
                        label="MCP Servers"
                        value={platform.mcp_servers.total}
                        subtitle={`${platform.mcp_servers.active} ativos · ${platform.mcp_servers.connections} conexões`}
                        color="purple"
                    />
                    <PlatformCard
                        icon={Package}
                        label="Builds"
                        value={platform.builds.total}
                        subtitle={`${platform.builds.success} sucesso · ${platform.builds.failed} falhas`}
                        color="orange"
                    />
                    <PlatformCard
                        icon={FolderOpen}
                        label="Workspaces"
                        value={platform.workspaces}
                        subtitle="Total cadastrados"
                        color="cyan"
                    />
                    <PlatformCard
                        icon={Wrench}
                        label="Tools"
                        value={platform.tools}
                        subtitle="Ferramentas disponíveis"
                        color="yellow"
                    />
                </div>
            </section>

            {/* Execution Stats Section */}
            <section>
                <div className="flex items-center justify-between mb-6">
                    <h2 className="text-2xl font-bold text-white flex items-center gap-2">
                        <Activity className="text-[#50fa7b]" />
                        Estatísticas de Execuções
                    </h2>
                    <div className="text-sm text-[#6272a4] font-mono">
                        Total: <span className="text-[#f8f8f2] font-bold">{executions.total}</span>
                    </div>
                </div>

                <div className="grid grid-cols-[repeat(auto-fill,minmax(220px,1fr))] gap-4 mb-8">
                    <StatCard
                        icon={CheckCircle}
                        label="Sucessos"
                        value={executions.by_status.success}
                        total={executions.total}
                        color="green"
                    />
                    <StatCard
                        icon={XCircle}
                        label="Falhas"
                        value={executions.by_status.failed}
                        total={executions.total}
                        color="red"
                    />
                    <StatCard
                        icon={Activity}
                        label="Em Execução"
                        value={executions.by_status.running}
                        total={executions.total}
                        color="blue"
                    />
                    <StatCard
                        icon={Clock}
                        label="Paradas"
                        value={executions.by_status.stopped}
                        total={executions.total}
                        color="gray"
                    />
                </div>

                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    <TopToolsCard tools={executions.top_tools} />
                    <PerformanceCard durations={executions.avg_durations} />
                </div>
            </section>
        </div>
    );
};

export default Overview;

