type EventMap = Record<string, unknown>;
type EventHandler<TPayload> = (payload: TPayload) => void;

export class EventBus<TEvents extends EventMap> {
  private readonly handlers = new Map<keyof TEvents, Set<EventHandler<TEvents[keyof TEvents]>>>();

  on<TKey extends keyof TEvents>(event: TKey, handler: EventHandler<TEvents[TKey]>): () => void {
    const existingHandlers = this.handlers.get(event) ?? new Set();
    existingHandlers.add(handler as EventHandler<TEvents[keyof TEvents]>);
    this.handlers.set(event, existingHandlers);

    return () => this.off(event, handler);
  }

  off<TKey extends keyof TEvents>(event: TKey, handler: EventHandler<TEvents[TKey]>): void {
    this.handlers.get(event)?.delete(handler as EventHandler<TEvents[keyof TEvents]>);
  }

  emit<TKey extends keyof TEvents>(event: TKey, payload: TEvents[TKey]): void {
    this.handlers.get(event)?.forEach((handler) => handler(payload));
  }

  clear(): void {
    this.handlers.clear();
  }
}
