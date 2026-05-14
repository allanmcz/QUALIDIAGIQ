/**
 * Estado de sessão do painel sem expor o JWT — dados derivados do token httpOnly.
 */

import { cookies } from "next/headers";
import { NextResponse } from "next/server";

import { PAINEL_ACCESS_TOKEN_COOKIE } from "@/lib/auth/painel_access_cookie";
import { jwtExpUnixSeconds, jwtPayloadRecord } from "@/lib/server/jwt_payload_exp";

export const runtime = "nodejs";

export async function GET(): Promise<Response> {
  const jar = await cookies();
  const token = jar.get(PAINEL_ACCESS_TOKEN_COOKIE)?.value?.trim();
  if (!token) {
    return NextResponse.json({ authenticated: false });
  }

  const exp = jwtExpUnixSeconds(token);
  const now = Math.floor(Date.now() / 1000);
  if (exp !== null && now >= exp) {
    return NextResponse.json({ authenticated: false, reason: "expired" });
  }

  const payload = jwtPayloadRecord(token);
  const nome =
    typeof payload?.nome === "string"
      ? payload.nome
      : typeof payload?.name === "string"
        ? payload.name
        : null;
  const perfil =
    payload?.perfil_conta === "avancado" || payload?.perfil_conta === "gratuito"
      ? payload.perfil_conta
      : null;

  return NextResponse.json({
    authenticated: true,
    nome: nome || "Admin",
    perfil_conta: perfil || "gratuito",
  });
}
