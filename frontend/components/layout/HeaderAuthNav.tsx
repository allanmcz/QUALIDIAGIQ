"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useLayoutEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import {
  ADMIN_NOME_STORAGE_KEY,
  ADMIN_PERFIL_CONTA_STORAGE_KEY,
  ADMIN_TOKEN_STORAGE_KEY,
} from "@/lib/api/config";
import { QDI_AUTH_CHANGED_EVENT } from "@/lib/auth/auth_events";

/**
 * Sessão B2B (JWT em localStorage) — só no cabeçalho global.
 * Estado inicial «convidado» evita placeholder «…» preso em hidratação; `useLayoutEffect` corrige antes do paint.
 */
export function HeaderAuthNav() {
  const router = useRouter();
  const [nome, setNome] = useState<string | null>(null);

  const sincronizar = useCallback(() => {
    if (typeof window === "undefined") return;
    const token = window.localStorage.getItem(ADMIN_TOKEN_STORAGE_KEY);
    if (!token) {
      setNome(null);
      return;
    }
    setNome(window.localStorage.getItem(ADMIN_NOME_STORAGE_KEY) || "Consultor");
  }, []);

  useLayoutEffect(() => {
    sincronizar();
    const onStorage = (e: StorageEvent) => {
      if (
        e.key === ADMIN_TOKEN_STORAGE_KEY ||
        e.key === ADMIN_NOME_STORAGE_KEY ||
        e.key === ADMIN_PERFIL_CONTA_STORAGE_KEY ||
        e.key === null
      ) {
        sincronizar();
      }
    };
    const onAuth = () => sincronizar();
    window.addEventListener("storage", onStorage);
    window.addEventListener(QDI_AUTH_CHANGED_EVENT, onAuth);
    return () => {
      window.removeEventListener("storage", onStorage);
      window.removeEventListener(QDI_AUTH_CHANGED_EVENT, onAuth);
    };
  }, [sincronizar]);

  const sair = () => {
    window.localStorage.removeItem(ADMIN_TOKEN_STORAGE_KEY);
    window.localStorage.removeItem(ADMIN_NOME_STORAGE_KEY);
    window.localStorage.removeItem(ADMIN_PERFIL_CONTA_STORAGE_KEY);
    window.dispatchEvent(new Event(QDI_AUTH_CHANGED_EVENT));
    router.push("/");
    router.refresh();
  };

  if (nome === null) {
    return (
      <div className="flex items-center gap-1.5 sm:gap-2" role="group" aria-label="Conta consultor B2B">
        <Button variant="outline" size="sm" asChild className="shrink-0">
          <Link href="/cadastro">Cadastrar</Link>
        </Button>
        <Button size="sm" asChild className="shrink-0">
          <Link href="/login?redirect=/dashboard">Entrar</Link>
        </Button>
      </div>
    );
  }

  return (
    <div className="flex items-center gap-1.5 sm:gap-2">
      <span
        className="hidden max-w-[10rem] truncate text-xs text-muted-foreground min-[400px]:inline sm:max-w-[14rem] sm:text-sm"
        title={nome}
      >
        Olá, <span className="font-medium text-foreground">{nome}</span>
      </span>
      <Button variant="outline" size="sm" asChild className="shrink-0">
        <Link href="/dashboard">Painel</Link>
      </Button>
      <Button variant="ghost" size="sm" type="button" className="shrink-0 text-destructive hover:text-destructive" onClick={sair}>
        Sair
      </Button>
    </div>
  );
}
