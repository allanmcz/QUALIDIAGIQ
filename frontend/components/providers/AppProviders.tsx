"use client";

import { useEffect } from "react";

import { ServiceWorkerRegister } from "@/components/pwa/ServiceWorkerRegister";
import { TooltipProvider } from "@/components/ui/tooltip";
import { sentryBrowserBeforeSend } from "@/lib/observability/sentry_scrub";

/**
 * Envoltório cliente: tooltips Radix + Sentry browser opcional (`NEXT_PUBLIC_SENTRY_DSN`).
 * QDI-H-016: `beforeSend` com redaction de PII (`sentryBrowserBeforeSend`).
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
        beforeSend: sentryBrowserBeforeSend,
      });
    });
  }, []);

  return (
    <TooltipProvider delayDuration={200}>
      <ServiceWorkerRegister />
      {children}
    </TooltipProvider>
  );
}
