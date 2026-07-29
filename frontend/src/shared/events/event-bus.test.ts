import { describe, expect, it, vi } from "vitest";

import { EventBus } from "@/shared/events/event-bus";

type Events = {
  ping: string;
};

describe("EventBus", () => {
  it("emits and unsubscribes events", () => {
    const bus = new EventBus<Events>();
    const handler = vi.fn();

    const unsubscribe = bus.on("ping", handler);
    bus.emit("ping", "hello");
    unsubscribe();
    bus.emit("ping", "ignored");

    expect(handler).toHaveBeenCalledOnce();
    expect(handler).toHaveBeenCalledWith("hello");
  });
});
