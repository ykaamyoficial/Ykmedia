import { type ButtonHTMLAttributes } from "react";

import { cn } from "@/components/ui/utils";

type YkButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "secondary" | "ghost";
  size?: "sm" | "md";
};

export function YkButton({
  className,
  variant = "primary",
  size = "md",
  ...props
}: YkButtonProps) {
  return (
    <button
      className={cn(
        "inline-flex items-center justify-center gap-2 rounded-lg font-medium transition-[background,border,color,opacity]",
        "focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent",
        "disabled:cursor-not-allowed disabled:opacity-55",
        size === "sm" ? "h-8 px-2.5 text-xs" : "h-9 px-3 text-sm",
        variant === "primary" && "bg-accent text-white hover:brightness-110 active:brightness-95",
        variant === "secondary" && "border border-border bg-panel text-foreground hover:bg-muted",
        variant === "ghost" && "text-secondary hover:bg-muted hover:text-foreground",
        className,
      )}
      {...props}
    />
  );
}
