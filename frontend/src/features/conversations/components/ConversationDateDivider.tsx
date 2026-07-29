type ConversationDateDividerProps = {
  label: string;
};

export function ConversationDateDivider({ label }: ConversationDateDividerProps) {
  return (
    <div className="my-3 flex items-center justify-center">
      <span className="rounded-full border border-border bg-panel px-3 py-1 text-[11px] text-secondary">
        {label}
      </span>
    </div>
  );
}
