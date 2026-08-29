import { useEffect, useMemo, useState } from "react";

import { YkButton } from "@/components/system/YkButton";
import { YkEmptyState } from "@/components/system/YkEmptyState";
import { YkPage } from "@/components/system/YkPage";
import { navigationItems } from "@/routes/navigation";
import { YkErrorState, YkOfflineState } from "@/shared/components";
import { friendlyErrorMessage, isOfflineError } from "@/shared/errors";
import { YkIcons } from "@/shared/icons";
import { toast } from "@/shared/toast";
import {
  CategoriesTable,
  CategoriesToolbar,
  CategoryDeleteDialog,
  CategoryNameDialog,
} from "@/features/categories/components";
import { useCategories, useSaveCategories } from "@/features/categories/hooks";
import { moveCategory, removeCategoryAt, replaceCategoryAt } from "@/features/categories/utils";

type CategoryDialogState =
  | { type: "add" }
  | { type: "edit"; index: number; value: string }
  | { type: "delete"; index: number }
  | null;

const categoriesItem = navigationItems.find((item) => item.path === "/categorias") ?? navigationItems[0];

export function CategoriesPage() {
  const categoriesQuery = useCategories();
  const saveCategoriesMutation = useSaveCategories();
  const [selectedIndex, setSelectedIndex] = useState(-1);
  const [dialogState, setDialogState] = useState<CategoryDialogState>(null);

  const categories = useMemo(() => categoriesQuery.data?.items ?? [], [categoriesQuery.data?.items]);
  const categoryNames = useMemo(() => categories.map((category) => category.name), [categories]);

  useEffect(() => {
    if (selectedIndex >= categories.length) {
      setSelectedIndex(categories.length - 1);
    }
  }, [categories.length, selectedIndex]);

  function saveList(nextCategories: string[]) {
    saveCategoriesMutation.mutate(nextCategories, {
      onSuccess: () => {
        toast.success("Categorias atualizadas.");
      },
      onError: (error) => {
        toast.error("Nao foi possivel salvar as categorias.", friendlyErrorMessage(error));
      },
    });
  }

  function refreshCategories() {
    void categoriesQuery.refetch();
  }

  if (categoriesQuery.isError) {
    return (
      <YkPage item={categoriesItem}>
        <div>
          <h2 className="text-2xl font-semibold text-foreground">Categorias cadastradas</h2>
          <p className="text-sm text-secondary">Pastas e classificacoes de destino.</p>
        </div>
        {isOfflineError(categoriesQuery.error) ? <YkOfflineState /> : <YkErrorState />}
        <YkButton variant="secondary" className="w-fit" onClick={refreshCategories}>
          <YkIcons.RefreshCcw className="h-4 w-4" aria-hidden="true" />
          Tentar novamente
        </YkButton>
      </YkPage>
    );
  }

  return (
    <YkPage item={categoriesItem}>
      <div>
        <h2 className="text-2xl font-semibold text-foreground">Categorias cadastradas</h2>
        <p className="text-sm text-secondary">Pastas e classificacoes de destino.</p>
      </div>

      <CategoriesToolbar
        selectedIndex={selectedIndex}
        total={categories.length}
        saving={saveCategoriesMutation.isPending}
        onAdd={() => setDialogState({ type: "add" })}
        onEdit={() => {
          if (selectedIndex >= 0) {
            setDialogState({
              type: "edit",
              index: selectedIndex,
              value: categories[selectedIndex]?.name ?? "",
            });
          }
        }}
        onRemove={() => {
          if (selectedIndex >= 0) {
            setDialogState({ type: "delete", index: selectedIndex });
          }
        }}
        onMoveUp={() => {
          saveList(moveCategory(categoryNames, selectedIndex, -1));
          setSelectedIndex(Math.max(0, selectedIndex - 1));
        }}
        onMoveDown={() => {
          saveList(moveCategory(categoryNames, selectedIndex, 1));
          setSelectedIndex(Math.min(categories.length - 1, selectedIndex + 1));
        }}
      />

      {categoriesQuery.isLoading ? (
        <CategoriesTable
          categories={[]}
          selectedIndex={selectedIndex}
          loading
          onSelect={setSelectedIndex}
        />
      ) : categories.length === 0 ? (
        <YkEmptyState
          icon={YkIcons.FolderTree}
          title="Nenhuma categoria cadastrada."
          description="Use Nova categoria para adicionar a primeira categoria."
        />
      ) : (
        <CategoriesTable
          categories={categories}
          selectedIndex={selectedIndex}
          onSelect={setSelectedIndex}
        />
      )}

      {dialogState?.type === "add" && (
        <CategoryNameDialog
          title="Nova categoria"
          onCancel={() => setDialogState(null)}
          onConfirm={(value) => {
            setDialogState(null);
            saveList([...categoryNames, value.trim()]);
          }}
        />
      )}
      {dialogState?.type === "edit" && (
        <CategoryNameDialog
          title="Editar categoria"
          initialValue={dialogState.value}
          onCancel={() => setDialogState(null)}
          onConfirm={(value) => {
            setDialogState(null);
            saveList(replaceCategoryAt(categoryNames, dialogState.index, value.trim()));
          }}
        />
      )}
      {dialogState?.type === "delete" && (
        <CategoryDeleteDialog
          onCancel={() => setDialogState(null)}
          onConfirm={() => {
            setDialogState(null);
            saveList(removeCategoryAt(categoryNames, dialogState.index));
            setSelectedIndex(-1);
          }}
        />
      )}
    </YkPage>
  );
}
