import { RouterProvider } from "react-router-dom";

import { router } from "@/app/router";
import { RootProviders } from "@/providers/RootProviders";

export function App() {
  return (
    <RootProviders>
      <RouterProvider router={router} future={{ v7_startTransition: true }} />
    </RootProviders>
  );
}
