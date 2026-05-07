"use client";

import { useEffect } from "react";

/**
 * Registra SW apenas em produção para PWA B2 (ADR-011).
 * Evita cache acidental em ambiente local durante desenvolvimento.
 */
export function ServiceWorkerRegister(): null {
  useEffect(() => {
    if (process.env.NODE_ENV !== "production") return;
    if (!("serviceWorker" in navigator)) return;

    const run = async () => {
      try {
        await navigator.serviceWorker.register("/sw.js", { scope: "/" });
      } catch (error) {
        console.warn("[pwa] falha ao registrar service worker", error);
      }
    };

    void run();
  }, []);

  return null;
}
