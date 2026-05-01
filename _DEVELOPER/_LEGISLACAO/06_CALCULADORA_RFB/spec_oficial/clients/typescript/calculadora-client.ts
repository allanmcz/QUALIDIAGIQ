/**
 * Cliente TypeScript — Calculadora de Tributos do Consumo (Reforma Tributária)
 *
 * Cliente HTTP enxuto baseado em fetch nativo + Zod para validação runtime.
 * Pertence ao pacote `01_shared/calculadora_rfb` do monorepo Tributiq.
 *
 * Princípios:
 * - Clean Architecture: este módulo é INFRAESTRUTURA. Não importe nada de domínio aqui.
 * - Tipagem forte (Zod schemas → TypeScript types)
 * - Resiliência (retry exponencial)
 * - Compatível com Fastify, Edge Functions Supabase, Cloudflare Workers
 *
 * Autor: Tributiq · Versão: 1.0 · 26/04/2026
 *
 * Documentação oficial:
 * - Swagger UI: https://consumo.tributos.gov.br/servico/calcular-tributos-consumo/api/swagger-ui/index.html
 * - OpenAPI:    https://consumo.tributos.gov.br/servico/calcular-tributos-consumo/api/api-docs
 */

import { z } from "zod";

// ═══════════════════════════════════════════════════════════════════
// Configuração
// ═══════════════════════════════════════════════════════════════════
export const DEFAULT_BASE_URL =
  "https://consumo.tributos.gov.br:18016/servico/calcular-tributos-consumo/api";
export const DEFAULT_TIMEOUT_MS = 30_000;
const USER_AGENT = "Tributiq/1.0 (+https://tributiq.com.br)";

// ═══════════════════════════════════════════════════════════════════
// Schemas Zod (subset essencial — gerar restante com openapi-zod-client)
// ═══════════════════════════════════════════════════════════════════
export const TributacaoRegularInputSchema = z.object({
  cst: z.string().max(3),
  cClassTrib: z.string().max(6),
});

export const ImpostoSeletivoInputSchema = z.object({
  cst: z.string().max(3),
  cClassTrib: z.string().max(6),
  baseCalculo: z.number(),
  impostoInformado: z.number(),
  quantidade: z.number().optional(),
  unidade: z.string().optional(),
});

export const ItemOperacaoInputSchema = z.object({
  numero: z.number().int(),
  cst: z.string().max(3),
  cClassTrib: z.string().max(6),
  ncm: z.string().optional(),
  nbs: z.string().optional(),
  baseCalculo: z.number().optional(),
  quantidade: z.number().optional(),
  unidade: z.string().optional(),
  tributacaoRegular: TributacaoRegularInputSchema.optional(),
  impostoSeletivo: ImpostoSeletivoInputSchema.optional(),
});

export const OperacaoInputSchema = z.object({
  id: z.string(),
  versao: z.string(),
  municipio: z.number().int(),
  itens: z.array(ItemOperacaoInputSchema),
  dhFatoGerador: z.string().optional(),
  uf: z.string().max(2).optional(),
});

export const VersaoOutputSchema = z.object({
  versaoApp: z.string(),
  versaoDb: z.string(),
  descricaoVersaoDb: z.string().optional(),
  dataVersaoDb: z.string().optional(),
  ambiente: z.string().optional(),
});

export const AliquotaDadosAbertosOutputSchema = z.object({
  aliquotaReferencia: z.number(),
  aliquotaPropria: z.number(),
  formaAplicacao: z.enum(["SUBSTITUICAO", "ACRESCIMO", "DECRESCIMO"]),
});

export const UfDadosAbertosOutputSchema = z.object({
  sigla: z.string(),
  nome: z.string(),
  codigo: z.number().int(),
});

export const MunicipioDadosAbertosOutputSchema = z.object({
  codigo: z.number().int(),
  nome: z.string(),
});

export const ProblemDetailSchema = z.object({
  type: z.string().optional(),
  title: z.string().optional(),
  status: z.number().int().optional(),
  detail: z.string().optional(),
  instance: z.string().optional(),
  properties: z.record(z.unknown()).optional(),
});

// Tipos derivados dos schemas
export type OperacaoInput = z.infer<typeof OperacaoInputSchema>;
export type VersaoOutput = z.infer<typeof VersaoOutputSchema>;
export type AliquotaDadosAbertosOutput = z.infer<
  typeof AliquotaDadosAbertosOutputSchema
>;
export type UfDadosAbertosOutput = z.infer<typeof UfDadosAbertosOutputSchema>;
export type MunicipioDadosAbertosOutput = z.infer<
  typeof MunicipioDadosAbertosOutputSchema
>;
export type ProblemDetail = z.infer<typeof ProblemDetailSchema>;

export type TipoDfe =
  | "nfe"
  | "nfce"
  | "nfse"
  | "cte"
  | "cte-simplificado"
  | "bpe"
  | "bpe-tm"
  | "nf3e";

// ═══════════════════════════════════════════════════════════════════
// Erros
// ═══════════════════════════════════════════════════════════════════
export class CalculadoraError extends Error {
  public readonly type?: string;
  public readonly title?: string;
  public readonly status?: number;
  public readonly detail?: string;
  public readonly instance?: string;
  public readonly properties: Record<string, unknown>;

  constructor(problem: ProblemDetail) {
    super(`[${problem.status}] ${problem.title}: ${problem.detail}`);
    this.name = "CalculadoraError";
    this.type = problem.type;
    this.title = problem.title;
    this.status = problem.status;
    this.detail = problem.detail;
    this.instance = problem.instance;
    this.properties = problem.properties ?? {};
  }
}

// ═══════════════════════════════════════════════════════════════════
// Utilitário de retry com backoff exponencial
// ═══════════════════════════════════════════════════════════════════
async function withRetry<T>(
  fn: () => Promise<T>,
  attempts = 3,
  baseDelayMs = 1000,
): Promise<T> {
  let lastErr: unknown;
  for (let i = 0; i < attempts; i++) {
    try {
      return await fn();
    } catch (err) {
      lastErr = err;
      // Não retentar erros 4xx (cliente)
      if (err instanceof CalculadoraError && err.status && err.status < 500) {
        throw err;
      }
      if (i === attempts - 1) break;
      const delay = baseDelayMs * Math.pow(2, i);
      await new Promise((r) => setTimeout(r, delay));
    }
  }
  throw lastErr;
}

// ═══════════════════════════════════════════════════════════════════
// Cliente principal
// ═══════════════════════════════════════════════════════════════════
export interface CalculadoraClientOptions {
  baseUrl?: string;
  timeoutMs?: number;
  fetchImpl?: typeof fetch;
}

export class CalculadoraClient {
  private readonly baseUrl: string;
  private readonly timeoutMs: number;
  private readonly fetchImpl: typeof fetch;

  constructor(opts: CalculadoraClientOptions = {}) {
    this.baseUrl = opts.baseUrl ?? DEFAULT_BASE_URL;
    this.timeoutMs = opts.timeoutMs ?? DEFAULT_TIMEOUT_MS;
    this.fetchImpl = opts.fetchImpl ?? fetch;
  }

  // ─── Núcleo HTTP ───
  private async request<T>(
    method: string,
    path: string,
    opts: {
      query?: Record<string, string | number>;
      jsonBody?: unknown;
      rawBody?: BodyInit;
      contentType?: string;
      schema?: z.ZodSchema<T>;
      acceptXml?: boolean;
    } = {},
  ): Promise<T> {
    const url = new URL(this.baseUrl + path);
    if (opts.query) {
      for (const [k, v] of Object.entries(opts.query)) {
        url.searchParams.set(k, String(v));
      }
    }

    const ctrl = new AbortController();
    const timer = setTimeout(() => ctrl.abort(), this.timeoutMs);

    let body: BodyInit | undefined;
    const headers: Record<string, string> = {
      "User-Agent": USER_AGENT,
      Accept: opts.acceptXml ? "application/xml" : "application/json",
    };
    if (opts.jsonBody !== undefined) {
      body = JSON.stringify(opts.jsonBody);
      headers["Content-Type"] = "application/json";
    } else if (opts.rawBody !== undefined) {
      body = opts.rawBody;
      if (opts.contentType) headers["Content-Type"] = opts.contentType;
    }

    return withRetry(async () => {
      try {
        const r = await this.fetchImpl(url.toString(), {
          method,
          headers,
          body,
          signal: ctrl.signal,
        });

        if (!r.ok) {
          let problem: ProblemDetail = { status: r.status };
          try {
            problem = ProblemDetailSchema.parse(await r.json());
          } catch {
            /* corpo não-JSON */
          }
          throw new CalculadoraError(problem);
        }

        if (opts.acceptXml) {
          // @ts-expect-error — caller espera Response/string
          return (await r.text()) as T;
        }

        const data = await r.json();
        return opts.schema ? opts.schema.parse(data) : (data as T);
      } finally {
        clearTimeout(timer);
      }
    });
  }

  // ═════════════════════════════════════════════════════════════
  // Calculadora
  // ═════════════════════════════════════════════════════════════
  async calcularRegimeGeral(operacao: OperacaoInput): Promise<unknown> {
    OperacaoInputSchema.parse(operacao); // validação de saída
    return this.request<unknown>("POST", "/calculadora/regime-geral", {
      jsonBody: operacao,
    });
  }

  async validarXml(
    xml: string,
    tipo: TipoDfe,
    subtipo: "grupo" | "nota" = "nota",
  ): Promise<unknown> {
    return this.request<unknown>("POST", "/calculadora/xml/validate", {
      query: { tipo, subtipo },
      rawBody: xml,
      contentType: "application/xml",
    });
  }

  async gerarXml(roc: unknown, tipo: TipoDfe): Promise<string> {
    return this.request<string>("POST", "/calculadora/xml/generate", {
      query: { tipo },
      jsonBody: roc,
      acceptXml: true,
    });
  }

  // ═════════════════════════════════════════════════════════════
  // Base de Cálculo
  // ═════════════════════════════════════════════════════════════
  async calcularBcCibs(payload: Record<string, unknown>): Promise<number> {
    const r = await this.request<{ baseCalculo: number }>(
      "POST",
      "/calculadora/base-calculo/cbs-ibs-mercadorias",
      { jsonBody: payload, schema: z.object({ baseCalculo: z.number() }) },
    );
    return r.baseCalculo;
  }

  async calcularBcIs(payload: Record<string, unknown>): Promise<number> {
    const r = await this.request<{ baseCalculo: number }>(
      "POST",
      "/calculadora/base-calculo/is-mercadorias",
      { jsonBody: payload, schema: z.object({ baseCalculo: z.number() }) },
    );
    return r.baseCalculo;
  }

  async calcularBcNfse(payload: Record<string, unknown>): Promise<number> {
    const r = await this.request<{ baseCalculo: number }>(
      "POST",
      "/calculadora/nfse/base-calculo",
      { jsonBody: payload, schema: z.object({ baseCalculo: z.number() }) },
    );
    return r.baseCalculo;
  }

  // ═════════════════════════════════════════════════════════════
  // Pedágio
  // ═════════════════════════════════════════════════════════════
  async calcularPedagio(payload: Record<string, unknown>): Promise<unknown> {
    return this.request<unknown>("POST", "/calculadora/pedagio", {
      jsonBody: payload,
    });
  }

  // ═════════════════════════════════════════════════════════════
  // Dados Abertos
  // ═════════════════════════════════════════════════════════════
  async consultarVersao(): Promise<VersaoOutput> {
    return this.request<VersaoOutput>("GET", "/calculadora/dados-abertos/versao", {
      schema: VersaoOutputSchema,
    });
  }

  async consultarUfs(): Promise<UfDadosAbertosOutput[]> {
    return this.request<UfDadosAbertosOutput[]>(
      "GET",
      "/calculadora/dados-abertos/ufs",
      { schema: z.array(UfDadosAbertosOutputSchema) },
    );
  }

  async consultarMunicipios(siglaUf: string): Promise<MunicipioDadosAbertosOutput[]> {
    return this.request<MunicipioDadosAbertosOutput[]>(
      "GET",
      "/calculadora/dados-abertos/ufs/municipios",
      { query: { siglaUf }, schema: z.array(MunicipioDadosAbertosOutputSchema) },
    );
  }

  async consultarAliquotaUniao(dataRef: string): Promise<AliquotaDadosAbertosOutput> {
    return this.request<AliquotaDadosAbertosOutput>(
      "GET",
      "/calculadora/dados-abertos/aliquota-uniao",
      { query: { data: dataRef }, schema: AliquotaDadosAbertosOutputSchema },
    );
  }

  async consultarAliquotaUf(
    codigoUf: number,
    dataRef: string,
  ): Promise<AliquotaDadosAbertosOutput> {
    return this.request<AliquotaDadosAbertosOutput>(
      "GET",
      "/calculadora/dados-abertos/aliquota-uf",
      {
        query: { codigoUf, data: dataRef },
        schema: AliquotaDadosAbertosOutputSchema,
      },
    );
  }

  async consultarAliquotaMunicipio(
    codigoMunicipio: number,
    dataRef: string,
  ): Promise<AliquotaDadosAbertosOutput> {
    return this.request<AliquotaDadosAbertosOutput>(
      "GET",
      "/calculadora/dados-abertos/aliquota-municipio",
      {
        query: { codigoMunicipio, data: dataRef },
        schema: AliquotaDadosAbertosOutputSchema,
      },
    );
  }

  async consultarNcm(ncm: string, dataRef: string): Promise<unknown> {
    return this.request("GET", "/calculadora/dados-abertos/ncm", {
      query: { ncm, data: dataRef },
    });
  }

  async consultarNbs(nbs: string, dataRef: string): Promise<unknown> {
    return this.request("GET", "/calculadora/dados-abertos/nbs", {
      query: { nbs, data: dataRef },
    });
  }

  async consultarClassificacoesCbsIbs(dataRef: string): Promise<unknown[]> {
    return this.request<unknown[]>(
      "GET",
      "/calculadora/dados-abertos/classificacoes-tributarias/cbs-ibs",
      { query: { data: dataRef } },
    );
  }

  async validarCClassTribDfe(
    siglaDfe: string,
    cClassTrib: string,
    dataRef: string,
  ): Promise<unknown> {
    return this.request(
      "GET",
      `/calculadora/dados-abertos/classificacoes-tributarias/cbs-ibs/${siglaDfe}/${cClassTrib}`,
      { query: { data: dataRef } },
    );
  }

  async consultarFundamentacoesLegais(dataRef: string): Promise<unknown[]> {
    return this.request<unknown[]>(
      "GET",
      "/calculadora/dados-abertos/fundamentacoes-legais",
      { query: { data: dataRef } },
    );
  }
}

// ═══════════════════════════════════════════════════════════════════
// Demo
// ═══════════════════════════════════════════════════════════════════
// $ npx tsx clients/typescript/calculadora-client.ts
if (import.meta.url === `file://${process.argv[1]}`) {
  (async () => {
    const cli = new CalculadoraClient();

    const v = await cli.consultarVersao();
    console.log(`✓ versão app=${v.versaoApp}, db=${v.versaoDb}, amb=${v.ambiente}`);

    const ufs = await cli.consultarUfs();
    console.log(`✓ ${ufs.length} UFs — primeira: ${ufs[0].sigla} (${ufs[0].nome})`);

    const hoje = new Date().toISOString().slice(0, 10);
    const aliq = await cli.consultarAliquotaUniao(hoje);
    console.log(
      `✓ Alíquota CBS hoje: própria=${aliq.aliquotaPropria}% (forma=${aliq.formaAplicacao})`,
    );
  })().catch((e) => {
    console.error("Erro:", e);
    process.exit(1);
  });
}
