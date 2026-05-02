import { z } from "zod";

// Utils
/** DV alinhado ao domínio Python (`cnpj_brasil`) — pesos oficiais RFB. */
function validaCNPJ(cnpj: string): boolean {
  const c = cnpj.replace(/\D/g, "");
  if (c.length !== 14 || /^(\d)\1{13}$/.test(c)) return false;
  const calcDv = (base: string, pesos: number[]) => {
    let soma = 0;
    for (let i = 0; i < base.length; i++) soma += parseInt(base[i]!, 10) * pesos[i]!;
    const resto = soma % 11;
    return resto < 2 ? 0 : 11 - resto;
  };
  const w1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2];
  const w2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2];
  const d1 = calcDv(c.slice(0, 12), w1);
  const d2 = calcDv(c.slice(0, 13), w2);
  return d1 === parseInt(c[12]!, 10) && d2 === parseInt(c[13]!, 10);
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

/** Faixa de faturamento bruto anual autodeclarada (opcional) — slugs alinhados à API Python. */
export const FAIXAS_FATURAMENTO_OPCIONAL = [
  "ate_360_mil",
  "entre_360_mil_e_4_8_mi",
  "entre_4_8_mi_e_10_mi",
  "entre_10_mi_e_60_mi",
  "entre_60_mi_e_100_mi",
  "entre_100_mi_e_500_mi",
  "acima_500_mi",
] as const;

/** Rótulos PT-BR para o `<select>` do wizard (passo empresa). */
export const ROTULOS_FAIXA_FATURAMENTO: Record<(typeof FAIXAS_FATURAMENTO_OPCIONAL)[number], string> = {
  ate_360_mil: "Até R$ 360 mil",
  entre_360_mil_e_4_8_mi: "De R$ 360 mil a R$ 4,8 milhões",
  entre_4_8_mi_e_10_mi: "De R$ 4,8 milhões a R$ 10 milhões",
  entre_10_mi_e_60_mi: "De R$ 10 milhões a R$ 60 milhões",
  entre_60_mi_e_100_mi: "De R$ 60 milhões a R$ 100 milhões",
  entre_100_mi_e_500_mi: "De R$ 100 milhões a R$ 500 milhões",
  acima_500_mi: "Acima de R$ 500 milhões",
};

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
  /** Opcional — omitir ou vazio = não informar (LGPD / minimização). */
  faixa_faturamento: z
    .union([z.literal(""), z.enum(FAIXAS_FATURAMENTO_OPCIONAL)])
    .optional()
    .transform((v) => (v === undefined || v === "" ? undefined : v)),
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

const LOCALES_RELATORIO_PDF = ["pt-BR", "en"] as const;

export const DiagnosticoPayloadSchema = z.object({
  empresa: EmpresaSchema,
  respondente: RespondenteSchema,
  respostas: z.array(RespostaSchema).min(1, "Responda ao questionário carregado"),
  /** Idioma do relatório PDF (WeasyPrint): pt-BR ou en (labels EN; narrativa dinâmica pode seguir em PT). */
  locale_relatorio: z.enum(LOCALES_RELATORIO_PDF).default("pt-BR"),
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
