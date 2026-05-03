/**
 * Proxy HTTP servidor → FastAPI (substitui rewrites frágeis do `next.config` em alguns ambientes).
 *
 * O browser chama sempre same-origin `/api-backend/...`; este handler encaminha para
 * `API_PROXY_TARGET` (ex.: `http://api:8000` no Compose ou `http://127.0.0.1:60000` no host).
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

async function proxy(request: NextRequest, segments: string[] | undefined): Promise<Response> {
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
    redirect: "manual",
  };

  if (!["GET", "HEAD"].includes(request.method)) {
    const buf = await request.arrayBuffer();
    if (buf.byteLength > 0) {
      init.body = buf;
    }
  }

  try {
    const upstream = await fetch(alvo, init);
    /** Corpo em buffer: reencaminhar `ReadableStream` cru falha em alguns browsers (fetch → «Failed to fetch»). */
    const buf = await upstream.arrayBuffer();
    const out = new Headers();
    const omitir = new Set(["connection", "keep-alive", "transfer-encoding", "content-encoding"]);
    upstream.headers.forEach((value, key) => {
      if (!omitir.has(key.toLowerCase())) {
        out.set(key, value);
      }
    });
    out.set("content-length", String(buf.byteLength));
    return new NextResponse(buf, {
      status: upstream.status,
      statusText: upstream.statusText,
      headers: out,
    });
  } catch (e) {
    const msg = e instanceof Error ? e.message : String(e);
    return NextResponse.json(
      {
        detail: `Falha ao contactar a API em «${base}» (${pathSuffix || "/"}). ` + `Erro: ${msg}`,
      },
      { status: 502 },
    );
  }
}

type RotaCtx = { params: { slug?: string[] } };

export async function GET(request: NextRequest, ctx: RotaCtx) {
  return proxy(request, ctx.params.slug);
}

export async function POST(request: NextRequest, ctx: RotaCtx) {
  return proxy(request, ctx.params.slug);
}

export async function PUT(request: NextRequest, ctx: RotaCtx) {
  return proxy(request, ctx.params.slug);
}

export async function PATCH(request: NextRequest, ctx: RotaCtx) {
  return proxy(request, ctx.params.slug);
}

export async function DELETE(request: NextRequest, ctx: RotaCtx) {
  return proxy(request, ctx.params.slug);
}

export async function OPTIONS(request: NextRequest, ctx: RotaCtx) {
  return proxy(request, ctx.params.slug);
}
