import { useState, useEffect } from 'react';

export function useSidebarState() {
    const [isCollapsed, setIsCollapsed] = useState(() => {
        const stored = localStorage.getItem('sidebar_collapsed');
        return stored === 'true';
    });

    const toggleSidebar = () => {
        setIsCollapsed(prev => {
            const newValue = !prev;
            localStorage.setItem('sidebar_collapsed', String(newValue));
            return newValue;
        });
    };

    useEffect(() => {
        // Debounce function to limit execution frequency
        const debounce = (func: Function, wait: number) => {
            let timeout: NodeJS.Timeout;
            return (...args: any[]) => {
                clearTimeout(timeout);
                timeout = setTimeout(() => func(...args), wait);
            };
        };

        // Auto-collapse on mobile/tablet
        const handleResize = debounce(() => {
            if (window.innerWidth < 768) {
                setIsCollapsed(true);
            }
        }, 150);

        // Initial check
        handleResize();

        window.addEventListener('resize', handleResize);

        // Sync with localStorage changes from other tabs
        const handleStorageChange = (e: StorageEvent) => {
            if (e.key === 'sidebar_collapsed') {
                setIsCollapsed(e.newValue === 'true');
            }
        };

        window.addEventListener('storage', handleStorageChange);
        return () => {
            window.removeEventListener('resize', handleResize);
            window.removeEventListener('storage', handleStorageChange);
        };
    }, []);

    return { isCollapsed, toggleSidebar };
}
