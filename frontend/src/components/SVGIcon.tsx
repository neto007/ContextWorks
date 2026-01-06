import React, { useEffect, useState } from 'react';
import { sanitizeSVG } from '@/lib/svg-utils';
import { FileIcon } from 'lucide-react';

interface SVGIconProps {
    svgCode?: string;
    svgUrl?: string;
    fallbackIcon?: React.ReactNode;
    size?: number;
    className?: string;
}

const SVGIcon: React.FC<SVGIconProps> = ({
    svgCode,
    svgUrl,
    fallbackIcon,
    size = 24,
    className = ''
}) => {
    const memoizedSvg = React.useMemo(() => {
        if (!svgCode) return null;
        try {
            return sanitizeSVG(svgCode);
        } catch (e) {
            console.error('Failed to sanitize SVG:', e);
            return null;
        }
    }, [svgCode]);

    const [fetchedSvg, setFetchedSvg] = useState<string | null>(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(false);

    useEffect(() => {
        if (svgUrl) {
            setLoading(true);
            fetch(svgUrl)
                .then(res => {
                    if (!res.ok) throw new Error('Failed to fetch SVG');
                    return res.text();
                })
                .then(text => {
                    const sanitized = sanitizeSVG(text);
                    setFetchedSvg(sanitized);
                    setError(false);
                })
                .catch(err => {
                    console.error('Failed to load SVG:', err);
                    setError(true);
                })
                .finally(() => setLoading(false));
        }
    }, [svgUrl]);

    const svg = svgCode ? memoizedSvg : fetchedSvg;

    if (loading) {
        return (
            <div
                className={`${className} flex items-center justify-center`}
                style={{ width: size, height: size }}
            >
                <div className="animate-spin rounded-full h-4 w-4 border-2 border-[#8be9fd] border-t-transparent" />
            </div>
        );
    }

    if (error || !svg) {
        return (
            <div style={{ width: size, height: size }}>
                {fallbackIcon || <FileIcon size={size} className="text-[#6272a4]" />}
            </div>
        );
    }

    return (
        <div
            className={`svg-icon ${className} [&>svg]:w-full [&>svg]:h-full`}
            style={{ width: size, height: size }}
            dangerouslySetInnerHTML={{ __html: svg }}
        />
    );
};

export default SVGIcon;
