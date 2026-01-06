export interface ValidationResult {
    valid: boolean;
    errors: string[];
    warnings: string[];
}

export function validatePythonCode(code: string): ValidationResult {
    const errors: string[] = [];
    const warnings: string[] = [];

    // Check if code is empty
    if (!code.trim()) {
        errors.push('Script code cannot be empty');
        return { valid: false, errors, warnings };
    }

    // Check for main function
    if (!code.includes('def main(')) {
        errors.push('Missing main() function - required for tool execution');
    }

    // Check for if __name__ == "__main__"
    if (!code.includes('if __name__')) {
        errors.push('Missing if __name__ == "__main__" block');
    }

    // Check for dangerous imports/functions
    const dangerousPatterns = [
        { pattern: 'os.system', message: 'os.system() - use subprocess instead' },
        { pattern: 'eval(', message: 'eval() - dangerous code execution' },
        { pattern: 'exec(', message: 'exec() - dangerous code execution' },
        { pattern: '__import__', message: '__import__ - potential security risk' },
        { pattern: 'compile(', message: 'compile() - potential security risk' },
    ];

    dangerousPatterns.forEach(({ pattern, message }) => {
        if (code.includes(pattern)) {
            warnings.push(`Potentially dangerous: ${message}`);
        }
    });

    // Check for basic Python syntax issues
    const lines = code.split('\n');
    lines.forEach((line, idx) => {
        const trimmed = line.trim();

        // Function definition without colon
        if (trimmed.startsWith('def ') && !trimmed.includes(':')) {
            errors.push(`Line ${idx + 1}: Missing colon after function definition`);
        }

        // Class definition without colon
        if (trimmed.startsWith('class ') && !trimmed.includes(':')) {
            errors.push(`Line ${idx + 1}: Missing colon after class definition`);
        }

        // If/elif/else without colon
        if ((trimmed.startsWith('if ') || trimmed.startsWith('elif ') || trimmed === 'else') &&
            !trimmed.includes(':') && !trimmed.includes('#')) {
            errors.push(`Line ${idx + 1}: Missing colon after conditional statement`);
        }

        // For/while without colon
        if ((trimmed.startsWith('for ') || trimmed.startsWith('while ')) &&
            !trimmed.includes(':')) {
            errors.push(`Line ${idx + 1}: Missing colon after loop statement`);
        }
    });

    // Check for mismatched quotes (very basic)
    const singleQuotes = (code.match(/'/g) || []).length;
    const doubleQuotes = (code.match(/"/g) || []).length;
    const tripleQuotes = (code.match(/"""/g) || []).length;


    if (singleQuotes % 2 !== 0) {
        warnings.push('Possible unmatched single quotes');
    }
    if ((doubleQuotes - tripleQuotes * 3) % 2 !== 0) {
        warnings.push('Possible unmatched double quotes');
    }

    // Check for print statement (Python 2 syntax)
    if (/\bprint\s+[^(]/.test(code)) {
        warnings.push('Using Python 2 print statement - use print() function instead');
    }

    // Check for common imports that should be present
    if (code.includes('json.dumps') || code.includes('json.loads')) {
        if (!code.includes('import json')) {
            errors.push('Using json methods but missing "import json"');
        }
    }

    if (code.includes('sys.argv')) {
        if (!code.includes('import sys')) {
            errors.push('Using sys.argv but missing "import sys"');
        }
    }

    return {
        valid: errors.length === 0,
        errors,
        warnings
    };
}

export function getValidationSeverity(result: ValidationResult): 'success' | 'warning' | 'error' {
    if (!result.valid) return 'error';
    if (result.warnings.length > 0) return 'warning';
    return 'success';
}

export function getValidationMessage(result: ValidationResult): string {
    if (!result.valid) {
        return `${result.errors.length} error${result.errors.length > 1 ? 's' : ''} found`;
    }
    if (result.warnings.length > 0) {
        return `${result.warnings.length} warning${result.warnings.length > 1 ? 's' : ''}`;
    }
    return 'All validation checks passed';
}
