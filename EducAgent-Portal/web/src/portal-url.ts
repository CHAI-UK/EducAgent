export function previewLocation(href: string, enabled: boolean): string {
  const url = new URL(href);
  if (enabled) url.searchParams.set("preview", "1");
  else url.searchParams.delete("preview");
  return url.href;
}

export function moduleLocation(href: string, moduleId: string): string {
  const url = new URL(href);
  url.searchParams.set("module", moduleId);
  return url.href;
}
