/** @type {import('tailwindcss').Config} */
export default {
    content: [
        "./index.html",
        "./src/**/*.{js,ts,jsx,tsx}",
    ],
    theme: {
        extend: {
            colors: {
                // Dracula Palette (FlowSec)
                'dracula-bg': '#050101',
                'dracula-current': '#1a1b26',
                'dracula-selection': '#282a36',
                'dracula-foreground': '#f8f8f2',
                'dracula-comment': '#6272a4',
                'dracula-cyan': '#8be9fd',
                'dracula-green': '#50fa7b',
                'dracula-orange': '#ffb86c',
                'dracula-pink': '#ff79c6',
                'dracula-purple': '#bd93f9',
                'dracula-red': '#ff5555',
                'dracula-yellow': '#f1fa8c',

                // Design System Aliases
                background: '#050101',
                foreground: '#f8f8f2',
                card: {
                    DEFAULT: '#0b0b11',
                    foreground: '#f8f8f2'
                },
                popover: {
                    DEFAULT: '#282a36',
                    foreground: '#f8f8f2'
                },
                primary: {
                    DEFAULT: '#bd93f9',
                    foreground: '#282a36'
                },
                secondary: {
                    DEFAULT: '#1a1b26',
                    foreground: '#f8f8f2'
                },
                muted: {
                    DEFAULT: '#1a1b26',
                    foreground: '#6272a4'
                },
                accent: {
                    DEFAULT: '#44475a',
                    foreground: '#f8f8f2'
                },
                destructive: {
                    DEFAULT: '#ff5555',
                    foreground: '#f8f8f2'
                },
                border: '#1a1b26',
                input: '#1a1b26',
                ring: '#bd93f9',
            },
            boxShadow: {
                'neu': '4px 4px 0px 0px rgba(0,0,0,1)',
                'neu-sm': '2px 2px 0px 0px rgba(0,0,0,1)',
                'neu-purple': '4px 4px 0px 0px #bd93f9',
                'neu-green': '4px 4px 0px 0px #50fa7b',
            },
            borderRadius: {
                lg: '0.75rem',
                md: '0.5rem',
                sm: '0.25rem',
            },
            keyframes: {
                wiggle: {
                    '0%, 100%': { transform: 'rotate(-3deg)' },
                    '50%': { transform: 'rotate(3deg)' },
                },
                'squash': {
                    '0%': { transform: 'scale(1)' },
                    '50%': { transform: 'scale(0.95, 1.05)' },
                    '100%': { transform: 'scale(1)' },
                }
            },
            animation: {
                wiggle: 'wiggle 1s ease-in-out infinite',
                squash: 'squash 0.2s ease-in-out',
            }
        },
    },
    plugins: [
        require("tailwindcss-animate")
    ],
}
