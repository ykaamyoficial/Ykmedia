import { setApiAuthToken } from "@/shared/services/http-client";

function isTauriRuntime(): boolean {
  return typeof window !== "undefined" && "__TAURI_INTERNALS__" in window;
}

/**
 * Obtem o token da API junto ao shell Tauri e configura o cliente HTTP.
 *
 * Fora do Tauri (dev no navegador) o backend roda sem token, entao nao ha nada
 * a fazer. Falhas sao registradas mas nao impedem a inicializacao da interface.
 */
export async function initApiAuth(): Promise<void> {
  if (!isTauriRuntime()) {
    return;
  }

  try {
    const { invoke } = await import("@tauri-apps/api/core");
    const token = await invoke<string>("api_token");
    if (token) {
      setApiAuthToken(token);
    }
  } catch (error) {
    console.error("Nao foi possivel obter o token da API do YkMedia.", error);
  }
}
