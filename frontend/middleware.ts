import type { NextRequest } from "next/server";
import { NextResponse } from "next/server";

import { PAINEL_ACCESS_TOKEN_COOKIE } from "@/lib/auth/painel_access_cookie";
import { ADMIN_SESSION_COOKIE_FLAG } from "@/lib/auth/session_cookie";

/**
 * Protecção em profundidade das rotas `/dashboard/*`:
 * exige cookie httpOnly `qdi_painel_access` (BFF) **ou** flag legada `qdi_admin_session` (MVP antigo).
 */
export function middleware(request: NextRequest) {
  const jwtPainel = request.cookies.get(PAINEL_ACCESS_TOKEN_COOKIE)?.value?.trim() ?? "";
  const hasHttpOnlyPainel = jwtPainel.length > 20;
  const hasFlag = request.cookies.get(ADMIN_SESSION_COOKIE_FLAG)?.value === "1";
  if (!hasHttpOnlyPainel && !hasFlag) {
    const url = request.nextUrl.clone();
    url.pathname = "/login";
    url.searchParams.set(
      "redirect",
      `${request.nextUrl.pathname}${request.nextUrl.search}`,
    );
    return NextResponse.redirect(url);
  }
  return NextResponse.next();
}

export const config = {
  matcher: ["/dashboard/:path*"],
};
