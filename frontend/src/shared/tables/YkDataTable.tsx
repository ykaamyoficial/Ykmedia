import {
  flexRender,
  getCoreRowModel,
  type Row,
  useReactTable,
  type ColumnDef,
} from "@tanstack/react-table";

import { cn } from "@/components/ui/utils";
import { YkNoDataState } from "@/shared/components/empty-states";
import { YkSkeleton } from "@/shared/components/loading";

type YkDataTableProps<TData> = {
  data: TData[];
  columns: Array<ColumnDef<TData>>;
  loading?: boolean;
  getRowClassName?: (row: Row<TData>) => string | undefined;
  onRowClick?: (row: Row<TData>) => void;
};

export function YkDataTable<TData>({
  data,
  columns,
  loading = false,
  getRowClassName,
  onRowClick,
}: YkDataTableProps<TData>) {
  const table = useReactTable({
    data,
    columns,
    getCoreRowModel: getCoreRowModel(),
  });

  if (loading) {
    return <YkSkeleton className="h-44 w-full" />;
  }

  if (data.length === 0) {
    return <YkNoDataState />;
  }

  return (
    <div className="yk-scroll overflow-x-auto rounded-xl border border-border">
      <table className="w-full min-w-[640px] border-collapse text-sm">
        <thead className="bg-muted text-left text-xs uppercase tracking-wide text-secondary">
          {table.getHeaderGroups().map((headerGroup) => (
            <tr key={headerGroup.id}>
              {headerGroup.headers.map((header) => (
                <th key={header.id} className="px-3 py-2 font-semibold">
                  {header.isPlaceholder
                    ? null
                    : flexRender(header.column.columnDef.header, header.getContext())}
                </th>
              ))}
            </tr>
          ))}
        </thead>
        <tbody className="divide-y divide-border bg-panel">
          {table.getRowModel().rows.map((row) => (
            <tr
              key={row.id}
              className={cn(
                onRowClick && "cursor-pointer transition hover:bg-muted/60",
                getRowClassName?.(row),
              )}
              onClick={() => onRowClick?.(row)}
            >
              {row.getVisibleCells().map((cell) => (
                <td key={cell.id} className="px-3 py-2 text-foreground">
                  {flexRender(cell.column.columnDef.cell, cell.getContext())}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
