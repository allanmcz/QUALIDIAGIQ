/**
 * Proxy HTTP servidor → FastAPI (substitui rewrites frágeis do `next.config` em alguns ambientes).
 *
 * O browser chama sempre same-origin `/api-backend/...`; este handler encaminha para
 * `API_PROXY_TARGET` (ex.: `http://api:8000` no Compose ou `http://127.0.0.1:60000` no host).
 *
 * Se o pedido **não** trouxer `Authorization` e existir cookie httpOnly `qdi_painel_access` (BFF login),
 * o proxy acrescenta `Authorization: Bearer <JWT>` ao upstream — o token não fica em `localStorage`.
 *
 * `Host` no pedido ao upstream vem da URL em `fetch` (Undici); não forçar — cabeçalho proibido na API Fetch.
 */

import { type NextRequest, NextResponse } from "next/server";

import { PAINEL_ACCESS_TOKEN_COOKIE } from "@/lib/auth/painel_access_cookie";
import { resolveApiUpstreamBase } from "@/lib/server/api_proxy_upstream";
import { timeoutProxyMsForRequest } from "@/lib/server/api_proxy_timeout";

export const dynamic = "force-dynamic";
export const runtime = "nodejs";

/** Cabeçalhos repassados à API (contratos da plataforma e JSON). */
const CABECALHOS_REPASSE = [
  "authorization",
  "content-type",
  "idempotency-key",
  "if-match",
  "accept",
  "accept-language",
  "x-rascunho-token",
  "traceparent",
  "tracestate",
] as const;

function montarCaminhoUpstream(segments: string[] | undefined): string {
  if (!segments?.length) return "";
  const joined = segments.join("/");
  if (joined.includes("..") || joined.startsWith("//")) {
    throw new Error("caminho_invalido");
  }
  return `/${joined}`;
}

/**
 * FastAPI exige barra final em algumas coleções (`POST /diagnosticos/`).
 * O browser costuma chamar `/api-backend/diagnosticos` (sem barra) após 308 do Next.
 * Seguir 307/308 com corpo no `fetch` do Node (Undici) falha → «fetch failed».
 */
function normalizarCaminhoUpstreamFastApi(pathSuffix: string, method: string): string {
  /** FastAPI monta `GET/POST` em `/diagnosticos/` — evita 307/308 no proxy Node. */
  if (pathSuffix === "/diagnosticos") {
    return "/diagnosticos/";
  }
  return pathSuffix;
}

function montarCabecalhos(request: NextRequest): Headers {
  const h = new Headers();
  for (const nome of CABECALHOS_REPASSE) {
    const v = request.headers.get(nome);
    if (v) h.set(nome, v);
  }
  if (!h.get("authorization")) {
    const tokenPainel = request.cookies.get(PAINEL_ACCESS_TOKEN_COOKIE)?.value?.trim();
    if (tokenPainel) {
      h.set("authorization", `Bearer ${tokenPainel}`);
    }
  }
  return h;
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
    const base = resolveApiUpstreamBase();
    if (!base) {
      return NextResponse.json(
          {
            detail:
            "Serviço temporariamente indisponível. Tente novamente em instantes ou acione o suporte.",
        },
        { status: 503 },
      );
    }

    let pathSuffix: string;
    try {
      pathSuffix = montarCaminhoUpstream(segments);
    } catch {
      return NextResponse.json({ detail: "Solicitação inválida para este serviço." }, { status: 400 });
    }
    pathSuffix = normalizarCaminhoUpstreamFastApi(pathSuffix, request.method);

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
      signal: AbortSignal.timeout(timeoutProxyMsForRequest(request.method, pathSuffix)),
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
              ? "Serviço temporariamente indisponível. Tente novamente em instantes."
              : "Serviço temporariamente indisponível. Tente novamente em instantes.",
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
          timeout_ms: timeoutProxyMsForRequest(request.method, pathSuffix),
          erro: msg,
        }),
      );
      return NextResponse.json(
        {
          detail: respostaErroProxySeguro()
            ? "Serviço temporariamente indisponível. Tente novamente em instantes."
            : "Serviço temporariamente indisponível. Tente novamente em instantes.",
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
          ? "Serviço temporariamente indisponível. Tente novamente em instantes."
          : "Serviço temporariamente indisponível. Tente novamente em instantes.",
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
