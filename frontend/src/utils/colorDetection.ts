export const getDominantColor = (canvas: HTMLCanvasElement): string => {
    const ctx = canvas.getContext('2d', { willReadFrequently: true });
    if (!ctx) return '#bd93f9'; // Fallback to Dracula Purple

    const imageData = ctx.getImageData(0, 0, canvas.width, canvas.height);
    const data = imageData.data;

    let bestHex = '#bd93f9';
    let maxVibrance = -1;

    // Sample pixels to find the most vibrant one
    for (let i = 0; i < data.length; i += 16) { // Step 4 pixels for speed
        const r = data[i];
        const g = data[i + 1];
        const b = data[i + 2];
        const a = data[i + 3];

        if (a < 128) continue; // Skip semi-transparent pixels

        const brightness = (r + g + b) / 3;
        const saturation = Math.max(r, g, b) - Math.min(r, g, b);

        // Vibrance check: we want bright AND saturated colors
        // We weight saturation more heavily to avoid whites/grays
        const vibrance = saturation * saturation * brightness;

        if (vibrance > maxVibrance) {
            maxVibrance = vibrance;
            bestHex = `#${((1 << 24) + (r << 16) + (g << 8) + b).toString(16).slice(1)}`;
        }
    }

    return bestHex;
};

