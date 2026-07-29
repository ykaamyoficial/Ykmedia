import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { DashboardMetricCard, DashboardSection, DashboardStatusCard } from "@/features/dashboard/components";
import { YkIcons } from "@/shared/icons";

describe("dashboard components", () => {
  it("renders metric cards", () => {
    render(
      <DashboardMetricCard
        label="Midias"
        value={12}
        description="Total real"
        icon={YkIcons.Archive}
      />,
    );

    expect(screen.getByText("Midias")).toBeInTheDocument();
    expect(screen.getByText("12")).toBeInTheDocument();
  });

  it("renders status cards", () => {
    render(<DashboardStatusCard label="Backend" status="online" description="Respondendo" />);

    expect(screen.getByText("Backend")).toBeInTheDocument();
    expect(screen.getByText("online")).toBeInTheDocument();
  });

  it("renders dashboard sections", () => {
    render(<DashboardSection title="Saude">Conteudo</DashboardSection>);

    expect(screen.getByText("Saude")).toBeInTheDocument();
    expect(screen.getByText("Conteudo")).toBeInTheDocument();
  });
});
