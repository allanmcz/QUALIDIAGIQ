/**
 * Constantes de formulário do assistente — alinhadas a `DiagnosticoPayloadSchema` / API.
 */

import type { DiagnosticoPayloadFormInput } from "@/lib/schemas/wizard";

export const TOTAL_STEPS = 3;

/** Defaults — `reset` ao reiniciar e `useForm.defaultValues`. */
export const DEFAULT_WIZARD_FORM_VALUES: DiagnosticoPayloadFormInput = {
  empresa: {
    cnpj: "",
    razao_social: "",
    porte: "",
    regime: "",
    cnae_principal: "",
    uf: "",
    setor_macro: "",
  },
  respondente: {
    nome: "",
    email: "",
    telefone: "",
  },
  locale_relatorio: "pt-BR",
  plano: "gratuito",
  respostas: [],
  aceite_termos_privacidade: false,
};
