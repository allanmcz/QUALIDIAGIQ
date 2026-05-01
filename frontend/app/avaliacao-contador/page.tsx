import Link from "next/link";

import { getApiUrl } from "@/lib/api/config";

export const metadata = {
  title: "Avaliação para contadores | QualiDiagIQ",
  description:
    "Checklist resumida para contadores e fiscalistas avaliarem transparência, LGPD e limites do MVP QDI.",
};

/**
 * Página institucional para profissionais contábeis (due diligence leve).
 * O guia completo versionado está em docs/contabilidade/AVALIACAO_CONTADOR_MVP_FECHADO.md no repositório.
 */
export default function AvaliacaoContadorPage() {
  const baseApi = getApiUrl().replace(/\/$/, "");

  return (
    <div className="container max-w-3xl py-12 space-y-8">
      <div className="space-y-2">
        <Link href="/" className="text-sm text-primary hover:underline">
          Voltar ao início
        </Link>
        <h1 className="text-3xl font-bold tracking-tight">Avaliação para contadores e fiscalistas</h1>
        <p className="text-muted-foreground leading-relaxed">
          Esta página resume o que conferir antes de chancelar o uso institucional do{" "}
          <strong>QualiDiagIQ (MVP)</strong>. Não substitui parecer jurídico nem trabalho de auditoria
          independente.
        </p>
      </div>

      <section className="space-y-3">
        <h2 className="text-xl font-semibold">1. Natureza do produto</h2>
        <ul className="list-disc pl-6 space-y-2 text-sm leading-relaxed">
          <li>
            <strong>É:</strong> diagnóstico de maturidade tributária frente à Reforma do Consumo (EC
            132/2023, LC 214/2025) com eixo ABNT NBR 17301:2026.
          </li>
          <li>
            <strong>Não é:</strong> apuração CBS/IBS/IS contínua, substituição de ERP nem defesa em
            auto de infração.
          </li>
          <li>O resultado depende da <strong>veracidade das respostas</strong> ao questionário.</li>
        </ul>
      </section>

      <section className="space-y-3">
        <h2 className="text-xl font-semibold">2. Transparência do score (pesos auditáveis)</h2>
        <ul className="list-disc pl-6 space-y-2 text-sm leading-relaxed">
          <li>
            <Link href="/metodologia" className="text-primary underline font-medium">
              Metodologia e manifesto no site
            </Link>
          </li>
          <li>
            API — manifesto JSON:{" "}
            <a
              href={`${baseApi}/diagnosticos/manifesto-pesos`}
              className="text-primary underline break-all font-medium"
              target="_blank"
              rel="noopener noreferrer"
            >
              {baseApi}/diagnosticos/manifesto-pesos
            </a>
          </li>
          <li>
            API — metodologia:{" "}
            <a
              href={`${baseApi}/diagnosticos/metodologia`}
              className="text-primary underline break-all font-medium"
              target="_blank"
              rel="noopener noreferrer"
            >
              {baseApi}/diagnosticos/metodologia
            </a>
          </li>
        </ul>
      </section>

      <section className="space-y-3">
        <h2 className="text-xl font-semibold">3. LGPD e limitação de responsabilidade</h2>
        <ul className="list-disc pl-6 space-y-2 text-sm leading-relaxed">
          <li>
            O fluxo de diagnóstico exige <strong>aceite explícito</strong> da política de privacidade;
            o servidor registra o instante do aceite (evidência LGPD).
          </li>
          <li>
            <Link href="/privacidade" className="text-primary underline font-medium">
              Política de privacidade (MVP)
            </Link>{" "}
            e{" "}
            <Link href="/termos" className="text-primary underline font-medium">
              Termos de uso (MVP)
            </Link>{" "}
            devem ser revisados pelo assessor jurídico antes de go-live comercial amplo.
          </li>
        </ul>
      </section>

      <section className="space-y-3">
        <h2 className="text-xl font-semibold">4. PDF e âncoras normativas</h2>
        <p className="text-sm text-muted-foreground leading-relaxed">
          O relatório PDF deve trazer seções executivas e técnicas, cronograma alinhado à LC 214/2025,
          matriz por área e disclaimers com EC 132/2023, LC 214/2025 e ABNT NBR 17301:2026. Homologação
          visual em ambiente de produção espelho é recomendada antes do sign-off contábil.
        </p>
      </section>

      <section className="space-y-3">
        <h2 className="text-xl font-semibold">5. Confidencialidade (multi-tenant)</h2>
        <p className="text-sm text-muted-foreground leading-relaxed">
          Confirmar com TI que o isolamento por <strong>tenant</strong> está ativo no banco de produção
          (políticas RLS no PostgreSQL / Supabase) e que o acesso à API usa JWT com{" "}
          <code className="rounded bg-muted px-1">tenant_id</code> válido.
        </p>
      </section>

      <section className="rounded-lg border bg-muted/30 p-4 space-y-2">
        <h2 className="text-lg font-semibold">Guia completo no repositório</h2>
        <p className="text-sm leading-relaxed text-muted-foreground">
          Para checklist detalhado, sign-off sugerido e riscos por tema, use o ficheiro versionado{" "}
          <code className="rounded bg-background px-1">docs/contabilidade/AVALIACAO_CONTADOR_MVP_FECHADO.md</code>{" "}
          no projeto QDI.
        </p>
      </section>
    </div>
  );
}
