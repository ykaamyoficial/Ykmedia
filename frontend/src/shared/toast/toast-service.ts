import { EventBus } from "@/shared/events/event-bus";
import { type ToastMessage, type ToastType } from "@/shared/toast/toast-types";

type ToastEvents = {
  show: ToastMessage;
  dismiss: string;
};

const toastBus = new EventBus<ToastEvents>();

function createToast(type: ToastType, title: string, description?: string): string {
  const id = crypto.randomUUID();
  toastBus.emit("show", { id, type, title, description });
  return id;
}

export const toast = {
  subscribe: toastBus.on.bind(toastBus),
  dismiss: (id: string) => toastBus.emit("dismiss", id),
  success: (title: string, description?: string) => createToast("success", title, description),
  error: (title: string, description?: string) => createToast("error", title, description),
  warning: (title: string, description?: string) => createToast("warning", title, description),
  info: (title: string, description?: string) => createToast("info", title, description),
  loading: (title: string, description?: string) => createToast("loading", title, description),
};
