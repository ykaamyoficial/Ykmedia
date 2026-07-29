import { describe, expect, it } from "vitest";

import { filterDownloadJobs } from "@/features/downloads/utils";
import { type DownloadJobItem } from "@/features/downloads/types";

const jobs: DownloadJobItem[] = [
  {
    id: "job-1",
    short_id: "job-1",
    sender: "+55 62 99999-9999",
    sender_raw: "5562999999999@s.whatsapp.net",
    origin: "WhatsApp",
    file: "foto.jpg",
    kind: "Imagem",
    status: "PENDENTE",
    created_at: "29/07/2026 10:00",
  },
  {
    id: "job-2",
    short_id: "job-2",
    sender: "+55 62 88888-8888",
    sender_raw: "5562888888888@s.whatsapp.net",
    origin: "YouTube",
    file: "louvor.mp4",
    kind: "Video",
    status: "CONCLUIDO",
    created_at: "29/07/2026 10:10",
  },
];

describe("filterDownloadJobs", () => {
  it("filters by status", () => {
    expect(filterDownloadJobs(jobs, { search: "", status: "CONCLUIDO" })).toEqual([jobs[1]]);
  });

  it("filters by any visible job value", () => {
    expect(filterDownloadJobs(jobs, { search: "louvor", status: "Todos" })).toEqual([jobs[1]]);
    expect(filterDownloadJobs(jobs, { search: "imagem", status: "Todos" })).toEqual([jobs[0]]);
  });
});
