import { describe, expect, it } from "vitest";

import { filterFiles, uniqueFileCategories, uniqueFileOrigins } from "@/features/files/utils";
import { type FileLibraryItem } from "@/features/files/types";

const files: FileLibraryItem[] = [
  {
    id: "hist-1",
    date: "2026-07-29T10:00:00+00:00",
    date_display: "29/07/2026 10:00",
    sender: "+55 62 99999-9999",
    sender_raw: "5562999999999@s.whatsapp.net",
    origin: "WhatsApp",
    category: "Louvores",
    final_name: "imagem.jpg",
    file_path: "Louvores/imagem.jpg",
    absolute_path: "C:\\media\\Louvores\\imagem.jpg",
    kind: "Imagem",
    status: "CONCLUIDO",
    size: "5 B",
    exists: true,
  },
  {
    id: "hist-2",
    date: "2026-07-29T11:00:00+00:00",
    date_display: "29/07/2026 11:00",
    sender: "+55 62 88888-8888",
    sender_raw: "5562888888888@s.whatsapp.net",
    origin: "YouTube",
    category: "Mensagens",
    final_name: "pregacao.mp4",
    file_path: "Mensagens/pregacao.mp4",
    absolute_path: "C:\\media\\Mensagens\\pregacao.mp4",
    kind: "YouTube",
    status: "CONCLUIDO",
    size: "10 MB",
    exists: true,
  },
];

describe("file filters", () => {
  it("filters by search, category and origin", () => {
    expect(filterFiles(files, { search: "pregacao", category: "Todos", origin: "Todas" })).toEqual([files[1]]);
    expect(filterFiles(files, { search: "", category: "Louvores", origin: "Todas" })).toEqual([files[0]]);
    expect(filterFiles(files, { search: "", category: "Todos", origin: "YouTube" })).toEqual([files[1]]);
  });

  it("builds unique filter options", () => {
    expect(uniqueFileCategories(files)).toEqual(["Louvores", "Mensagens"]);
    expect(uniqueFileOrigins(files)).toEqual(["WhatsApp", "YouTube"]);
  });
});
