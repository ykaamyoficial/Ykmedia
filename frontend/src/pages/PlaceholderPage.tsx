import { YkPage } from "@/components/system/YkPage";
import { type NavigationItem } from "@/routes/navigation";

export function PlaceholderPage({ item }: { item: NavigationItem }) {
  return <YkPage item={item} />;
}
