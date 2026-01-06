import React from 'react';
import { TrendingUp } from 'lucide-react';
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/Card/Card";

interface TopTool {
    tool_name: string;
    count: number;
}

interface TopToolsCardProps {
    tools: TopTool[];
}

const TopToolsCard: React.FC<TopToolsCardProps> = ({ tools }) => {
    return (
        <Card className="bg-[#1a1b26]/50 border-[#44475a]">
            <CardHeader>
                <CardTitle className="flex items-center gap-2">
                    <TrendingUp className="text-[#bd93f9]" size={20} />
                    Ferramentas Mais Usadas
                </CardTitle>
            </CardHeader>
            <CardContent>
                {tools.length === 0 ? (
                    <div className="text-center text-[#6272a4] py-8">
                        Nenhuma execução registrada
                    </div>
                ) : (
                    <div className="space-y-3">
                        {tools.map((tool, index) => (
                            <div
                                key={tool.tool_name}
                                className="flex items-center justify-between p-3 bg-[#282a36] rounded-lg border border-[#44475a] hover:border-[#6272a4] transition-colors"
                            >
                                <div className="flex items-center gap-3">
                                    <div className="w-6 h-6 rounded-full bg-[#bd93f9]/20 flex items-center justify-center">
                                        <span className="text-xs font-bold text-[#bd93f9]">
                                            {index + 1}
                                        </span>
                                    </div>
                                    <span className="text-[#f8f8f2] font-mono text-sm">
                                        {tool.tool_name}
                                    </span>
                                </div>
                                <div className="flex items-center gap-2">
                                    <span className="text-xs px-2 py-1 rounded-full bg-[#8be9fd]/20 text-[#8be9fd] font-bold">
                                        {tool.count}
                                    </span>
                                    <div className="w-24 bg-[#44475a] rounded-full h-2">
                                        <div
                                            className="bg-gradient-to-r from-[#bd93f9] to-[#8be9fd] h-2 rounded-full transition-all"
                                            style={{ width: `${(tool.count / tools[0].count) * 100}%` }}
                                        />
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

export default TopToolsCard;
