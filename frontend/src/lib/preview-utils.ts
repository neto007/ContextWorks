import { type Argument } from '../components/ArgumentsBuilder';

export function generateYAML(
    toolName: string,
    description: string,
    arguments_: Argument[]
): string {
    let yaml = `name: ${toolName}\n`;
    yaml += `description: ${description || `Security tool: ${toolName}`}\n`;

    if (arguments_.length > 0) {
        yaml += `arguments:\n`;
        arguments_.forEach(arg => {
            yaml += `  - name: ${arg.name}\n`;
            yaml += `    type: ${arg.type}\n`;
            yaml += `    description: ${arg.description}\n`;
            yaml += `    required: ${arg.required}\n`;
            if (arg.default) {
                yaml += `    default: ${arg.default}\n`;
            }
        });
    }

    return yaml;
}

export function getCodePreview(code: string, maxLines: number = 20): string {
    const lines = code.split('\n');
    if (lines.length <= maxLines) {
        return code;
    }

    return lines.slice(0, maxLines).join('\n') + `\n\n... (${lines.length - maxLines} more lines)`;
}
