import { describe, expect, it, vi } from "vitest";

import { ConnectionManager } from "@/shared/websocket/connection-manager";

describe("ConnectionManager", () => {
  it("prepares websocket lifecycle handling", () => {
    const close = vi.fn();
    vi.stubGlobal(
      "WebSocket",
      vi.fn().mockImplementation(() => ({ close })),
    );
    const manager = new ConnectionManager();

    manager.connect("ws://localhost");
    manager.close();

    expect(manager.state).toBe("closed");
    expect(close).toHaveBeenCalled();
  });
});
