/**
 * Rascunho do wizard na sessão do navegador — evita perda ao sair para páginas
 * institucionais (ex.: política de privacidade) e voltar.
 *
 * Escopo: mesma aba/sessão; não substitui o fluxo `STORAGE_PENDING_DIAGNOSTICO` (pós-login).
 */

import type { DiagnosticoPayloadFormInput } from "@/lib/schemas/wizard";

export const STORAGE_WIZARD_DRAFT = "qdi_wizard_draft_v1";

export type WizardDraftV1 = {
  v: 1;
  step: number;
  indicePerguntaAtual: number;
  form: DiagnosticoPayloadFormInput;
};

function isRecord(x: unknown): x is Record<string, unknown> {
  return x !== null && typeof x === "object" && !Array.isArray(x);
}

/** Lê e valida estrutura mínima; retorna null se inválido ou ausente. */
export function loadWizardDraft(): WizardDraftV1 | null {
  if (typeof window === "undefined") return null;
  try {
    const raw = sessionStorage.getItem(STORAGE_WIZARD_DRAFT);
    if (!raw) return null;
    const data: unknown = JSON.parse(raw);
    if (!isRecord(data)) return null;
    if (data["v"] !== 1) return null;
    const step = data["step"];
    const indicePerguntaAtual = data["indicePerguntaAtual"];
    const form = data["form"];
    if (typeof step !== "number" || step < 1 || step > 3) return null;
    if (typeof indicePerguntaAtual !== "number" || indicePerguntaAtual < 0) return null;
    if (!isRecord(form)) return null;
    return {
      v: 1,
      step,
      indicePerguntaAtual,
      form: form as DiagnosticoPayloadFormInput,
    };
  } catch {
    return null;
  }
}

export function saveWizardDraft(draft: WizardDraftV1): void {
  if (typeof window === "undefined") return;
  try {
    sessionStorage.setItem(STORAGE_WIZARD_DRAFT, JSON.stringify(draft));
  } catch {
    /* quota / modo privado */
  }
}

export function clearWizardDraft(): void {
  if (typeof window === "undefined") return;
  try {
    sessionStorage.removeItem(STORAGE_WIZARD_DRAFT);
  } catch {
    /* ignore */
  }
}

/**
 * Indica se o rascunho guardado representa progresso real (não só defaults vazios no passo 1).
 * Usado ao reabrir o wizard para decidir se perguntamos «continuar vs reiniciar».
 */
export function wizardDraftHasProgress(draft: WizardDraftV1): boolean {
  if (draft.step >= 2) return true;
  const e = draft.form.empresa;
  const r = draft.form.respondente;
  const cnpjDigits = String(e.cnpj ?? "").replace(/\D/g, "");
  if (cnpjDigits.length >= 14) return true;
  if ((e.razao_social ?? "").trim().length >= 3) return true;
  if ((r.nome ?? "").trim().length >= 1) return true;
  if ((r.email ?? "").trim().length >= 3) return true;
  const tel = String(r.telefone ?? "").replace(/\D/g, "");
  if (tel.length >= 8) return true;
  if (draft.form.aceite_termos_privacidade === true) return true;
  return false;
}
