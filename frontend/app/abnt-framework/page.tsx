import Link from "next/link";

/**
 * Conteúdo estático — Mapeamento UX do modelo ABNT NBR 17301:2026 ao fluxo QDI (M11).
 * Não substitui o texto jurídico da norma; serve como navegação didática para o cliente.
 */

const PILARES = [
  {
    pilar: "Contexto da organização",
    foco:
      "Governança, stakeholders e escopo tributário — primeira camada antes de KPIs formais.",
  },
  {
    pilar: "Liderança",
    foco:
      "Patrocínio executivo das mudanças da Reforma (EC 132/2023, LC 214/2025): comitês e comunicação.",
  },
  {
    pilar: "Planejamento",
    foco: "Gestão de risco fiscal/regulatório e plano de transição paralela CBS/legacy.",
  },
  {
    pilar: "Suporte",
    foco:
      "Pessoas, TI, infraestrutura de dados mestres — base para NFC-e, catálogo e relatórios (NT 2025.002 como referência de layout).",
  },
  {
    pilar: "Operação",
    foco:
      "Controles sobre processos tributários cotidianos — apurações, escrituração digital e SLA de correção.",
  },
  {
    pilar: "Avaliação de desempenho",
    foco:
      "Monitoramento contra metas por dimensão do score QDI — laços com M05/M07 recomendações específicas.",
  },
  {
    pilar: "Melhoria contínua",
    foco: "PDCA institucional: Plan-Do-Check-Act ancorando incidentes ao plano tributário estratégico.",
  },
] as const;

export default function AbntFrameworkPage() {
  return (
    <div className="container max-w-3xl py-12 space-y-10">
      <div>
        <Link href="/wizard" className="text-sm text-primary hover:underline">
          ← Wizard de diagnóstico
        </Link>
      </div>
      <header className="space-y-3">
        <p className="text-xs uppercase tracking-wide text-muted-foreground font-semibold">
          Framework no produto QualiDiagIQ
        </p>
        <h1 className="text-3xl font-bold tracking-tight">ABNT NBR 17301:2026 × QDI — PDCA em 8 etapas</h1>
        <p className="text-muted-foreground leading-relaxed">
          A metodologia do QDI estrutura o diagnóstico em oito microetapas (ver{" "}
          <code className="text-xs bg-muted px-1 rounded">docs/refs/04_METODOLOGIA.md</code>). O ciclo macro
          de melhoria contínua do sistema de conformidade tributário segue Plan-Do-Check-Act conforme ABNT NBR 17301:2026
          (<strong>M11 — espinha do produto</strong>).
        </p>
      </header>

      <section className="rounded-xl border bg-card p-6 space-y-4">
        <h2 className="text-xl font-semibold">Plan / Do / Check / Act × questionário adaptativo</h2>
        <ul className="list-disc list-inside text-sm space-y-2 text-muted-foreground leading-relaxed">
          <li>
            <strong>Plan</strong>: identifica perfil, carrega perguntas filtradas pelo motor (<strong>M01</strong>),
            garante evidências legais e consentimento LGPD (<strong>M09</strong>).
          </li>
          <li>
            <strong>Do</strong>: coleta ponderada pelo manifesto público (<strong>M03</strong>,
            também disponível na área pública de{" "}
            <Link href="/metodologia" className="text-primary underline font-medium">
              Metodologia e pesos
            </Link>{" "}
            ).
          </li>
          <li>
            <strong>Check</strong>: gera radar, heatmap e ranking (<strong>M05</strong>) + PDF executivo sintético (<strong>M04</strong>).
          </li>
          <li>
            <strong>Act</strong>: plano priorizado quando o score está disponível (<strong>M07</strong>), com
            rastreabilidade por empresa no painel (<strong>M10</strong>).
          </li>
        </ul>
      </section>

      <section className="space-y-4">
        <h2 className="text-xl font-semibold">Os 7 pilares (orientação rápida)</h2>
        <div className="grid gap-3">
          {PILARES.map((linha, idx) => (
            <article key={linha.pilar} className="border rounded-lg p-4 bg-muted/20">
              <p className="text-xs font-bold text-muted-foreground mb-1">Pilar {idx + 1}</p>
              <h3 className="font-semibold">{linha.pilar}</h3>
              <p className="text-sm text-muted-foreground mt-1 leading-relaxed">{linha.foco}</p>
            </article>
          ))}
        </div>
      </section>

      <p className="text-xs text-muted-foreground italic">
        Referências legais: EC 132/2023 · LC 214/2025 · ABNT NBR 17301:2026 · NT NF-e onde aplicável
        ao cadastro tributário (ex.: NT 2025.002).
      </p>
    </div>
  );
}
