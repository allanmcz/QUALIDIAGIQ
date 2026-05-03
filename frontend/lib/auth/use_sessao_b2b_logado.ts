"use client";

import { useCallback, useEffect, useState } from "react";

import { ADMIN_TOKEN_STORAGE_KEY, getAccessToken } from "@/lib/api/config";
import { QDI_AUTH_CHANGED_EVENT } from "@/lib/auth/auth_events";

/**
 * `true` / `false` conforme `admin_token` no localStorage; `undefined` até hidratar no cliente.
 */
export function useSessaoB2bLogado(): boolean | undefined {
  const [logado, setLogado] = useState<boolean | undefined>(undefined);

  const sincronizar = useCallback(() => {
    setLogado(!!getAccessToken());
  }, []);

  useEffect(() => {
    sincronizar();
    const onAuth = () => sincronizar();
    const onStorage = (e: StorageEvent) => {
      if (e.key === ADMIN_TOKEN_STORAGE_KEY || e.key === null) sincronizar();
    };
    window.addEventListener(QDI_AUTH_CHANGED_EVENT, onAuth);
    window.addEventListener("storage", onStorage);
    return () => {
      window.removeEventListener(QDI_AUTH_CHANGED_EVENT, onAuth);
      window.removeEventListener("storage", onStorage);
    };
  }, [sincronizar]);

  return logado;
}
