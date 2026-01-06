import React from 'react';
import { Card, CardContent } from "@/components/ui/Card/Card";

export interface PlatformCardProps {
    icon: React.ComponentType<{ size?: number; className?: string }>;
    label: string;
    value: number;
    subtitle: string;
    color: 'purple' | 'orange' | 'cyan' | 'yellow';
}

const PlatformCard: React.FC<PlatformCardProps> = ({ icon: Icon, label, value, subtitle, color }) => {
    const colorMap = {
        purple: {
            bg: 'bg-[#bd93f9]/20',
            text: 'text-[#bd93f9]',
            icon: 'text-[#bd93f9]',
        },
        orange: {
            bg: 'bg-[#ffb86c]/20',
            text: 'text-[#ffb86c]',
            icon: 'text-[#ffb86c]',
        },
        cyan: {
            bg: 'bg-[#8be9fd]/20',
            text: 'text-[#8be9fd]',
            icon: 'text-[#8be9fd]',
        },
        yellow: {
            bg: 'bg-[#f1fa8c]/20',
            text: 'text-[#f1fa8c]',
            icon: 'text-[#f1fa8c]',
        },
    };

    const colors = colorMap[color];

    return (
        <Card className="border-[#44475a] hover:border-[#6272a4] transition-colors bg-[#1a1b26]/50">
            <CardContent className="p-6">
                <div className="flex items-center gap-4 mb-4">
                    <div className={`p-3 rounded-lg ${colors.bg}`}>
                        <Icon size={24} className={colors.icon} />
                    </div>
                    <div className="flex-1">
                        <div className={`text-3xl font-bold ${colors.text}`}>
                            {value}
                        </div>
                        <div className="text-sm text-[#6272a4]">
                            {label}
                        </div>
                    </div>
                </div>
                <div className="text-xs text-[#6272a4] border-t border-[#44475a] pt-3">
                    {subtitle}
                </div>
            </CardContent>
        </Card>
    );
};

export default PlatformCard;
