import { appMessages } from "@/shared/constants/app";

export type AppErrorKind = "network" | "validation" | "server" | "unknown";

export class AppError extends Error {
  constructor(
    message: string,
    public readonly kind: AppErrorKind,
    public readonly friendlyMessage: string,
    public readonly cause?: unknown,
  ) {
    super(message);
    this.name = "AppError";
  }
}

export class NetworkError extends AppError {
  constructor(message = "Network request failed.", cause?: unknown) {
    super(message, "network", appMessages.networkError, cause);
    this.name = "NetworkError";
  }
}

export class ValidationError extends AppError {
  constructor(message = "Validation failed.", cause?: unknown) {
    super(message, "validation", appMessages.validationError, cause);
    this.name = "ValidationError";
  }
}

export class ServerError extends AppError {
  constructor(
    public readonly status: number,
    message = `Server returned ${status}.`,
    cause?: unknown,
  ) {
    super(message, "server", appMessages.serverError, cause);
    this.name = "ServerError";
  }
}

export class UnknownError extends AppError {
  constructor(message = "Unknown error.", cause?: unknown) {
    super(message, "unknown", appMessages.unknownError, cause);
    this.name = "UnknownError";
  }
}

export function toAppError(error: unknown): AppError {
  if (error instanceof AppError) {
    return error;
  }
  if (error instanceof DOMException && error.name === "AbortError") {
    return new NetworkError("Request was aborted.", error);
  }
  if (error instanceof Error) {
    return new UnknownError(error.message, error);
  }
  return new UnknownError("Non-error value thrown.", error);
}

export function friendlyErrorMessage(error: unknown): string {
  return toAppError(error).friendlyMessage;
}

export function isOfflineError(error: unknown): boolean {
  return toAppError(error).kind === "network";
}
