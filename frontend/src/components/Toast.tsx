import React, { createContext, useContext, useState, useCallback } from 'react';
import { CheckCircle, XCircle, AlertCircle, Info, X } from 'lucide-react';

export type ToastType = 'success' | 'error' | 'warning' | 'info';

export interface Toast {
    id: string;
    type: ToastType;
    message: string;
    duration?: number;
}

interface ToastContextType {
    toasts: Toast[];
    addToast: (type: ToastType, message: string, duration?: number) => void;
    removeToast: (id: string) => void;
    success: (message: string, duration?: number) => void;
    error: (message: string, duration?: number) => void;
    warning: (message: string, duration?: number) => void;
    info: (message: string, duration?: number) => void;
}

const ToastContext = createContext<ToastContextType | undefined>(undefined);

export const useToast = () => {
    const context = useContext(ToastContext);
    if (!context) {
        throw new Error('useToast must be used within ToastProvider');
    }
    return context;
};

export const ToastProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
    const [toasts, setToasts] = useState<Toast[]>([]);

    const removeToast = useCallback((id: string) => {
        setToasts(prev => prev.filter(t => t.id !== id));
    }, []);

    const addToast = useCallback((type: ToastType, message: string, duration: number = 5000) => {
        const id = Date.now().toString() + Math.random().toString(36);
        const toast: Toast = { id, type, message, duration };

        setToasts(prev => [...prev, toast]);

        // Auto remove after duration
        if (duration > 0) {
            setTimeout(() => {
                removeToast(id);
            }, duration);
        }
    }, [removeToast]);

    const success = useCallback((message: string, duration?: number) => {
        addToast('success', message, duration);
    }, [addToast]);

    const error = useCallback((message: string, duration?: number) => {
        addToast('error', message, duration);
    }, [addToast]);

    const warning = useCallback((message: string, duration?: number) => {
        addToast('warning', message, duration);
    }, [addToast]);

    const info = useCallback((message: string, duration?: number) => {
        addToast('info', message, duration);
    }, [addToast]);

    const contextValue = React.useMemo(() => ({
        toasts, addToast, removeToast, success, error, warning, info
    }), [toasts, addToast, removeToast, success, error, warning, info]);

    return (
        <ToastContext.Provider value={contextValue}>
            {children}
            <ToastContainer toasts={toasts} onRemove={removeToast} />
        </ToastContext.Provider>
    );
};

interface ToastItemProps {
    toast: Toast;
    onRemove: (id: string) => void;
}

const ToastItem: React.FC<ToastItemProps> = ({ toast, onRemove }) => {
    const getIcon = () => {
        switch (toast.type) {
            case 'success':
                return <CheckCircle size={20} className="flex-shrink-0" />;
            case 'error':
                return <XCircle size={20} className="flex-shrink-0" />;
            case 'warning':
                return <AlertCircle size={20} className="flex-shrink-0" />;
            case 'info':
                return <Info size={20} className="flex-shrink-0" />;
        }
    };

    const getStyles = () => {
        switch (toast.type) {
            case 'success':
                return 'bg-[#50fa7b] text-[#050101] border-[#50fa7b]';
            case 'error':
                return 'bg-[#ff5555] text-white border-[#ff5555]';
            case 'warning':
                return 'bg-[#ffb86c] text-[#050101] border-[#ffb86c]';
            case 'info':
                return 'bg-[#8be9fd] text-[#050101] border-[#8be9fd]';
        }
    };

    return (
        <div
            className={`
        ${getStyles()}
        rounded-lg shadow-lg border-2 px-4 py-3
        flex items-center gap-3 min-w-[300px] max-w-md
        animate-slide-in-right
      `}
        >
            {getIcon()}
            <span className="flex-1 font-mono text-sm font-medium">{toast.message}</span>
            <button
                onClick={() => onRemove(toast.id)}
                className="flex-shrink-0 hover:opacity-70 transition-opacity"
            >
                <X size={18} />
            </button>
        </div>
    );
};

interface ToastContainerProps {
    toasts: Toast[];
    onRemove: (id: string) => void;
}

const ToastContainer: React.FC<ToastContainerProps> = ({ toasts, onRemove }) => {
    return (
        <div className="fixed top-4 right-4 z-[9999] space-y-2 pointer-events-none">
            <div className="space-y-2 pointer-events-auto">
                {toasts.map(toast => (
                    <ToastItem key={toast.id} toast={toast} onRemove={onRemove} />
                ))}
            </div>
        </div>
    );
};
