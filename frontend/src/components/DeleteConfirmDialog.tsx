import React from 'react';
import { AlertTriangle, X } from 'lucide-react';
import { Button } from "@/components/ui/Button/Button";

interface DeleteConfirmDialogProps {
    isOpen: boolean;
    onClose: () => void;
    onConfirm: () => void;
    itemName: string;
    itemType?: string; // "tool", "workspace", etc.
    isDeleting?: boolean;
}

const DeleteConfirmDialog: React.FC<DeleteConfirmDialogProps> = ({
    isOpen,
    onClose,
    onConfirm,
    itemName,
    itemType = "item",
    isDeleting = false
}) => {
    if (!isOpen) return null;

    return (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 animate-fade-in">
            {/* Backdrop */}
            <div
                className="absolute inset-0 bg-black/80 backdrop-blur-sm"
                onClick={onClose}
            />

            {/* Dialog */}
            <div className="relative bg-gradient-to-br from-[#1a1b26] to-[#0b0b11] rounded-xl border-2 border-[#ff5555]/50 shadow-2xl max-w-md w-full animate-slide-in-bottom overflow-hidden">
                {/* Glow Effect */}
                <div className="absolute inset-0 bg-gradient-to-br from-[#ff5555]/10 to-transparent pointer-events-none" />

                {/* Header */}
                <div className="relative p-6 pb-4 border-b border-[#ff5555]/20">
                    <div className="flex items-start gap-4">
                        <div className="flex-shrink-0 w-12 h-12 rounded-full bg-[#ff5555]/20 flex items-center justify-center">
                            <AlertTriangle className="w-6 h-6 text-[#ff5555]" />
                        </div>
                        <div className="flex-1">
                            <h3 className="text-xl font-bold text-white mb-1">
                                Confirmar Exclusão
                            </h3>
                            <p className="text-sm text-[#6272a4]">
                                Esta ação não pode ser desfeita
                            </p>
                        </div>
                        <button
                            onClick={onClose}
                            className="flex-shrink-0 p-1 hover:bg-white/10 rounded transition-colors"
                            disabled={isDeleting}
                        >
                            <X size={20} className="text-[#6272a4] hover:text-white" />
                        </button>
                    </div>
                </div>

                {/* Content */}
                <div className="relative p-6">
                    <p className="text-[#f8f8f2] mb-4">
                        Tem certeza que deseja deletar {itemType === "tool" ? "a ferramenta" : "o item"}:
                    </p>

                    <div className="bg-[#0b0b11] border border-[#ff5555]/30 rounded-lg p-4 mb-6">
                        <p className="font-mono text-[#ff5555] font-bold break-all">
                            {itemName}
                        </p>
                    </div>

                    <div className="bg-[#ffb86c]/10 border border-[#ffb86c]/30 rounded-lg p-3 flex items-start gap-2">
                        <AlertTriangle size={16} className="text-[#ffb86c] flex-shrink-0 mt-0.5" />
                        <p className="text-xs text-[#ffb86c]">
                            {itemType === "tool"
                                ? "Todos os dados, configurações e histórico de execução serão permanentemente removidos."
                                : "Todos os dados associados serão permanentemente removidos."
                            }
                        </p>
                    </div>
                </div>

                {/* Footer */}
                <div className="relative p-6 pt-0 flex gap-3 justify-end">
                    <Button
                        onClick={onClose}
                        disabled={isDeleting}
                        variant="ghost"
                        className="bg-[#282a36] hover:bg-[#44475a] text-white font-mono"
                    >
                        Cancelar
                    </Button>
                    <Button
                        onClick={onConfirm}
                        disabled={isDeleting}
                        className="bg-gradient-to-r from-[#ff5555] to-[#ff6b6b] hover:from-[#ff6b6b] hover:to-[#ff5555] text-white font-bold uppercase tracking-wider border-b-4 border-[#cc0000] hover:border-[#cc0000] active:border-b-0 active:translate-y-1 transition-all disabled:opacity-50 disabled:cursor-not-allowed"
                    >
                        {isDeleting ? (
                            <>
                                <span className="animate-spin mr-2">⚙️</span>
                                Deletando...
                            </>
                        ) : (
                            'Deletar'
                        )}
                    </Button>
                </div>
            </div>
        </div>
    );
};

export default DeleteConfirmDialog;
