import React from 'react';
import { Card, CardContent } from "@/components/ui/Card/Card";

export interface StatCardProps {
    icon: React.ComponentType<{ size?: number; className?: string }>;
    label: string;
    value: number;
    total: number;
    color: 'green' | 'red' | 'blue' | 'gray';
}

const StatCard: React.FC<StatCardProps> = ({ icon: Icon, label, value, total, color }) => {
    const percentage = total > 0 ? ((value / total) * 100).toFixed(1) : '0.0';

    const colorMap = {
        green: {
            bg: 'bg-[#50fa7b]/20',
            text: 'text-[#50fa7b]',
            border: 'border-[#50fa7b]',
        },
        red: {
            bg: 'bg-[#ff5555]/20',
            text: 'text-[#ff5555]',
            border: 'border-[#ff5555]',
        },
        blue: {
            bg: 'bg-[#8be9fd]/20',
            text: 'text-[#8be9fd]',
            border: 'border-[#8be9fd]',
        },
        gray: {
            bg: 'bg-[#6272a4]/20',
            text: 'text-[#6272a4]',
            border: 'border-[#6272a4]',
        },
    };

    const colors = colorMap[color];

    return (
        <Card className="border-[#44475a] hover:border-[#6272a4] transition-colors bg-[#1a1b26]/50">
            <CardContent className="p-6">
                <div className="flex items-center justify-between mb-4">
                    <div className={`p-3 rounded-lg ${colors.bg}`}>
                        <Icon size={24} className={colors.text} />
                    </div>
                    <div className={`text-xs px-2 py-1 rounded-full ${colors.bg} ${colors.text} font-bold`}>
                        {percentage}%
                    </div>
                </div>
                <div className="space-y-1">
                    <div className={`text-3xl font-bold ${colors.text}`}>
                        {value}
                    </div>
                    <div className="text-sm text-[#6272a4]">
                        {label}
                    </div>
                </div>
            </CardContent>
        </Card>
    );
};

export default StatCard;
