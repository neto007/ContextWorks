import React, { useState, useRef, useEffect } from 'react';

interface GlowImageProps extends React.ImgHTMLAttributes<HTMLImageElement> {
    radius?: number;
    spread?: number;
    brightness?: number;
    opacity?: number;
    passes?: number;
    onColorDetected?: (color: string) => void;
}

const GlowImage: React.FC<GlowImageProps> = ({
    src,
    alt,
    className,
    radius,
    spread,
    brightness,
    opacity = 0.6,
    onColorDetected,
    ...props
}) => {
    const [isLoaded, setIsLoaded] = useState(false);
    const imgRef = useRef<HTMLImageElement>(null);

    useEffect(() => {
        if (isLoaded && imgRef.current && onColorDetected) {
            try {
                // 1. Setup Canvas
                const canvas = document.createElement('canvas');
                const ctx = canvas.getContext('2d', { willReadFrequently: true });
                if (!ctx) return;

                const img = imgRef.current;
                // Use small size for performance and natural averaging
                canvas.width = 50;
                canvas.height = 50;

                // 2. Replicate the CSS Blur effect here!
                // BOOSTED Vibrancy: Hyper-saturate to extract neon-like colors
                ctx.filter = 'blur(10px) saturate(500%) brightness(130%)';
                ctx.drawImage(img, 0, 0, 50, 50);

                // 3. Sample the center pixel (which represents the average "glow")
                // Since it's heavily blurred, the center pixel is the perfect "dominant" mix
                const p = ctx.getImageData(25, 25, 1, 1).data;
                const hex = `#${((1 << 24) + (p[0] << 16) + (p[1] << 8) + p[2]).toString(16).slice(1)}`;

                onColorDetected(hex);
            } catch (error) {
                // Fallback to default purple silently
                onColorDetected('#bd93f9');
            }
        }
    }, [isLoaded, onColorDetected, src]);

    return (
        <div className={`relative inline-block ${className}`}>
            {/* Background Glow Layer - Blurred Duplicate */}
            {isLoaded && (
                <img
                    src={src}
                    alt=""
                    aria-hidden="true"
                    className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[102%] h-[102%] max-w-none object-contain blur-[2px] brightness-150 saturate-200 transition-opacity duration-700 z-0 pointer-events-none"
                    style={{ opacity: 1 }}
                />
            )}

            {/* Foreground Image */}
            <img
                ref={imgRef}
                src={src}
                alt={alt}
                crossOrigin="anonymous"
                className={`w-full h-full object-contain relative z-10 transition-opacity duration-300 ${isLoaded ? 'opacity-100' : 'opacity-0'}`}
                onLoad={() => setIsLoaded(true)}
                {...props}
            />
        </div>
    );
};

export default GlowImage;
