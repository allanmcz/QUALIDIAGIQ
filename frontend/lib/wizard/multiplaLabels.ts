/**
 * Rótulos para perguntas multipla_escolha / checklist (catálogo inconsistente).
 * Mantém o wizard resiliente sem crash quando `opcoes` vem vazia.
 */
export function montarRotulosMultiplaEscolha(
  total: number,
  opcoes: string[] | undefined | null,
  codigoPergunta: string,
): { labels: string[]; avisoRotulos?: string } {
  if (total < 1) {
    return {
      labels: [],
    };
  }
  const base = opcoes?.length ? opcoes.map((o) => o.trim()).filter(Boolean) : [];
  const labels = Array.from(
    { length: total },
    (_, i) => base[i] || `Opção ${i + 1}`,
  );
  const avisoRotulos =
    (!opcoes || opcoes.length === 0) && total > 0
      ? `O catálogo não enviou rótulos para «${codigoPergunta}». Seleção possível por itens genéricos; se persistir, contacte o suporte.`
      : undefined;
  return { labels, avisoRotulos };
}
