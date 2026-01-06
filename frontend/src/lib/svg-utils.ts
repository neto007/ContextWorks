import DOMPurify from 'dompurify';

/**
 * Sanitiza código SVG removendo scripts e event handlers perigosos
 */
export function sanitizeSVG(svgCode: string): string {
    // Configurar DOMPurify para SVG
    const clean = DOMPurify.sanitize(svgCode, {
        USE_PROFILES: { svg: true, svgFilters: true },
        ADD_TAGS: ['use'],
        ADD_ATTR: ['xlink:href']
    });

    // Parse e remove scripts manualmente (double check)
    const parser = new DOMParser();
    const doc = parser.parseFromString(clean, 'image/svg+xml');

    // Remove qualquer tag script
    const scripts = doc.querySelectorAll('script');
    scripts.forEach(s => s.remove());

    // Remove event handlers (onclick, onerror, etc)
    const allElements = doc.querySelectorAll('*');
    allElements.forEach(el => {
        Array.from(el.attributes).forEach(attr => {
            if (attr.name.startsWith('on')) {
                el.removeAttribute(attr.name);
            }
        });
    });

    return new XMLSerializer().serializeToString(doc);
}

/**
 * Valida se uma string é um SVG válido
 */
export function isValidSVG(svgCode: string): boolean {
    try {
        const parser = new DOMParser();
        const doc = parser.parseFromString(svgCode, 'image/svg+xml');

        // Verificar se há erros de parsing
        const errorNode = doc.querySelector('parsererror');
        if (errorNode) {
            return false;
        }

        // Verificar se o elemento root é <svg>
        const svgElement = doc.documentElement;
        if (svgElement.tagName.toLowerCase() !== 'svg') {
            return false;
        }

        return true;
    } catch (_e) {
        return false;
    }
}

/**
 * Valida tamanho do SVG (em bytes)
 */
export function isValidSVGSize(svgCode: string, maxSizeKB: number = 100): boolean {
    const sizeBytes = new Blob([svgCode]).size;
    const sizeKB = sizeBytes / 1024;
    return sizeKB <= maxSizeKB;
}

/**
 * Lê arquivo SVG e retorna código sanitizado
 */
export async function readSVGFile(file: File): Promise<string> {
    return new Promise((resolve, reject) => {
        // Check mime type OR extension
        if (!file.type.includes('svg') && !file.name.toLowerCase().endsWith('.svg')) {
            reject(new Error('File must be SVG format'));
            return;
        }

        const reader = new FileReader();
        reader.onload = (e) => {
            const content = e.target?.result as string;

            if (!isValidSVG(content)) {
                reject(new Error('Invalid SVG format'));
                return;
            }

            const sanitized = sanitizeSVG(content);
            resolve(sanitized);
        };
        reader.onerror = () => reject(new Error('Failed to read file'));
        reader.readAsText(file);
    });
}

/**
 * Extrai viewBox de um SVG para redimensionamento correto
 */
export function extractViewBox(svgCode: string): string | null {
    const parser = new DOMParser();
    const doc = parser.parseFromString(svgCode, 'image/svg+xml');
    const svgElement = doc.documentElement;
    return svgElement.getAttribute('viewBox');
}
