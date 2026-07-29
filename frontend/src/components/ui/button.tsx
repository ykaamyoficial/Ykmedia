import { type ButtonHTMLAttributes } from "react";

import { cn } from "@/components/ui/utils";

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "secondary";
};

export function Button({ className, variant = "primary", ...props }: ButtonProps) {
  return (
    <button
      className={cn(
        "inline-flex h-9 items-center justify-center gap-2 rounded-lg px-3 text-sm font-medium transition",
        "focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent",
        "disabled:cursor-not-allowed disabled:opacity-60",
        variant === "primary" &&
          "bg-accent text-white shadow-sm hover:brightness-110 active:brightness-95",
        variant === "secondary" &&
          "border border-border bg-panel text-foreground hover:bg-muted",
        className,
      )}
      {...props}
    />
  );
}
