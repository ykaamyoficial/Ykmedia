export const APP_NAME = "YkMedia";

export const appRoutes = {
  dashboard: "/dashboard",
  conversations: "/conversas",
  downloads: "/downloads",
  files: "/arquivos",
  categories: "/categorias",
  history: "/historico",
  settings: "/configuracoes",
} as const;

export const appTimeouts = {
  httpRequestMs: 5000,
  debounceMs: 300,
  toastMs: 4200,
} as const;

export const appMessages = {
  genericError: "Nao foi possivel concluir a operacao.",
  networkError: "Sem conexao com o backend.",
  validationError: "Dados invalidos.",
  serverError: "O backend retornou um erro.",
  unknownError: "Erro inesperado.",
} as const;
