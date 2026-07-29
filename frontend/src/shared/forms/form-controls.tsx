import { type InputHTMLAttributes, type SelectHTMLAttributes, type TextareaHTMLAttributes } from "react";

import { cn } from "@/components/ui/utils";

const fieldClass =
  "h-9 rounded-lg border border-border bg-panel px-3 text-sm text-foreground outline-none transition focus:border-accent disabled:opacity-60";

export function YkInput(props: InputHTMLAttributes<HTMLInputElement>) {
  return <input className={cn(fieldClass, props.className)} {...props} />;
}

export function YkTextarea(props: TextareaHTMLAttributes<HTMLTextAreaElement>) {
  return <textarea className={cn(fieldClass, "min-h-24 py-2", props.className)} {...props} />;
}

export function YkSelect(props: SelectHTMLAttributes<HTMLSelectElement>) {
  return <select className={cn(fieldClass, props.className)} {...props} />;
}

export function YkCheckbox(props: InputHTMLAttributes<HTMLInputElement>) {
  return <input type="checkbox" className={cn("h-4 w-4 accent-[hsl(var(--accent))]", props.className)} {...props} />;
}

export function YkSwitch(props: InputHTMLAttributes<HTMLInputElement>) {
  return <input type="checkbox" role="switch" className={cn("h-4 w-8 accent-[hsl(var(--accent))]", props.className)} {...props} />;
}

export function YkRadio(props: InputHTMLAttributes<HTMLInputElement>) {
  return <input type="radio" className={cn("h-4 w-4 accent-[hsl(var(--accent))]", props.className)} {...props} />;
}

export function YkDatePicker(props: InputHTMLAttributes<HTMLInputElement>) {
  return <YkInput type="date" {...props} />;
}
