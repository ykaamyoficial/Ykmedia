function isTauriRuntime() {
  return "__TAURI_INTERNALS__" in window;
}

function fileUrl(path: string) {
  return `file:///${path.replace(/\\/g, "/")}`;
}

function parentPath(path: string) {
  const normalized = path.replace(/\\/g, "/");
  return normalized.includes("/") ? normalized.slice(0, normalized.lastIndexOf("/")) : normalized;
}

export async function openNativePath(path?: string) {
  if (!path) {
    return;
  }

  if (isTauriRuntime()) {
    const { invoke } = await import("@tauri-apps/api/core");
    await invoke("open_media_file", { path });
    return;
  }

  window.open(fileUrl(path), "_blank", "noopener,noreferrer");
}

export async function revealNativePath(path?: string) {
  if (!path) {
    return;
  }

  if (isTauriRuntime()) {
    const { invoke } = await import("@tauri-apps/api/core");
    await invoke("reveal_media_file", { path });
    return;
  }

  window.open(fileUrl(parentPath(path)), "_blank", "noopener,noreferrer");
}

/**
 * Abre um endereco web no navegador padrao.
 *
 * Diferente de `openNativePath`, nao converte o valor em `file:///` — o
 * fallback do navegador precisa receber a URL intacta.
 */
export async function openExternalUrl(url: string) {
  if (!url) {
    return;
  }

  if (isTauriRuntime()) {
    const { invoke } = await import("@tauri-apps/api/core");
    await invoke("open_media_file", { path: url });
    return;
  }

  window.open(url, "_blank", "noopener,noreferrer");
}
