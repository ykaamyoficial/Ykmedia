import { containingFolderPath } from "@/features/files/utils/filter-files";

function openLocalPath(path: string): void {
  if (!path) {
    return;
  }
  const normalized = path.replace(/\\/g, "/");
  window.open(`file:///${normalized}`, "_blank", "noopener,noreferrer");
}

export function openFile(path: string): void {
  openLocalPath(path);
}

export function openContainingFolder(path: string): void {
  openLocalPath(containingFolderPath(path));
}
