export function YkLoading() {
  return (
    <div className="space-y-3" aria-label="Carregando">
      <div className="h-5 w-40 animate-pulse rounded-md bg-muted" />
      <div className="grid gap-3 md:grid-cols-2">
        <div className="h-28 animate-pulse rounded-xl bg-muted" />
        <div className="h-28 animate-pulse rounded-xl bg-muted" />
      </div>
      <div className="h-48 animate-pulse rounded-xl bg-muted" />
    </div>
  );
}
