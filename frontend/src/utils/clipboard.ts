/**
 * Copiar depende da Clipboard API, disponível em localhost. Se o navegador
 * recusar a permissão, devolvemos false para a tela explicar o que fazer.
 */
export async function copyToClipboard(value: string): Promise<boolean> {
  if (!navigator.clipboard || typeof navigator.clipboard.writeText !== "function") {
    return false;
  }
  try {
    await navigator.clipboard.writeText(value);
    return true;
  } catch {
    return false;
  }
}
