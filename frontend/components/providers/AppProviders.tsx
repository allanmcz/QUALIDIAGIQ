"use client";

import { useEffect } from "react";

import { TooltipProvider } from "@/components/ui/tooltip";

/**
 * Envoltório cliente: tooltips Radix + Sentry browser opcional (`NEXT_PUBLIC_SENTRY_DSN`).
 */
export function AppProviders({ children }: { children: React.ReactNode }) {
  useEffect(() => {
    const dsn = process.env.NEXT_PUBLIC_SENTRY_DSN?.trim();
    if (!dsn) return;
    void import("@sentry/browser").then((Sentry) => {
      Sentry.init({
        dsn,
        tracesSampleRate: 0.1,
        environment: process.env.NODE_ENV ?? "development",
      });
    });
  }, []);

  return <TooltipProvider delayDuration={200}>{children}</TooltipProvider>;
}
