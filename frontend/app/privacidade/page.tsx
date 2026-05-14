import Link from "next/link";

import {
  getDpoPublicContact,
  getPoliticaPublicMeta,
  getRetencaoResumoPublicacao,
} from "@/lib/legal/dpoPublic";
import { LGPD_PRAZO_RESPOSTA_ART18_DIAS_UTEIS } from "@/lib/legal/lgpdOperacao";

export const metadata = {
  title: "Política de Privacidade | QualiDiagIQ",
};

export default function PrivacidadePage() {
  const dpo = getDpoPublicContact();
  const politicaMeta = getPoliticaPublicMeta();
  const retencaoResumo = getRetencaoResumoPublicacao();

  return (
    <div className="container max-w-3xl py-12 space-y-6">
      <Link href="/wizard" className="text-sm text-primary hover:underline">
        Voltar ao diagnóstico
      </Link>
      <h1 className="text-3xl font-bold tracking-tight">Política de privacidade (MVP QDI)</h1>
      <p className="rounded-md border border-primary/20 bg-primary/5 px-3 py-2 text-sm text-foreground">
        <strong>Status:</strong> minuta <strong>aprovada</strong> (parecer jurídico de 5 mai. 2026) e{" "}
        <strong>aprovada para publicação</strong> pelo controlador. LGPD (Lei 13.709/2018).
        {politicaMeta ? (
          <>
            {" "}
            <strong>Versão {politicaMeta.versao}</strong> · vigência <strong>{politicaMeta.vigenciaIso}</strong>.
          </>
        ) : null}{" "}
        Canal do encarregado (DPO) na seção abaixo{dpo ? "" : " — defina `NEXT_PUBLIC_LGPD_DPO_EMAIL` no deploy"}.
      </p>
      <section
        id="dpo"
        className="scroll-mt-24 rounded-md border bg-muted/40 px-4 py-3 text-sm leading-relaxed"
        aria-labelledby="dpo-heading"
      >
        <h2 id="dpo-heading" className="text-base font-semibold tracking-tight">
          Encarregado de Proteção de Dados (DPO)
        </h2>
        {dpo ? (
          <p className="mt-2 text-muted-foreground">
            {dpo.nomeExibicao ? (
              <>
                <span className="text-foreground">{dpo.nomeExibicao}</span> —{" "}
              </>
            ) : null}
            contato para exercício de direitos do titular e questões de tratamento de dados:{" "}
            <a className="font-medium text-primary underline" href={`mailto:${dpo.email}`}>
              {dpo.email}
            </a>
            .
          </p>
        ) : (
          <p className="mt-2 text-muted-foreground">
            O endereço público do encarregado será exibido aqui quando{" "}
            <code className="rounded bg-muted px-1 py-0.5 text-xs">NEXT_PUBLIC_LGPD_DPO_EMAIL</code> estiver
            definido no ambiente do site (ex.: build de produção). Até lá, utilize o contato institucional do
            controlador (Tributiq) indicado na página de suporte ou no contrato comercial.
          </p>
        )}
      </section>

      {retencaoResumo ? (
        <section
          id="retencao-resumo-controlador"
          className="scroll-mt-24 rounded-md border border-primary/15 bg-primary/5 px-4 py-3 text-sm leading-relaxed"
          aria-labelledby="retencao-resumo-heading"
        >
          <h2 id="retencao-resumo-heading" className="text-base font-semibold tracking-tight">
            Retenção — resumo publicado pelo controlador
          </h2>
          <p className="mt-2 whitespace-pre-wrap text-muted-foreground">{retencaoResumo}</p>
          <p className="mt-2 text-xs text-muted-foreground">
            Texto injetado em build via{" "}
            <code className="rounded bg-muted px-1">NEXT_PUBLIC_LGPD_RETENCAO_RESUMO</code> (decisão pós-workshop LGPD
            / ADR-012). Ajuste no host quando a política de retenção for actualizada.
          </p>
        </section>
      ) : null}

      <section
        id="retencao-telefone"
        className="scroll-mt-24 rounded-md border bg-muted/30 px-4 py-3 text-sm leading-relaxed"
        aria-labelledby="retencao-telefone-heading"
      >
        <h2 id="retencao-telefone-heading" className="text-base font-semibold tracking-tight">
          Telefone do respondente — retenção e titularidade
        </h2>
        <p className="mt-2 text-muted-foreground">
          O telefone opcional mantém-se associado ao registro do diagnóstico no mesmo período de retenção daquele
          registro. Pedidos dos titulares (acesso, correção, anonimização, eliminação nos limites legais) tramitam pelo
          canal do DPO; em caso de pedido fundamentado sobre este dado, o controlador registra a solicitação, avalia o
          enquadramento com o WORM/auditoria e responde no prazo interno definido pela operação — alinhado ao runbook{" "}
          <span className="font-mono text-xs">RUNBOOK_DIREITOS_TITULAR_RASCUNHO.md</span> e aos endpoints autenticados{" "}
          <span className="font-mono text-xs">POST/GET/PATCH /privacidade/solicitacoes</span> na API.
        </p>
      </section>

      <section
        id="sla-art-18"
        className="scroll-mt-24 rounded-md border bg-muted/30 px-4 py-3 text-sm leading-relaxed"
        aria-labelledby="sla-art-18-heading"
      >
        <h2 id="sla-art-18-heading" className="text-base font-semibold tracking-tight">
          Prazo de resposta aos pedidos do titular (art. 18 LGPD)
        </h2>
        <p className="mt-2 text-muted-foreground">
          Para pedidos de confirmação, acesso, correção e demais direitos exercidos pelo canal do DPO, o
          controlador compromete-se com prazo de resposta de{" "}
          <strong>{LGPD_PRAZO_RESPOSTA_ART18_DIAS_UTEIS} dias úteis</strong>, em linha com o art. 19, II da Lei
          13.709/2018, salvo fundamentação de extensão ou complexidade adicional registada na solicitação.
        </p>
      </section>

      <ul className="list-disc pl-6 space-y-2 text-sm leading-relaxed">
        <li>
          <strong>Controlador:</strong> Tributiq / QualiDiagIQ — contato pelo canal oficial do produto.
        </li>
        <li>
          <strong>Finalidade:</strong> elaboração do diagnóstico tributário e comunicações relacionadas ao
          serviço solicitado.
        </li>
        <li>
          <strong>Dados tratados:</strong> dados cadastrais da empresa e do respondente informados no
          formulário; respostas ao questionário; métricas de uso técnico (logs), quando aplicável.
        </li>
        <li>
          <strong>Telefone do respondente (opcional):</strong> quando informado, utilizado para contato
          comercial na plataforma relacionado ao diagnóstico; mantido pelo mesmo período de retenção do registro do
          diagnóstico no PostgreSQL (Supabase); exclusão e titularidade — ver{" "}
          <Link href="/privacidade#retencao-telefone" className="text-primary underline font-medium">
            retenção e titularidade (telefone)
          </Link>
          .
        </li>
        <li>
          <strong>Relatório PDF (WeasyPrint):</strong> na peça gerada para download, o bloco explícito de
          captação de lead exibe apenas <strong>e-mail</strong> e <strong>telefone</strong>; nome e cargo
          permanecem no cadastro operacional/API quando informados, mas não são repetidos nesse bloco do PDF.
        </li>
        <li>
          <strong>Base legal:</strong> execução de procedimentos preliminares a pedido do titular e
          medidas de segurança (LGPD art. 7º e 11º).
        </li>
        <li>
          <strong>Fluxos de gravação:</strong> o diagnóstico pode ser concluído sem conta na plataforma por
          confirmação de e-mail self-service, ou gravado/vinculado em uma sessão com conta na plataforma. Em ambos os
          casos, os pedidos LGPD seguem pelo canal do DPO.
        </li>
        <li>
          <strong>Retenção:</strong> diagnóstico finalizado e logs de auditoria multi-tenant por referência operacional
          de 5 anos; dados pessoais identificáveis até cancelamento + 6 meses, observados os limites legais, o RIPD e a
          política de anonimização quando o registro técnico precisar ser preservado.
        </li>
        <li>
          <strong>Direitos do titular:</strong> confirmação, acesso, correção, anonimização, eliminação
          e portabilidade, nos limites da lei —{" "}
          {dpo ? (
            <>
              contato do DPO:{" "}
              <a className="text-primary underline font-medium" href={`mailto:${dpo.email}`}>
                {dpo.email}
              </a>{" "}
              (ver também{" "}
              <a className="text-primary underline font-medium" href="#dpo">
                seção DPO
              </a>
              ).
            </>
          ) : (
            <>canal do DPO acima, quando configurado, ou contato institucional do controlador.</>
          )}
        </li>
      </ul>
      <p className="text-sm text-muted-foreground pt-2">
        Condições gerais de uso:{" "}
        <Link href="/termos" className="text-primary underline font-medium">
          Termos de uso (MVP)
        </Link>
        .
      </p>
    </div>
  );
}
