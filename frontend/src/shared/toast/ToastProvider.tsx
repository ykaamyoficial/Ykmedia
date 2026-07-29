import { useEffect, useState, type ReactNode } from "react";

import { cn } from "@/components/ui/utils";
import { toast } from "@/shared/toast/toast-service";
import { type ToastMessage } from "@/shared/toast/toast-types";

const toneClass: Record<ToastMessage["type"], string> = {
  success: "border-success/40",
  error: "border-danger/40",
  warning: "border-warning/40",
  info: "border-accent/40",
  loading: "border-secondary/40",
};

export function ToastProvider({ children }: { children: ReactNode }) {
  const [messages, setMessages] = useState<ToastMessage[]>([]);

  useEffect(() => {
    const unsubscribeShow = toast.subscribe("show", (message) => {
      setMessages((current) => [...current, message]);
    });
    const unsubscribeDismiss = toast.subscribe("dismiss", (id) => {
      setMessages((current) => current.filter((message) => message.id !== id));
    });
    return () => {
      unsubscribeShow();
      unsubscribeDismiss();
    };
  }, []);

  return (
    <>
      {children}
      <div className="fixed bottom-4 right-4 z-50 flex w-80 flex-col gap-2" aria-live="polite">
        {messages.map((message) => (
          <button
            key={message.id}
            type="button"
            onClick={() => toast.dismiss(message.id)}
            className={cn(
              "rounded-xl border bg-panel-elevated p-3 text-left shadow-panel",
              toneClass[message.type],
            )}
          >
            <p className="text-sm font-semibold text-foreground">{message.title}</p>
            {message.description && <p className="mt-1 text-xs text-secondary">{message.description}</p>}
          </button>
        ))}
      </div>
    </>
  );
}
