/**
 * BFF login: chama FastAPI `/auth/login` no servidor e grava JWT em cookie httpOnly.
 *
 * O browser **não** recebe o token no JSON — só metadados para UX (nome, perfil, e-mail).
 */

import { NextResponse } from "next/server";

import {
  PAINEL_ACCESS_COOKIE_MAX_TTL_SEC,
  PAINEL_ACCESS_TOKEN_COOKIE,
} from "@/lib/auth/painel_access_cookie";
import { resolveApiUpstreamBase } from "@/lib/server/api_proxy_upstream";
import { jwtExpUnixSeconds } from "@/lib/server/jwt_payload_exp";

export const runtime = "nodejs";

type CorpoLogin = { email?: string; password?: string };

export async function POST(request: Request): Promise<Response> {
  const base = resolveApiUpstreamBase();
  if (!base) {
    return NextResponse.json(
      {
        detail:
          "Login indisponível: defina API_PROXY_TARGET no Next (ex.: http://127.0.0.1:60000) e reinicie.",
      },
      { status: 503 },
    );
  }

  let corpo: CorpoLogin;
  try {
    corpo = (await request.json()) as CorpoLogin;
  } catch {
    return NextResponse.json({ detail: "JSON inválido" }, { status: 400 });
  }

  const upstream = await fetch(`${base}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json", Accept: "application/json" },
    body: JSON.stringify({
      email: corpo.email ?? "",
      password: corpo.password ?? "",
    }),
  });

  const raw = await upstream.text();
  const ct = upstream.headers.get("content-type") ?? "application/json";

  if (!upstream.ok) {
    return new NextResponse(raw, { status: upstream.status, headers: { "Content-Type": ct } });
  }

  let data: { access_token?: string; nome?: string | null; perfil_conta?: string };
  try {
    data = JSON.parse(raw) as { access_token?: string; nome?: string | null; perfil_conta?: string };
  } catch {
    return NextResponse.json({ detail: "Resposta de login inválida (JSON)" }, { status: 502 });
  }

  const token = data.access_token;
  if (!token || typeof token !== "string") {
    return NextResponse.json({ detail: "Resposta de login sem access_token" }, { status: 502 });
  }

  const exp = jwtExpUnixSeconds(token);
  const now = Math.floor(Date.now() / 1000);
  let maxAge = PAINEL_ACCESS_COOKIE_MAX_TTL_SEC;
  if (exp !== null) {
    maxAge = Math.max(60, Math.min(PAINEL_ACCESS_COOKIE_MAX_TTL_SEC, exp - now));
  }

  const perfil =
    data.perfil_conta === "avancado" || data.perfil_conta === "gratuito" ? data.perfil_conta : "gratuito";
  const emailTrim = (corpo.email ?? "").trim();

  const res = NextResponse.json({
    ok: true,
    nome: data.nome || "Admin",
    email: emailTrim,
    perfil_conta: perfil,
  });

  const secure = process.env.NODE_ENV === "production";
  res.cookies.set({
    name: PAINEL_ACCESS_TOKEN_COOKIE,
    value: token,
    httpOnly: true,
    secure,
    sameSite: "lax",
    path: "/",
    maxAge,
  });

  return res;
}
