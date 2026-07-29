import { YkButton } from "@/components/system/YkButton";
import { YkSearch } from "@/components/system/YkSearch";
import { useDebounce } from "@/shared/hooks/useDebounce";
import { YkIcons } from "@/shared/icons";

type YkSearchBoxProps = {
  value: string;
  onChange: (value: string) => void;
  onDebouncedChange?: (value: string) => void;
  placeholder?: string;
};

export function YkSearchBox({ value, onChange, onDebouncedChange, placeholder }: YkSearchBoxProps) {
  useDebounce(value, 300, (debouncedValue) => {
    onDebouncedChange?.(debouncedValue);
  });

  return (
    <div className="flex items-center gap-2">
      <YkSearch
        value={value}
        onChange={(event) => onChange(event.target.value)}
        placeholder={placeholder ?? "Buscar..."}
      />
      {value && (
        <YkButton type="button" variant="ghost" size="sm" onClick={() => onChange("")} aria-label="Limpar busca">
          <YkIcons.X className="h-4 w-4" />
        </YkButton>
      )}
    </div>
  );
}
