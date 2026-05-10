import type { NextRequest } from "next/server";
import { NextResponse } from "next/server";

import { ADMIN_SESSION_COOKIE_FLAG } from "@/lib/auth/session_cookie";

/**
 * Protecção em profundidade das rotas `/dashboard/*`: sem cookie de presença,
 * redireciona para login (o layout cliente continua a validar JWT em `localStorage`).
 */
export function middleware(request: NextRequest) {
  const hasFlag = request.cookies.get(ADMIN_SESSION_COOKIE_FLAG)?.value === "1";
  if (!hasFlag) {
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
