import DiagnosticoDetalheClient from "./DiagnosticoDetalheClient";

export default function DiagnosticoDetalhePage({ params }: { params: { id: string } }) {
  return <DiagnosticoDetalheClient id={params.id} />;
}
