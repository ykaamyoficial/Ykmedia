export const publicRoutes = {
  root: "/",
} as const;

export const internalRoutes = {
  dashboard: "/dashboard",
  conversations: "/conversas",
  downloads: "/downloads",
  files: "/arquivos",
  categories: "/categorias",
  history: "/historico",
  settings: "/configuracoes",
} as const;

export const protectedRoutes = {} as const;
