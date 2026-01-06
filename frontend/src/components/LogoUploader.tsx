import React, { useState, useRef } from 'react';
import { Upload, X, FileCode } from 'lucide-react';
import { Button } from "@/components/ui/Button/Button";
import SVGIcon from './SVGIcon';
import { readSVGFile, isValidSVG } from '@/lib/svg-utils';
import { useToast } from './Toast';

interface LogoUploaderProps {
    currentLogo?: string;
    onLogoChange: (svgCode: string | null) => void;
    label?: string;
}

const LogoUploader: React.FC<LogoUploaderProps> = ({
    currentLogo,
    onLogoChange,
    label = "Logo (optional)"
}) => {
    const [svgCode, setSvgCode] = useState<string>(currentLogo || '');
    const [showCodeInput, setShowCodeInput] = useState(false);
    const fileInputRef = useRef<HTMLInputElement>(null);
    const toast = useToast();

    React.useEffect(() => {
        setSvgCode(currentLogo || '');
    }, [currentLogo]);

    const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
        const file = e.target.files?.[0];
        if (!file) return;

        try {
            const sanitizedSVG = await readSVGFile(file);
            setSvgCode(sanitizedSVG);
            onLogoChange(sanitizedSVG);
            toast.success('SVG logo uploaded successfully!');
        } catch (error) {
            toast.error(error instanceof Error ? error.message : 'Failed to upload SVG');
        }
    };

    const handleCodePaste = (code: string) => {
        if (!code.trim()) {
            setSvgCode('');
            onLogoChange(null);
            return;
        }

        if (!isValidSVG(code)) {
            toast.error('Invalid SVG code');
            return;
        }

        setSvgCode(code);
        onLogoChange(code);
        toast.success('SVG code applied!');
    };

    const handleRemoveLogo = () => {
        setSvgCode('');
        onLogoChange(null);
        setShowCodeInput(false);
        toast.info('Logo removed');
    };

    return (
        <div className="space-y-3">
            <label className="block text-sm font-mono text-[#6272a4] uppercase">
                {label}
            </label>

            {/* Preview & Actions */}
            <div className="flex items-center gap-3">
                {/* Preview */}
                <div className="w-16 h-16 bg-[#1a1b26] border border-[#282a36] rounded-lg flex items-center justify-center overflow-hidden relative">
                    {/* Transparency Grid */}
                    <div className="absolute inset-0 opacity-20" style={{
                        backgroundImage: `linear-gradient(45deg, #282a36 25%, transparent 25%), linear-gradient(-45deg, #282a36 25%, transparent 25%), linear-gradient(45deg, transparent 75%, #282a36 75%), linear-gradient(-45deg, transparent 75%, #282a36 75%)`,
                        backgroundSize: '10px 10px',
                        backgroundPosition: '0 0, 0 5px, 5px -5px, -5px 0px'
                    }} />

                    <div className="relative z-10">
                        {svgCode ? (
                            <SVGIcon svgCode={svgCode} size={40} />
                        ) : (
                            <Upload size={24} className="text-[#6272a4]" />
                        )}
                    </div>
                </div>

                {/* Actions */}
                <div className="flex flex-col gap-2">
                    <div className="flex gap-2">
                        <input
                            ref={fileInputRef}
                            type="file"
                            accept=".svg,image/svg+xml"
                            className="hidden"
                            onChange={handleFileUpload}
                        />

                        <Button
                            type="button"
                            size="sm"
                            onClick={() => fileInputRef.current?.click()}
                            className="text-xs bg-[#8be9fd]/20 hover:bg-[#8be9fd]/30 text-[#8be9fd] border border-[#8be9fd]/30"
                        >
                            <Upload size={14} className="mr-1" />
                            Upload SVG
                        </Button>

                        <Button
                            type="button"
                            size="sm"
                            onClick={() => setShowCodeInput(!showCodeInput)}
                            className="text-xs bg-[#bd93f9]/20 hover:bg-[#bd93f9]/30 text-[#bd93f9] border border-[#bd93f9]/30"
                        >
                            <FileCode size={14} className="mr-1" />
                            {showCodeInput ? 'Hide' : 'Paste'} Code
                        </Button>

                        {svgCode && (
                            <Button
                                type="button"
                                size="sm"
                                onClick={handleRemoveLogo}
                                className="text-xs bg-[#ff5555]/20 hover:bg-[#ff5555]/30 text-[#ff5555] border border-[#ff5555]/30"
                            >
                                <X size={14} className="mr-1" />
                                Remove
                            </Button>
                        )}
                    </div>

                    <p className="text-xs text-[#6272a4]">
                        {svgCode
                            ? `${(new Blob([svgCode]).size / 1024).toFixed(1)} KB`
                            : 'No logo set'
                        }
                    </p>
                </div>
            </div>

            {/* Code Input */}
            {showCodeInput && (
                <div>
                    <textarea
                        placeholder="Paste SVG code here... (e.g., <svg>...</svg>)"
                        value={svgCode}
                        onChange={(e) => handleCodePaste(e.target.value)}
                        className="w-full h-32 bg-[#1a1b26] border border-[#282a36] rounded px-3 py-2 text-white font-mono text-xs resize-none focus:outline-none focus:border-[#8be9fd]"
                    />
                    <p className="text-xs text-[#6272a4] mt-1">
                        SVG format only • Will be sanitized for security
                    </p>
                </div>
            )}
        </div>
    );
};

export default LogoUploader;
