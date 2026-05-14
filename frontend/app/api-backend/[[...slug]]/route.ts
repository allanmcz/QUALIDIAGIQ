/**
 * Proxy HTTP servidor → FastAPI (substitui rewrites frágeis do `next.config` em alguns ambientes).
 *
 * O browser chama sempre same-origin `/api-backend/...`; este handler encaminha para
 * `API_PROXY_TARGET` (ex.: `http://api:8000` no Compose ou `http://127.0.0.1:60000` no host).
 *
 * `Host` no pedido ao upstream vem da URL em `fetch` (Undici); não forçar — cabeçalho proibido na API Fetch.
 */

import fs from "node:fs";

import { type NextRequest, NextResponse } from "next/server";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

/** Cabeçalhos repassados à API (contratos da plataforma e JSON). */
const CABECALHOS_REPASSE = [
  "authorization",
  "content-type",
  "idempotency-key",
  "accept",
  "accept-language",
  "x-rascunho-token",
  "traceparent",
  "tracestate",
] as const;

function isLikelyDockerContainer(): boolean {
  try {
    return fs.existsSync("/.dockerenv");
  } catch {
    return false;
  }
}

/** Mesma regra que existia em `next.config.mjs` antes do proxy em Route Handler. */
function resolveUpstreamBase(): string | null {
  const explicit = process.env.API_PROXY_TARGET?.trim();
  if (explicit) return explicit.replace(/\/$/, "");
  if (process.env.NODE_ENV === "production") return null;
  // Compose QDI: serviço `api` na rede interna (evita 503 se `.env.local` montado esvaziar o env).
  if (isLikelyDockerContainer()) return "http://api:8000";
  return "http://127.0.0.1:60000";
}

function montarCaminhoUpstream(segments: string[] | undefined): string {
  if (!segments?.length) return "";
  const joined = segments.join("/");
  if (joined.includes("..") || joined.startsWith("//")) {
    throw new Error("caminho_invalido");
  }
  return `/${joined}`;
}

function montarCabecalhos(request: NextRequest): Headers {
  const h = new Headers();
  for (const nome of CABECALHOS_REPASSE) {
    const v = request.headers.get(nome);
    if (v) h.set(nome, v);
  }
  return h;
}

/** Timeout ms para pedidos ao upstream (env opcional). */
function timeoutProxyMs(): number {
  const bruto = process.env.API_PROXY_TIMEOUT_MS?.trim();
  const n = bruto ? Number.parseInt(bruto, 10) : NaN;
  if (Number.isFinite(n) && n > 0) return Math.min(n, 120_000);
  return 30_000;
}

/** QDI-H-036 — em produção não expor host interno / stack ao browser. */
function respostaErroProxySeguro(): boolean {
  return process.env.NODE_ENV === "production" || process.env.QDI_PROXY_SAFE_ERRORS === "1";
}

/** Cabeçalhos que não devem ser repassados ao browser nem podem falhar em `Headers.append`. */
const OMITIR_CABECALHO_RESPOSTA = new Set([
  "connection",
  "keep-alive",
  "transfer-encoding",
  "content-encoding",
  "content-length",
  "proxy-authenticate",
  "proxy-authorization",
  "te",
  "trailer",
  "upgrade",
]);

function montarCabecalhosResposta(upstream: Response, buf: ArrayBuffer): Headers {
  const out = new Headers();
  upstream.headers.forEach((value, key) => {
    const k = key.toLowerCase();
    if (OMITIR_CABECALHO_RESPOSTA.has(k)) return;
    try {
      out.append(key, value);
    } catch {
      /* Nome/valor inválido para `Response` no runtime — ignorar (evita 500 genérico no Next). */
    }
  });
  out.set("content-length", String(buf.byteLength));
  return out;
}

async function proxy(request: NextRequest, segments: string[] | undefined): Promise<Response> {
  try {
    const base = resolveUpstreamBase();
    if (!base) {
      return NextResponse.json(
        {
          detail:
            "Proxy /api-backend indisponível: defina API_PROXY_TARGET no ambiente do Next " +
            "(ex.: http://api:8000 no Docker ou http://127.0.0.1:60000 no host) e reinicie o servidor.",
        },
        { status: 503 },
      );
    }

    let pathSuffix: string;
    try {
      pathSuffix = montarCaminhoUpstream(segments);
    } catch {
      return NextResponse.json({ detail: "Caminho de proxy inválido" }, { status: 400 });
    }

    const alvo = `${base}${pathSuffix}${request.nextUrl.search}`;
    const headers = montarCabecalhos(request);

    const init: RequestInit = {
      method: request.method,
      headers,
      /**
       * Seguir redirecionamentos **no servidor** (Undici), não repassar 3xx ao browser.
       * Com `manual`, o FastAPI/Starlette pode devolver `Location: http://api:8000/...`
       * (host interno do Compose); o browser tenta seguir esse URL → hostname «api» irreconhecível
       * → «Failed to fetch» sem resposta HTTP legível no painel.
       */
      redirect: "follow",
      signal: AbortSignal.timeout(timeoutProxyMs()),
    };

    if (!["GET", "HEAD"].includes(request.method)) {
      const corpoEntrada = await request.arrayBuffer();
      if (corpoEntrada.byteLength > 0) {
        init.body = corpoEntrada;
      }
    }

    try {
      const upstream = await fetch(alvo, init);
      /** Corpo em buffer: reencaminhar `ReadableStream` cru falha em alguns browsers (fetch → «Failed to fetch»). */
      const buf = await upstream.arrayBuffer();
      const out = montarCabecalhosResposta(upstream, buf);
      try {
        return new NextResponse(buf, {
          status: upstream.status,
          statusText: upstream.statusText,
          headers: out,
        });
      } catch (montagem) {
        const m = montagem instanceof Error ? montagem.message : String(montagem);
        console.error(
          JSON.stringify({
            evento: "qdi_api_proxy_next_response_falhou",
            metodo: request.method,
            upstream_base: base,
            caminho: pathSuffix || "/",
            erro: m,
          }),
        );
        return NextResponse.json(
          {
            detail: respostaErroProxySeguro()
              ? "Indisponível temporariamente (proxy). Consulte os logs do servidor."
              : "Proxy não conseguiu montar a resposta ao browser (cabeçalhos/corpo). " +
                  `Verifique logs «qdi_api_proxy_next_response_falhou». Detalhe: ${m}`,
          },
          { status: 502 },
        );
      }
    } catch (e) {
      const msg = e instanceof Error ? e.message : String(e);
      console.error(
        JSON.stringify({
          evento: "qdi_api_proxy_upstream_falhou",
          metodo: request.method,
          upstream_base: base,
          caminho: pathSuffix || "/",
          timeout_ms: timeoutProxyMs(),
          erro: msg,
        }),
      );
      return NextResponse.json(
        {
          detail: respostaErroProxySeguro()
            ? "Indisponível temporariamente (proxy). Consulte os logs do servidor."
            : `Falha ao contactar a API em «${base}» (${pathSuffix || "/"}). ` + `Erro: ${msg}`,
        },
        { status: 502 },
      );
    }
  } catch (inesperado) {
    const msg = inesperado instanceof Error ? inesperado.message : String(inesperado);
    console.error(
      JSON.stringify({
        evento: "qdi_api_proxy_excecao_nao_tratada",
        metodo: request.method,
        erro: msg,
      }),
    );
    return NextResponse.json(
      {
        detail: respostaErroProxySeguro()
          ? "Indisponível temporariamente (proxy). Consulte os logs do servidor."
          : `Exceção no proxy /api-backend (evita página HTML «Internal Server Error»). Detalhe: ${msg}`,
      },
      { status: 502 },
    );
  }
}

/** Next 15: ``params`` em dynamic routes é assíncrono. */
type RotaCtx = { params: Promise<{ slug?: string[] }> };

async function segmentos(ctx: RotaCtx): Promise<string[] | undefined> {
  const p = await ctx.params;
  return p.slug;
}

export async function GET(request: NextRequest, ctx: RotaCtx) {
  return proxy(request, await segmentos(ctx));
}

export async function POST(request: NextRequest, ctx: RotaCtx) {
  return proxy(request, await segmentos(ctx));
}

export async function PUT(request: NextRequest, ctx: RotaCtx) {
  return proxy(request, await segmentos(ctx));
}

export async function PATCH(request: NextRequest, ctx: RotaCtx) {
  return proxy(request, await segmentos(ctx));
}

export async function DELETE(request: NextRequest, ctx: RotaCtx) {
  return proxy(request, await segmentos(ctx));
}

export async function OPTIONS(request: NextRequest, ctx: RotaCtx) {
  return proxy(request, await segmentos(ctx));
}
