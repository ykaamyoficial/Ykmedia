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
  // Preparar o sistema baixa mais de 1 GB de imagens do Docker na primeira
  // vez. Com o limite padrao a tela desistia em 5 segundos e acusava falha
  // enquanto o backend seguia trabalhando.
  systemPrepareMs: 20 * 60 * 1000,
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
