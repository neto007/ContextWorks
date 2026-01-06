import React, { useEffect, useRef } from 'react';
import DOMPurify from 'dompurify';

const ansiToHtml = (text: string) => {
    const colors: Record<string, string> = {
        '30': '#282a36', // Black
        '31': '#ff5555', // Red
        '32': '#50fa7b', // Green
        '33': '#f1fa8c', // Yellow
        '34': '#bd93f9', // Blue (using purple for dracula)
        '35': '#ff79c6', // Magenta
        '36': '#8be9fd', // Cyan
        '37': '#f8f8f2', // White
        '90': '#6272a4', // Bright Black (Gray)
    };

    let html = text
        .replace(/\u001b\[0m/g, '</span>')
        .replace(/\u001b\[(\d+)m/g, (_match, code) => {
            const color = colors[code];
            return color ? `<span style="color: ${color}">` : '<span>';
        })
        .replace(/\[\s*\[(\d+)m/g, (_match, code) => {
            const color = colors[code];
            return color ? `<span style="color: ${color}">` : '<span>';
        })
        .replace(/\[0m\]/g, '</span>]')
        .replace(/\n/g, '<br/>');

    const openSpans = (html.match(/<span/g) || []).length;
    const closedSpans = (html.match(/<\/span/g) || []).length;
    for (let i = 0; i < openSpans - closedSpans; i++) {
        html += '</span>';
    }

    return html;
};

interface ExecutionLogsProps {
    logs: string;
    autoScroll?: boolean;
}

const ExecutionLogs: React.FC<ExecutionLogsProps> = ({ logs, autoScroll = true }) => {
    const logsEndRef = useRef<HTMLDivElement>(null);

    useEffect(() => {
        if (autoScroll) {
            logsEndRef.current?.scrollIntoView({ behavior: "smooth" });
        }
    }, [logs, autoScroll]);

    return (
        <div className="p-4 h-full overflow-auto custom-scrollbar font-mono text-xs leading-relaxed text-[#f8f8f2] whitespace-pre-wrap">
            <div
                dangerouslySetInnerHTML={{
                    __html: DOMPurify.sanitize(ansiToHtml(logs || ""))
                }}
            />
            {!logs && <span className="text-[#6272a4] italic">No logs available.</span>}
            <div ref={logsEndRef} />
        </div>
    );
};

export default ExecutionLogs;
