/**
 * BFF logout: remove o cookie httpOnly do JWT do painel.
 */

import { NextResponse } from "next/server";

import { ADMIN_SESSION_COOKIE_FLAG } from "@/lib/auth/session_cookie";
import { PAINEL_ACCESS_TOKEN_COOKIE } from "@/lib/auth/painel_access_cookie";

export const runtime = "nodejs";

export async function POST(): Promise<Response> {
  const res = NextResponse.json({ ok: true });
  const secure = process.env.NODE_ENV === "production";
  res.cookies.set({
    name: PAINEL_ACCESS_TOKEN_COOKIE,
    value: "",
    httpOnly: true,
    secure,
    sameSite: "lax",
    path: "/",
    maxAge: 0,
  });
  /** Compat legado: remove flag não-httpOnly usada antes do BFF. */
  res.cookies.set({
    name: ADMIN_SESSION_COOKIE_FLAG,
    value: "",
    path: "/",
    maxAge: 0,
    sameSite: "lax",
  });
  return res;
}
