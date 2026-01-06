import * as React from "react"
import { Slot } from "@radix-ui/react-slot"
import { cva, type VariantProps } from "class-variance-authority"

import { cn } from "@/lib/utils"

const buttonVariants = cva(
    "inline-flex items-center justify-center whitespace-nowrap text-[10px] font-black uppercase tracking-widest transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:pointer-events-none disabled:opacity-50 rounded",
    {
        variants: {
            variant: {
                default: "bg-[#bd93f9] hover:bg-[#ff79c6] text-black shadow-[0_0_15px_rgba(189,147,249,0.3)] hover:shadow-[0_0_20px_rgba(255,121,198,0.4)]",
                destructive:
                    "bg-[#ff5555] hover:bg-[#ff5555]/80 text-[#f8f8f2] shadow-[0_0_15px_rgba(255,85,85,0.3)] hover:shadow-[0_0_20px_rgba(255,85,85,0.4)]",
                outline:
                    "border border-[#1a1b26] bg-transparent hover:bg-[#1a1b26] text-[#f8f8f2]",
                secondary:
                    "bg-[#1a1b26] text-[#f8f8f2] hover:bg-[#282a36]",
                ghost: "hover:bg-[#1a1b26] text-[#6272a4] hover:text-[#bd93f9]",
                link: "text-[#bd93f9] underline-offset-4 hover:underline",
                success: "bg-[#50fa7b] hover:bg-[#8be9fd] text-black shadow-[0_0_15px_rgba(80,250,123,0.3)] hover:shadow-[0_0_20px_rgba(139,233,253,0.4)]",
                warning: "bg-[#ffb86c] hover:bg-[#f1fa8c] text-black shadow-[0_0_15px_rgba(255,184,108,0.3)] hover:shadow-[0_0_20px_rgba(241,250,140,0.4)]",
                // Duolingo 3D style buttons
                duolingoCyan: "bg-[#8be9fd] hover:bg-[#8be9fd] text-[#050101] tracking-wider rounded-xl border-b-4 border-[#41a0b3] hover:border-[#41a0b3] active:border-b-0 active:translate-y-1",
                duolingoGreen: "bg-[#50fa7b] hover:bg-[#50fa7b] text-[#050101] tracking-wider rounded-xl border-b-4 border-[#2aa34a] hover:border-[#2aa34a] active:border-b-0 active:translate-y-1",
                duolingoYellow: "bg-[#f1fa8c] hover:bg-[#f1fa8c] text-[#050101] tracking-wider rounded-xl border-b-4 border-[#c7d04f] hover:border-[#c7d04f] active:border-b-0 active:translate-y-1",
                duolingoPurple: "bg-[#bd93f9] hover:bg-[#bd93f9] text-[#050101] tracking-wider rounded-xl border-b-4 border-[#7e4db3] hover:border-[#7e4db3] active:border-b-0 active:translate-y-1",
                duolingoOrange: "bg-[#ffb86c] hover:bg-[#ffb86c] text-[#050101] tracking-wider rounded-xl border-b-4 border-[#d49748] hover:border-[#d49748] active:border-b-0 active:translate-y-1",
            },
            size: {
                default: "h-10 px-4 py-3",
                sm: "h-9 px-3 py-2",
                lg: "h-11 px-8 py-3",
                icon: "h-10 w-10",
            },
        },
        defaultVariants: {
            variant: "default",
            size: "default",
        },
    }
)

export interface ButtonProps
    extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof buttonVariants> {
    asChild?: boolean
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
    ({ className, variant, size, asChild = false, ...props }, ref) => {
        const Comp = asChild ? Slot : "button"
        return (
            <Comp
                className={cn(buttonVariants({ variant, size, className }))}
                ref={ref}
                {...props}
            />
        )
    }
)
Button.displayName = "Button"

export { Button, buttonVariants }
