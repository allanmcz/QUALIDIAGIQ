import Link from "next/link";

export const metadata = {
  title: "Termos de Uso | QualiDiagIQ",
};

/**
 * Versão MVP — revisão jurídica obrigatória antes de produção comercial.
 */
export default function TermosPage() {
  return (
    <div className="container max-w-3xl py-12 space-y-6">
      <Link href="/" className="text-sm text-primary hover:underline">
        Voltar ao início
      </Link>
      <h1 className="text-3xl font-bold tracking-tight">Termos de uso (MVP QDI)</h1>
      <p className="text-muted-foreground">
        Texto-base para transparência no produto. Substitua por versão assinada pela assessoria jurídica
        antes do go-live institucional.
      </p>
      <ul className="list-disc pl-6 space-y-2 text-sm leading-relaxed">
        <li>
          <strong>Objeto:</strong> uso do serviço QualiDiagIQ (diagnóstico de maturidade tributária frente à
          Reforma do Consumo — EC 132/2023, LC 214/2025 e normas correlatas).
        </li>
        <li>
          <strong>Natureza do parecer:</strong> ferramenta de apoio à decisão; não substitui auditoria,
          consultoria fiscal individualizada nem obrigações perante o fisco.
        </li>
        <li>
          <strong>Cadastro e veracidade:</strong> o usuário declara que os dados informados são verdadeiros;
          o score e relatórios dependem da qualidade dessas informações (boa fé informacional — LC 214/2025).
        </li>
        <li>
          <strong>Propriedade intelectual:</strong> marca, layout e metodologia protegidos na forma da lei;
          uso não autorizado de cópia integral do relatório para fins enganosos é vedado.
        </li>
        <li>
          <strong>Limitação de responsabilidade:</strong> na máxima extensão permitida pela lei aplicável,
          exclusão de danos indiretos ou lucros cessantes decorrentes do uso do diagnóstico automatizado.
        </li>
        <li>
          <strong>LGPD:</strong> tratamento de dados conforme{" "}
          <Link href="/privacidade" className="text-primary underline font-medium">
            Política de Privacidade
          </Link>
          .
        </li>
      </ul>
    </div>
  );
}
