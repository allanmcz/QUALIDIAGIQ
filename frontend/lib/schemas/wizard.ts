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

export const EmpresaSchema = z.object({
  cnpj: z
    .string()
    .min(14, "CNPJ incompleto")
    .transform((val) => val.replace(/\D/g, ""))
    .refine((val) => validaCNPJ(val), "CNPJ inválido"),
  razao_social: z.string().min(3, "Razão social deve ter no mínimo 3 caracteres"),
  porte: z.enum(["micro", "pequeno", "medio", "grande", "enterprise"], {
    errorMap: () => ({ message: "Selecione o porte da empresa" }),
  }),
  regime: z.enum(["simples_nacional", "lucro_presumido", "lucro_real", "mei"], {
    errorMap: () => ({ message: "Selecione o regime tributário" }),
  }),
  cnae_principal: z
    .string()
    .min(7, "CNAE deve conter 7 dígitos numéricos")
    .max(7)
    .regex(/^\d+$/, "CNAE apenas números"),
  uf: z.enum(UFS_BR, { errorMap: () => ({ message: "Selecione um Estado (UF)" }) }),
  setor_macro: z.enum(["comercio", "industria", "servicos", "agro", "consumo"], {
    errorMap: () => ({ message: "Selecione o setor de atuação" }),
  }),
});

export const RespondenteSchema = z.object({
  nome: z.string().min(2, "Nome é obrigatório"),
  email: z.string().email("E-mail inválido"),
  /** M09 — lead B2B opcional (API aceita máx. 32 caracteres). */
  telefone: z.preprocess(
    (v) => {
      if (v === undefined || v === null || v === "") return undefined;
      return typeof v === "string" ? v.trim() : v;
    },
    z.string().max(32, "Telefone muito longo").optional(),
  ),
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
export type EmpresaData = z.infer<typeof EmpresaSchema>;
export type RespondenteData = z.infer<typeof RespondenteSchema>;
