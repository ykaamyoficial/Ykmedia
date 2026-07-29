import { useMemo } from "react";
import { type ColumnDef } from "@tanstack/react-table";

import { YkDataTable } from "@/shared/tables";
import { type CategoryItem } from "@/features/categories/types";

type CategoriesTableProps = {
  categories: CategoryItem[];
  selectedIndex: number;
  loading?: boolean;
  onSelect: (index: number) => void;
};

export function CategoriesTable({
  categories,
  selectedIndex,
  loading = false,
  onSelect,
}: CategoriesTableProps) {
  const columns = useMemo<Array<ColumnDef<CategoryItem>>>(
    () => [
      {
        accessorKey: "position",
        header: "Posicao",
      },
      {
        accessorKey: "name",
        header: "Categoria",
        cell: ({ row }) => <span className="font-medium">{row.original.name}</span>,
      },
      {
        accessorKey: "folder",
        header: "Pasta correspondente",
        cell: ({ row }) => <span className="text-secondary">{row.original.folder}</span>,
      },
    ],
    [],
  );

  return (
    <YkDataTable
      data={categories}
      columns={columns}
      loading={loading}
      getRowClassName={(row) => (selectedIndex === row.index ? "bg-muted" : undefined)}
      onRowClick={(row) => onSelect(row.index)}
    />
  );
}
