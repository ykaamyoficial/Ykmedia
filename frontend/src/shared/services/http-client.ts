import { appTimeouts } from "@/shared/constants/app";
import { NetworkError, ServerError, UnknownError } from "@/shared/errors/app-error";

type HttpMethod = "GET" | "POST" | "PUT" | "PATCH" | "DELETE";

export type HttpInterceptor = (request: RequestInit) => RequestInit;

export type HttpClientOptions = {
  baseUrl?: string;
  timeoutMs?: number;
  retries?: number;
  headers?: HeadersInit;
  interceptors?: HttpInterceptor[];
  fetcher?: typeof fetch;
};

export type HttpRequestOptions = {
  method?: HttpMethod;
  body?: unknown;
  signal?: AbortSignal;
  headers?: HeadersInit;
  timeoutMs?: number;
  retries?: number;
};

const defaultBaseUrl = import.meta.env.VITE_API_BASE_URL ?? "http://127.0.0.1:8010";

let apiAuthToken: string | null = null;

/** Define o token enviado em `Authorization` nas chamadas ao backend local. */
export function setApiAuthToken(token: string | null): void {
  apiAuthToken = token;
}

function mergeHeaders(defaultHeaders: HeadersInit, requestHeaders?: HeadersInit): Headers {
  const headers = new Headers(defaultHeaders);
  if (requestHeaders) {
    new Headers(requestHeaders).forEach((value, key) => headers.set(key, value));
  }
  return headers;
}

export class HttpClient {
  private readonly baseUrl: string;
  private readonly timeoutMs: number;
  private readonly retries: number;
  private readonly headers: HeadersInit;
  private readonly interceptors: HttpInterceptor[];
  private readonly fetcher?: typeof fetch;

  constructor(options: HttpClientOptions = {}) {
    this.baseUrl = options.baseUrl ?? defaultBaseUrl;
    this.timeoutMs = options.timeoutMs ?? appTimeouts.httpRequestMs;
    this.retries = options.retries ?? 0;
    this.headers = options.headers ?? { Accept: "application/json" };
    this.interceptors = options.interceptors ?? [];
    this.fetcher = options.fetcher;
  }

  async getJson<T>(path: string, options: Omit<HttpRequestOptions, "method" | "body"> = {}): Promise<T> {
    return this.requestJson<T>(path, { ...options, method: "GET" });
  }

  async requestJson<T>(path: string, options: HttpRequestOptions = {}): Promise<T> {
    const retries = options.retries ?? this.retries;
    let attempt = 0;

    while (true) {
      try {
        return await this.executeJsonRequest<T>(path, options);
      } catch (error) {
        if (attempt >= retries || error instanceof ServerError) {
          throw error;
        }
        attempt += 1;
      }
    }
  }

  private async executeJsonRequest<T>(path: string, options: HttpRequestOptions): Promise<T> {
    const controller = new AbortController();
    const timeout = window.setTimeout(
      () => controller.abort(),
      options.timeoutMs ?? this.timeoutMs,
    );
    const abortListener = () => controller.abort();
    options.signal?.addEventListener("abort", abortListener, { once: true });

    try {
      const headers = mergeHeaders(this.headers, options.headers);
      if (apiAuthToken && !headers.has("Authorization")) {
        headers.set("Authorization", `Bearer ${apiAuthToken}`);
      }
      const request = this.applyInterceptors({
        method: options.method ?? "GET",
        headers,
        signal: controller.signal,
        body: options.body === undefined ? undefined : JSON.stringify(options.body),
      });

      if (options.body !== undefined && !headers.has("Content-Type")) {
        headers.set("Content-Type", "application/json");
      }

      const response = await (this.fetcher ?? fetch)(`${this.baseUrl}${path}`, request);
      if (!response.ok) {
        throw new ServerError(response.status);
      }

      try {
        return (await response.json()) as T;
      } catch (error) {
        throw new UnknownError("Invalid JSON response.", error);
      }
    } catch (error) {
      if (error instanceof ServerError || error instanceof UnknownError) {
        throw error;
      }
      throw new NetworkError("Nao foi possivel conectar ao backend.", error);
    } finally {
      window.clearTimeout(timeout);
      options.signal?.removeEventListener("abort", abortListener);
    }
  }

  private applyInterceptors(request: RequestInit): RequestInit {
    return this.interceptors.reduce((current, interceptor) => interceptor(current), request);
  }
}

export const httpClient = new HttpClient();
