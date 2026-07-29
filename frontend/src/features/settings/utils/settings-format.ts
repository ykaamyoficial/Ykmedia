export function friendlyEvolutionState(state: string): string {
  const normalized = state.toLowerCase();
  if (normalized === "open") {
    return "WhatsApp conectado";
  }
  if (normalized === "connecting") {
    return "WhatsApp conectando";
  }
  if (normalized === "close" || normalized === "closed") {
    return "WhatsApp desconectado";
  }
  if (normalized === "erro" || normalized === "error") {
    return "WhatsApp com erro";
  }
  return "WhatsApp nao verificado";
}

export function statusTone(status: string): "success" | "warning" | "danger" | "neutral" {
  const normalized = status.toLowerCase();
  if (["ok", "open", "online"].includes(normalized)) {
    return "success";
  }
  if (["warning", "connecting", "pending", "running"].includes(normalized)) {
    return "warning";
  }
  if (["error", "erro", "close", "closed"].includes(normalized)) {
    return "danger";
  }
  return "neutral";
}
