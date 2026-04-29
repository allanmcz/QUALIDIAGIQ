import { DiagnosticoPayload } from "../schemas/wizard";

const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
// Tenant ID fixo provisório para MVP (o mesmo do seed do banco de dados)
const MOCK_TENANT_ID = "00000000-0000-0000-0000-000000000001";

export async function postDiagnostico(payload: DiagnosticoPayload) {
  try {
    const res = await fetch(`${API_URL}/diagnosticos/`, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        "X-Tenant-ID": MOCK_TENANT_ID,
      },
      body: JSON.stringify(payload),
    });

    if (!res.ok) {
      const errorData = await res.json().catch(() => ({}));
      throw new Error(errorData.detail || `Erro na API: ${res.status}`);
    }

    return await res.json();
  } catch (error) {
    console.error("Falha ao enviar diagnóstico:", error);
    throw error;
  }
}
