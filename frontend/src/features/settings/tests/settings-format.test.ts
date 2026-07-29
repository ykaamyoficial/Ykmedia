import { describe, expect, it } from "vitest";

import { friendlyEvolutionState, statusTone } from "@/features/settings/utils";

describe("settings format utils", () => {
  it("formats the existing Evolution states used by PySide6", () => {
    expect(friendlyEvolutionState("open")).toBe("WhatsApp conectado");
    expect(friendlyEvolutionState("connecting")).toBe("WhatsApp conectando");
    expect(friendlyEvolutionState("close")).toBe("WhatsApp desconectado");
    expect(statusTone("ERROR")).toBe("danger");
  });
});
