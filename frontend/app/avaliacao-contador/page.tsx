import Link from "next/link";

export const metadata = {
  title: "Avaliação para contadores | QualiDiagIQ",
  description:
    "Checklist resumida para contadores e fiscalistas avaliarem transparência, LGPD e limites do QualiDiagIQ.",
};

/**
 * Página institucional para profissionais contábeis (due diligence leve).
 * O guia completo versionado está em docs/contabilidade/AVALIACAO_CONTADOR_MVP_FECHADO.md no repositório.
 */
export default function AvaliacaoContadorPage() {
  return (
    <div className="container max-w-3xl py-12 space-y-8">
      <div className="space-y-2">
        <Link href="/" className="text-sm text-primary hover:underline">
          Voltar ao início
        </Link>
        <h1 className="text-3xl font-bold tracking-tight">Avaliação para contadores e fiscalistas</h1>
        <p className="text-muted-foreground leading-relaxed">
          Esta página resume o que conferir antes de chancelar o uso institucional do{" "}
          <strong>QualiDiagIQ</strong>. Não substitui parecer jurídico nem trabalho de auditoria
          independente.
        </p>
        <nav
          aria-label="Conferir metodologia e documentação pública"
          className="flex flex-col gap-3 rounded-lg border bg-muted/40 p-4 sm:flex-row sm:flex-wrap sm:items-center"
        >
          <span className="text-sm font-medium text-foreground shrink-0">Conferir agora:</span>
          <div className="flex flex-wrap gap-x-4 gap-y-2 text-sm">
            <Link href="/metodologia" className="text-primary font-semibold underline underline-offset-4">
              Metodologia e pesos (site)
            </Link>
            <Link href="/abnt-framework" className="text-primary font-semibold underline underline-offset-4">
              Framework ABNT (contexto)
            </Link>
            <Link href="/privacidade" className="text-primary font-semibold underline underline-offset-4">
              Privacidade e LGPD
            </Link>
          </div>
        </nav>
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
              Metodologia e pesos no site
            </Link>
          </li>
          <li>
            Manifesto de pesos: publicado na página de metodologia para conferência de critérios.
          </li>
          <li>
            Metodologia: critérios de pontuação, pesos e vigência apresentados em linguagem de negócio.
          </li>
        </ul>
      </section>

      <section className="space-y-3">
        <h2 className="text-xl font-semibold">3. LGPD e limitação de responsabilidade</h2>
        <ul className="list-disc pl-6 space-y-2 text-sm leading-relaxed">
          <li>
            O fluxo de diagnóstico exige <strong>aceite explícito</strong> da política de privacidade;
            a plataforma registra o instante do aceite como evidência LGPD.
          </li>
          <li>
            <Link href="/privacidade" className="text-primary underline font-medium">
              Política de privacidade
            </Link>{" "}
            e{" "}
            <Link href="/termos" className="text-primary underline font-medium">
              Termos de uso
            </Link>{" "}
            devem ser revisados pelo assessor jurídico antes de uso institucional amplo.
          </li>
        </ul>
      </section>

      <section className="space-y-3">
        <h2 className="text-xl font-semibold">4. PDF e âncoras normativas</h2>
        <p className="text-sm text-muted-foreground leading-relaxed">
          O relatório PDF deve trazer seções executivas e técnicas, cronograma alinhado à LC 214/2025,
          matriz por área e avisos de escopo com EC 132/2023, LC 214/2025 e ABNT NBR 17301:2026. Recomenda-se revisão
          visual e contábil antes de uso institucional amplo.
        </p>
      </section>

      <section className="space-y-3">
        <h2 className="text-xl font-semibold">5. Confidencialidade e segregação de dados</h2>
        <p className="text-sm text-muted-foreground leading-relaxed">
          Confirmar com TI ou com o responsável pela operação que cada cliente visualiza apenas seus próprios
          diagnósticos, relatórios e solicitações LGPD.
        </p>
      </section>

      <section className="rounded-lg border bg-muted/30 p-4 space-y-2">
        <h2 className="text-lg font-semibold">Guia completo de avaliação</h2>
        <p className="text-sm leading-relaxed text-muted-foreground">
          Para checklist detalhado, critérios de aceite e riscos por tema, consulte o material interno de avaliação
          contábil do QualiDiagIQ.
        </p>
      </section>
    </div>
  );
}
