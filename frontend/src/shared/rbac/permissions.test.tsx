import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { PermissionGuard, PermissionProvider } from "@/shared/rbac/permissions";

describe("permissions", () => {
  it("renders guarded content when permission exists", () => {
    render(
      <PermissionProvider permissions={["dashboard:view"]}>
        <PermissionGuard permission="dashboard:view">Permitido</PermissionGuard>
      </PermissionProvider>,
    );

    expect(screen.getByText("Permitido")).toBeInTheDocument();
  });

  it("renders fallback when permission is missing", () => {
    render(
      <PermissionProvider permissions={[]}>
        <PermissionGuard permission="dashboard:view" fallback="Negado">
          Permitido
        </PermissionGuard>
      </PermissionProvider>,
    );

    expect(screen.getByText("Negado")).toBeInTheDocument();
  });
});
