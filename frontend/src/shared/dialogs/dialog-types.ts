export type DialogType = "confirm" | "alert" | "info" | "error" | "question";

export type DialogRequest = {
  id: string;
  type: DialogType;
  title: string;
  description?: string;
  confirmLabel?: string;
  cancelLabel?: string;
};
