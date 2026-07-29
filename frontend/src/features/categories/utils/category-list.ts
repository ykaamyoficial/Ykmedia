export function replaceCategoryAt(categories: string[], index: number, value: string): string[] {
  return categories.map((category, currentIndex) => (currentIndex === index ? value : category));
}

export function removeCategoryAt(categories: string[], index: number): string[] {
  return categories.filter((_, currentIndex) => currentIndex !== index);
}

export function moveCategory(categories: string[], index: number, direction: -1 | 1): string[] {
  const target = index + direction;
  if (index < 0 || target < 0 || target >= categories.length) {
    return categories;
  }

  const next = [...categories];
  const [item] = next.splice(index, 1);
  next.splice(target, 0, item);
  return next;
}
