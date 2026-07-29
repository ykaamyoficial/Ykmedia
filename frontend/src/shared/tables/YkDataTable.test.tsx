import { type ColumnDef } from "@tanstack/react-table";
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { YkDataTable } from "@/shared/tables/YkDataTable";

type Row = { name: string };

const columns: Array<ColumnDef<Row>> = [
  {
    accessorKey: "name",
    header: "Nome",
  },
];

describe("YkDataTable", () => {
  it("renders table data", () => {
    render(<YkDataTable data={[{ name: "Arquivo" }]} columns={columns} />);

    expect(screen.getByText("Nome")).toBeInTheDocument();
    expect(screen.getByText("Arquivo")).toBeInTheDocument();
  });

  it("renders empty state", () => {
    render(<YkDataTable data={[]} columns={columns} />);

    expect(screen.getByText("Sem dados")).toBeInTheDocument();
  });
});
