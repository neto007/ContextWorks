import * as React from "react"
import { cva, type VariantProps } from "class-variance-authority"
import { cn } from "@/lib/utils"
import { ScrollArea } from "@/components/ui/ScrollArea/ScrollArea"

const Sidebar = React.forwardRef<
    HTMLElement,
    React.HTMLAttributes<HTMLElement>
>(({ className, ...props }, ref) => (
    <aside
        ref={ref}
        className={cn(
            "flex flex-col hidden border-r border-[#1a1b26] bg-[#050101] md:block md:w-64 lg:w-72 h-screen overflow-hidden",
            className
        )}
        {...props}
    />
))
Sidebar.displayName = "Sidebar"

const SidebarHeader = React.forwardRef<
    HTMLDivElement,
    React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
    <div
        ref={ref}
        className={cn("flex h-14 items-center border-b border-[#1a1b26] px-6", className)}
        {...props}
    />
))
SidebarHeader.displayName = "SidebarHeader"

const SidebarContent = React.forwardRef<
    HTMLDivElement,
    React.HTMLAttributes<HTMLDivElement>
>(({ className, children, ...props }, ref) => (
    <ScrollArea className="flex-1">
        <div
            ref={ref}
            className={cn("p-4 space-y-4", className)}
            {...props}
        >
            {children}
        </div>
    </ScrollArea>
))
SidebarContent.displayName = "SidebarContent"

const SidebarFooter = React.forwardRef<
    HTMLDivElement,
    React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
    <div
        ref={ref}
        className={cn("p-4 border-t border-[#1a1b26]", className)}
        {...props}
    />
))
SidebarFooter.displayName = "SidebarFooter"

const SidebarGroup = React.forwardRef<
    HTMLDivElement,
    React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
    <div ref={ref} className={cn("space-y-1", className)} {...props} />
))
SidebarGroup.displayName = "SidebarGroup"

const SidebarGroupLabel = React.forwardRef<
    HTMLDivElement,
    React.HTMLAttributes<HTMLDivElement>
>(({ className, ...props }, ref) => (
    <div
        ref={ref}
        className={cn("px-2 py-1.5 text-xs font-semibold uppercase tracking-wider text-[#6272a4]", className)}
        {...props}
    />
))
SidebarGroupLabel.displayName = "SidebarGroupLabel"

const sidebarItemVariants = cva(
    "flex w-full items-center gap-2 rounded-md px-2 py-2 text-sm font-medium transition-colors hover:bg-[#1a1b26] hover:text-[#f8f8f2]",
    {
        variants: {
            variant: {
                default: "text-[#6272a4]",
                active: "bg-[#bd93f9]/10 text-[#bd93f9] hover:bg-[#bd93f9]/20 hover:text-[#bd93f9]",
            },
        },
        defaultVariants: {
            variant: "default",
        },
    }
)

interface SidebarItemProps
    extends React.ButtonHTMLAttributes<HTMLButtonElement>,
    VariantProps<typeof sidebarItemVariants> {
    icon?: React.ComponentType<{ className?: string }>
    asChild?: boolean
}

const SidebarItem = React.forwardRef<HTMLButtonElement, SidebarItemProps>(
    ({ className, variant, icon: Icon, children, ...props }, ref) => {
        return (
            <button
                ref={ref}
                className={cn(sidebarItemVariants({ variant }), className)}
                {...props}
            >
                {Icon && <Icon className="h-4 w-4" />}
                {children}
            </button>
        )
    }
)
SidebarItem.displayName = "SidebarItem"

export {
    Sidebar,
    SidebarHeader,
    SidebarContent,
    SidebarFooter,
    SidebarGroup,
    SidebarGroupLabel,
    SidebarItem,
}
