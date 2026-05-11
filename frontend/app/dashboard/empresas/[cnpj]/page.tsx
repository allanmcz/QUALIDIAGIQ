import { notFound } from "next/navigation";

import EmpresaDiagnosticosClient from "./EmpresaDiagnosticosClient";
import { parseCnpjFromRouteSegment } from "@/lib/dashboard/empresa_diagnostico_urls";

function decodeRazaoSocialHint(raw: string | string[] | undefined): string {
  const v = Array.isArray(raw) ? raw[0] : raw;
  if (!v || typeof v !== "string") return "";
  try {
    return decodeURIComponent(v).trim();
  } catch {
    return v.trim();
  }
}

export default function EmpresaDiagnosticosPage({
  params,
  searchParams,
}: {
  params: { cnpj: string };
  searchParams: Record<string, string | string[] | undefined>;
}) {
  const cnpjNorm = parseCnpjFromRouteSegment(params.cnpj);
  if (!cnpjNorm) {
    notFound();
  }
  const razaoSocialHint = decodeRazaoSocialHint(searchParams.razao_social);

  return (
    <EmpresaDiagnosticosClient cnpjNormalizado={cnpjNorm} razaoSocialHint={razaoSocialHint} />
  );
}
