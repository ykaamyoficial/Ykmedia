import { describe, expect, it } from "vitest";

import { filterHistory, uniqueHistoryCategories, uniqueHistoryOrigins } from "@/features/history/utils";
import { type HistoryItem } from "@/features/history/types";

const items: HistoryItem[] = [
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
    kind: "Imagem",
    status: "CONCLUIDO",
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
    kind: "YouTube",
    status: "CONCLUIDO",
  },
];

describe("history filters", () => {
  it("filters by search, category and origin", () => {
    expect(filterHistory(items, { search: "pregacao", category: "Todos", origin: "Todas" })).toEqual([items[1]]);
    expect(filterHistory(items, { search: "", category: "Louvores", origin: "Todas" })).toEqual([items[0]]);
    expect(filterHistory(items, { search: "", category: "Todos", origin: "YouTube" })).toEqual([items[1]]);
  });

  it("builds unique filter options", () => {
    expect(uniqueHistoryCategories(items)).toEqual(["Louvores", "Mensagens"]);
    expect(uniqueHistoryOrigins(items)).toEqual(["WhatsApp", "YouTube"]);
  });
});
