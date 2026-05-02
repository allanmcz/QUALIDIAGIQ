import { z } from "zod";

// Utils
function validaCNPJ(cnpj: string): boolean {
  const c = cnpj.replace(/[^\d]/g, "");
  if (c.length !== 14 || !!c.match(/(\d)\1{13}/)) return false;
  const t = c.length - 2;
  const d = c.substring(t);
  const d1 = parseInt(d.charAt(0), 10);
  const d2 = parseInt(d.charAt(1), 10);
  const calc = (x: number) => {
    const n = c.substring(0, x);
    let y = x - 7;
    let s = 0;
    for (let i = x; i >= 1; i--) {
      s += parseInt(n.charAt(x - i), 10) * y--;
      if (y < 2) y = 9;
    }
    const r = 11 - (s % 11);
    return r > 9 ? 0 : r;
  };
  return calc(t) === d1 && calc(t + 1) === d2;
}

/** UFs brasileiras (mesmo conjunto validado na API). */
export const UFS_BR = [
  "AC",
  "AL",
  "AP",
  "AM",
  "BA",
  "CE",
  "DF",
  "ES",
  "GO",
  "MA",
  "MT",
  "MS",
  "MG",
  "PA",
  "PB",
  "PR",
  "PE",
  "PI",
  "RJ",
  "RN",
  "RS",
  "RO",
  "RR",
  "SC",
  "SP",
  "SE",
  "TO",
] as const;

/** Texto do `<option value="">` e validação dos selects do perfil empresa (wizard passo 2). */
export const MENSAGEM_SELECT_PERFIL_EMPRESA = "Selecione a opção.";

const PORTES_EMPRESA = ["micro", "pequeno", "medio", "grande", "enterprise"] as const;
const REGIMES_TRIBUTARIOS = ["simples_nacional", "lucro_presumido", "lucro_real", "mei"] as const;
const SETORES_MACRO = ["comercio", "industria", "servicos", "agro", "consumo"] as const;

function zSelectPerfilEmpresa(valoresPermitidos: readonly string[]) {
  return z.string().refine((val) => val !== "" && valoresPermitidos.includes(val), {
    message: MENSAGEM_SELECT_PERFIL_EMPRESA,
  });
}

export const EmpresaSchema = z.object({
  /** Vazio = não informar CNPJ (self-service / LGPD). Se preenchido, valida DV. */
  cnpj: z
    .string()
    .transform((val) => val.replace(/\D/g, ""))
    .refine((val) => val.length === 0 || val.length === 14, "CNPJ deve ter 14 dígitos ou ficar em branco")
    .refine((val) => val.length === 0 || validaCNPJ(val), "CNPJ inválido"),
  razao_social: z.string().min(3, "Razão social deve ter no mínimo 3 caracteres"),
  porte: zSelectPerfilEmpresa(PORTES_EMPRESA),
  regime: zSelectPerfilEmpresa(REGIMES_TRIBUTARIOS),
  cnae_principal: z
    .string()
    .min(7, "CNAE deve conter 7 dígitos numéricos")
    .max(7)
    .regex(/^\d+$/, "CNAE apenas números"),
  uf: zSelectPerfilEmpresa(UFS_BR),
  setor_macro: zSelectPerfilEmpresa(SETORES_MACRO),
});

export const RespondenteSchema = z.object({
  nome: z.string().min(2, "Nome é obrigatório"),
  email: z.string().email("E-mail inválido"),
  /**
   * M09 — opcional. Armazenado só com dígitos (DDD + número), sem DDI (+55).
   * 10 dígitos (fixo) ou 11 (celular com 9 na frente).
   */
  telefone: z
    .string()
    .optional()
    .transform((raw) => {
      if (raw == null || String(raw).trim() === "") return undefined;
      const d = String(raw).replace(/\D/g, "");
      return d.length === 0 ? undefined : d;
    })
    .refine((v) => v === undefined || v.length === 10 || v.length === 11, {
      message: "Telefone: DDD + número com 10 ou 11 dígitos (sem código do país).",
    }),
});

export const RespostaSchema = z.object({
  pergunta_id: z.string().uuid(),
  valor: z.union([z.string(), z.number(), z.array(z.string())]),
});

export const DiagnosticoPayloadSchema = z.object({
  empresa: EmpresaSchema,
  respondente: RespondenteSchema,
  respostas: z.array(RespostaSchema).min(1, "Responda ao questionário carregado"),
  /** LGPD — consentimento para tratamento dos dados informados (MVP). */
  aceite_termos_privacidade: z.boolean().refine((v) => v === true, {
    message: "É necessário aceitar o tratamento dos dados conforme a política de privacidade.",
  }),
});

export type DiagnosticoPayload = z.infer<typeof DiagnosticoPayloadSchema>;
/** Valores do formulário wizard (entrada Zod — alinha `react-hook-form` + `zodResolver`). */
export type DiagnosticoPayloadFormInput = z.input<typeof DiagnosticoPayloadSchema>;
export type EmpresaData = z.infer<typeof EmpresaSchema>;
export type RespondenteData = z.infer<typeof RespondenteSchema>;
