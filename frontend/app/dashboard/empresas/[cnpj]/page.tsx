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

export default async function EmpresaDiagnosticosPage({
  params,
  searchParams,
}: {
  params: Promise<{ cnpj: string }>;
  searchParams: Promise<Record<string, string | string[] | undefined>>;
}) {
  const { cnpj } = await params;
  const sp = await searchParams;
  const cnpjNorm = parseCnpjFromRouteSegment(cnpj);
  if (!cnpjNorm) {
    notFound();
  }
  const razaoSocialHint = decodeRazaoSocialHint(sp.razao_social);

  return (
    <EmpresaDiagnosticosClient cnpjNormalizado={cnpjNorm} razaoSocialHint={razaoSocialHint} />
  );
}
