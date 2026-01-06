import React from 'react';
import { Zap } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/Card/Card";

interface AvgDuration {
    tool_name: string;
    execution_count: number;
    avg_duration_seconds: number;
}

interface PerformanceCardProps {
    durations: AvgDuration[];
}

const PerformanceCard: React.FC<PerformanceCardProps> = ({ durations }) => {
    const formatDuration = (seconds: number) => {
        if (seconds < 1) return `${(seconds * 1000).toFixed(0)}ms`;
        if (seconds < 60) return `${seconds.toFixed(1)}s`;
        const mins = Math.floor(seconds / 60);
        const secs = Math.floor(seconds % 60);
        return `${mins}m ${secs}s`;
    };

    return (
        <Card className="bg-[#1a1b26]/50 border-[#44475a]">
            <CardHeader>
                <CardTitle className="flex items-center gap-2">
                    <Zap className="text-[#f1fa8c]" size={20} />
                    Performance Média
                </CardTitle>
            </CardHeader>
            <CardContent>
                {durations.length === 0 ? (
                    <div className="text-center text-[#6272a4] py-8">
                        Nenhuma execução finalizada
                    </div>
                ) : (
                    <div className="space-y-3">
                        {durations.slice(0, 10).map((tool) => (
                            <div
                                key={tool.tool_name}
                                className="flex items-center justify-between p-3 bg-[#282a36] rounded-lg border border-[#44475a] hover:border-[#6272a4] transition-colors"
                            >
                                <div className="flex-1">
                                    <div className="text-[#f8f8f2] font-mono text-sm mb-1">
                                        {tool.tool_name}
                                    </div>
                                    <div className="text-xs text-[#6272a4]">
                                        {tool.execution_count} execuç{tool.execution_count === 1 ? 'ão' : 'ões'}
                                    </div>
                                </div>
                                <div className="text-right">
                                    <div className={`text-sm font-bold ${tool.avg_duration_seconds < 5 ? 'text-[#50fa7b]' :
                                        tool.avg_duration_seconds < 30 ? 'text-[#f1fa8c]' :
                                            'text-[#ffb86c]'
                                        }`}>
                                        {formatDuration(tool.avg_duration_seconds)}
                                    </div>
                                    <div className="text-xs text-[#6272a4]">
                                        tempo médio
                                    </div>
                                </div>
                            </div>
                        ))}
                    </div>
                )}
            </CardContent>
        </Card>
    );
};

export default PerformanceCard;
