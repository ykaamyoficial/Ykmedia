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
