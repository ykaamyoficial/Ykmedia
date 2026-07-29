export type ToastType = "success" | "error" | "warning" | "info" | "loading";

export type ToastMessage = {
  id: string;
  type: ToastType;
  title: string;
  description?: string;
};
