import Link from "next/link";

export const metadata = {
  title: "Política de Privacidade | QualiDiagIQ",
};

export default function PrivacidadePage() {
  return (
    <div className="container max-w-3xl py-12 space-y-6">
      <Link href="/wizard" className="text-sm text-primary hover:underline">
        Voltar ao diagnóstico
      </Link>
      <h1 className="text-3xl font-bold tracking-tight">Política de privacidade (MVP QDI)</h1>
      <p className="rounded-md border border-primary/20 bg-primary/5 px-3 py-2 text-sm text-foreground">
        <strong>Status:</strong> minuta <strong>aprovada</strong> (parecer jurídico de 5 mai. 2026) e{" "}
        <strong>aprovada para publicação</strong> pelo controlador, com o mesmo enquadramento de Termos. LGPD (Lei
        13.709/2018). Em produção: indicar canal DPO, versão e data de vigência no corpo público quando o domínio
        estiver definitivo.
      </p>
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
          diagnóstico no PostgreSQL (Supabase); exclusão e titularidade conforme canal definido em produção.
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
          <strong>Retenção:</strong> pelo tempo necessário ao relatório e obrigações legais; política de
          backup conforme infraestrutura Supabase/PostgreSQL do projeto.
        </li>
        <li>
          <strong>Direitos do titular:</strong> confirmação, acesso, correção, anonimização, eliminação
          e portabilidade, nos limites da lei — canal a definir em produção.
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
