import { QueryClientProvider } from "@tanstack/react-query";
import { render } from "@testing-library/react";
import { type ReactNode } from "react";
import { createMemoryRouter, RouterProvider } from "react-router-dom";

import { AppProvider } from "@/providers/AppProvider";
import { BackendStatusProvider } from "@/providers/BackendStatusProvider";
import { ThemeProvider } from "@/providers/ThemeProvider";
import { routes } from "@/routes/routes";
import { createAppQueryClient } from "@/shared/query";

function createTestQueryClient() {
  const queryClient = createAppQueryClient();
  queryClient.setDefaultOptions({
    queries: {
      retry: false,
      gcTime: 0,
    },
  });
  return queryClient;
}

export function renderWithShellProviders(children: ReactNode) {
  const queryClient = createTestQueryClient();

  return render(
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <BackendStatusProvider>
          <AppProvider>{children}</AppProvider>
        </BackendStatusProvider>
      </ThemeProvider>
    </QueryClientProvider>,
  );
}

export function renderShellRoute(initialPath = "/dashboard") {
  const queryClient = createTestQueryClient();
  const router = createMemoryRouter(routes, {
    initialEntries: [initialPath],
    future: { v7_relativeSplatPath: true },
  });

  return render(
    <QueryClientProvider client={queryClient}>
      <ThemeProvider>
        <BackendStatusProvider>
          <AppProvider>
            <RouterProvider router={router} future={{ v7_startTransition: true }} />
          </AppProvider>
        </BackendStatusProvider>
      </ThemeProvider>
    </QueryClientProvider>,
  );
}
