import * as React from "react"
import { cn } from "@/lib/utils"

const Card = React.forwardRef<
    HTMLDivElement,
    React.HTMLAttributes<HTMLDivElement> & {
        glowColor?: "cyan" | "green" | "yellow" | "purple" | "orange"
    }
>(({ className, glowColor, style, ...props }, ref) => {
    const glowStyles = glowColor ? {
        borderColor: {
            cyan: "#8be9fd",
            green: "#50fa7b",
            yellow: "#f1fa8c",
            purple: "#bd93f9",
            orange: "#ffb86c",
        }[glowColor],
        boxShadow: {
            cyan: "0 0 10px rgba(139,233,253,0.3), 0 0 20px rgba(139,233,253,0.1)",
            green: "0 0 10px rgba(80,250,123,0.3), 0 0 20px rgba(80,250,123,0.1)",
            yellow: "0 0 10px rgba(241,250,140,0.3), 0 0 20px rgba(241,250,140,0.1)",
            purple: "0 0 10px rgba(189,147,249,0.3), 0 0 20px rgba(189,147,249,0.1)",
            orange: "0 0 10px rgba(255,184,108,0.3), 0 0 20px rgba(255,184,108,0.1)",
        }[glowColor],
    } : {}

    return (
        <div
            ref={ref}
            className={cn(
                "rounded-lg border border-[#1a1b26] bg-[#0b0b11] text-[#f8f8f2] shadow-neu-sm",
                glowColor && "border-2",
                className
            )}
            style={{ ...glowStyles, ...style }}
            {...props}
        />
    )
})
Card.displayName = "Card"

const CardHeader = React.forwardRef<
    HTMLDivElement,
    React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
    <div
        ref={ref}
        className={cn("flex flex-col space-y-1.5 p-6", className)}
        {...props}
    />
))
CardHeader.displayName = "CardHeader"

const CardTitle = React.forwardRef<
    HTMLParagraphElement,
    React.HTMLAttributes<HTMLHeadingElement>
>(({ className, ...props }, ref) => (
    <h3
        ref={ref}
        className={cn(
            "text-2xl font-semibold leading-none tracking-tight",
            className
        )}
        {...props}
    />
))
CardTitle.displayName = "CardTitle"

const CardDescription = React.forwardRef<
    HTMLParagraphElement,
    React.HTMLAttributes<HTMLParagraphElement>
>(({ className, ...props }, ref) => (
    <p
        ref={ref}
        className={cn("text-sm text-muted-foreground", className)}
        {...props}
    />
))
CardDescription.displayName = "CardDescription"

const CardContent = React.forwardRef<
    HTMLDivElement,
    React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
    <div ref={ref} className={cn("p-6 pt-0", className)} {...props} />
))
CardContent.displayName = "CardContent"

const CardFooter = React.forwardRef<
    HTMLDivElement,
    React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
    <div
        ref={ref}
        className={cn("flex items-center p-6 pt-0", className)}
        {...props}
    />
))
CardFooter.displayName = "CardFooter"

export { Card, CardHeader, CardFooter, CardTitle, CardDescription, CardContent }
