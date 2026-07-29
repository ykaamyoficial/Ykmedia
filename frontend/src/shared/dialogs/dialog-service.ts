import { EventBus } from "@/shared/events/event-bus";
import { type DialogRequest, type DialogType } from "@/shared/dialogs/dialog-types";

type DialogEvents = {
  open: DialogRequest;
  close: string;
};

const dialogBus = new EventBus<DialogEvents>();

function openDialog(type: DialogType, title: string, description?: string): string {
  const id = crypto.randomUUID();
  dialogBus.emit("open", { id, type, title, description });
  return id;
}

export const dialog = {
  subscribe: dialogBus.on.bind(dialogBus),
  close: (id: string) => dialogBus.emit("close", id),
  confirm: (title: string, description?: string) => openDialog("confirm", title, description),
  alert: (title: string, description?: string) => openDialog("alert", title, description),
  info: (title: string, description?: string) => openDialog("info", title, description),
  error: (title: string, description?: string) => openDialog("error", title, description),
  question: (title: string, description?: string) => openDialog("question", title, description),
};
