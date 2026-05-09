/**
 * Combina dados canónicos da API de consulta CNPJ com campos `empresa` do wizard.
 *
 * Regra de produto: preenche vazios e sobrescreve quando a fonte devolve valor
 * válido para o formulário — alinhado ao merge servidor + histórico em `AlterarDiagnostico`.
 */

import type { DiagnosticoPayloadFormInput } from "@/lib/schemas/wizard";
import { UFS_BR } from "@/lib/schemas/wizard";
import type { UseFormSetValue } from "react-hook-form";

const PORTES = new Set(["micro", "pequeno", "medio", "grande"]);
const REGIMES = new Set(["simples_nacional", "lucro_presumido", "lucro_real", "mei"]);
const SETORES_MACRO = new Set(["comercio", "industria", "servicos", "agro", "consumo"]);
const UFS = new Set(UFS_BR as unknown as string[]);

export type CnpjCanonicoCampos = {
  cnpj?: string | null;
  razao_social?: string | null;
  nome_fantasia?: string | null;
  cnae_principal?: string | null;
  uf?: string | null;
  situacao_cadastral?: string | null;
  porte?: string | null;
  regime?: string | null;
  setor_macro?: string | null;
  municipio?: string | null;
  logradouro?: string | null;
};

/** Formata CNAE fiscal para 7 dígitos quando a fonte trunca zeros à esquerda. */
function cnaeDigits7(raw: string | null | undefined): string | null {
  const d = String(raw ?? "").replace(/\D/g, "");
  if (!d || d.length > 7) return null;
  const z = d.padStart(7, "0");
  return z.length === 7 && /^\d{7}$/.test(z) ? z : null;
}

function normStr(v: string | null | undefined): string | null {
  const s = String(v ?? "").trim();
  return s || null;
}

/**
 * Escreve valores canónicos no formulário onde forem válidos para o schema Zod.
 * `situacao_cadastral`, `nome_fantasia`, etc. ficam apenas para UX futura —
 * não existem neste passo do wizard.
 */
export function aplicarCanonicoNoFormularioEmpresa(
  canonico: CnpjCanonicoCampos,
  setValue: UseFormSetValue<DiagnosticoPayloadFormInput>,
): void {
  const cnpj = normStr(canonico.cnpj)?.replace(/\D/g, "") ?? "";
  if (cnpj.length === 14) setValue("empresa.cnpj", cnpj, { shouldDirty: true, shouldValidate: true });

  const rz = normStr(canonico.razao_social);
  if (rz) setValue("empresa.razao_social", rz, { shouldDirty: true });

  const cnae = cnaeDigits7(normStr(canonico.cnae_principal));
  if (cnae) setValue("empresa.cnae_principal", cnae, { shouldDirty: true });

  const uf = normStr(canonico.uf)?.toUpperCase().slice(0, 2) ?? "";
  if (uf.length === 2 && UFS.has(uf))
    setValue("empresa.uf", uf as DiagnosticoPayloadFormInput["empresa"]["uf"], { shouldDirty: true });

  const porte = normStr(canonico.porte)?.toLowerCase() ?? "";
  if (porte && PORTES.has(porte))
    setValue("empresa.porte", porte as DiagnosticoPayloadFormInput["empresa"]["porte"], { shouldDirty: true });

  const regime = normStr(canonico.regime)?.toLowerCase() ?? "";
  if (regime && REGIMES.has(regime))
    setValue("empresa.regime", regime as DiagnosticoPayloadFormInput["empresa"]["regime"], {
      shouldDirty: true,
    });

  const setor = normStr(canonico.setor_macro)?.toLowerCase() ?? "";
  if (setor && SETORES_MACRO.has(setor))
    setValue(
      "empresa.setor_macro",
      setor as DiagnosticoPayloadFormInput["empresa"]["setor_macro"],
      { shouldDirty: true },
    );
}
