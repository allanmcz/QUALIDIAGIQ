import DiagnosticoDetalheClient from "./DiagnosticoDetalheClient";

export default async function DiagnosticoDetalhePage({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = await params;
  return <DiagnosticoDetalheClient id={id} />;
}
