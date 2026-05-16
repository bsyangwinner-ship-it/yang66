export function formatCalories(value: number): string {
  return `${Math.round(value).toLocaleString("zh-CN")} kcal`;
}

export function formatPercent(value: number): string {
  return `${Math.round(value)}%`;
}
