import { describe, expect, it } from "vitest";

import {
  AppError,
  NetworkError,
  ServerError,
  friendlyErrorMessage,
  toAppError,
} from "@/shared/errors/app-error";

describe("app errors", () => {
  it("keeps known application errors", () => {
    const error = new NetworkError();

    expect(toAppError(error)).toBe(error);
  });

  it("maps unknown errors to friendly messages", () => {
    const error = toAppError(new Error("raw"));

    expect(error).toBeInstanceOf(AppError);
    expect(friendlyErrorMessage(error)).toBe("Erro inesperado.");
  });

  it("maps server errors to friendly messages", () => {
    expect(friendlyErrorMessage(new ServerError(500))).toBe("O backend retornou um erro.");
  });
});
