"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useLayoutEffect, useState } from "react";

import { Button } from "@/components/ui/button";
import {
  ADMIN_EMAIL_STORAGE_KEY,
  ADMIN_NOME_STORAGE_KEY,
  ADMIN_PERFIL_CONTA_STORAGE_KEY,
  ADMIN_TOKEN_EXPIRES_AT_STORAGE_KEY,
  ADMIN_TOKEN_STORAGE_KEY,
  getAccessToken,
} from "@/lib/api/config";
import { QDI_AUTH_CHANGED_EVENT } from "@/lib/auth/auth_events";
import { clearPainelSessionLocal } from "@/lib/auth/painel_session";

/**
 * Sessão com conta na plataforma no cabeçalho global.
 *
 * Fluxo novo: JWT em cookie httpOnly (`/api/auth/login`); fluxo legado: JWT em `localStorage`.
 */
export function HeaderAuthNav() {
  const router = useRouter();
  const [nome, setNome] = useState<string | null>(null);

  const sincronizar = useCallback(() => {
    if (typeof window === "undefined") return;
    const token = getAccessToken();
    if (token) {
      setNome(window.localStorage.getItem(ADMIN_NOME_STORAGE_KEY) || "Consultor");
      return;
    }
    void fetch("/api/auth/session", { credentials: "same-origin" })
      .then((r) => r.json() as Promise<{ authenticated?: boolean; nome?: string | null }>)
      .then((j) => {
        if (j.authenticated) {
          setNome(
            (j.nome && String(j.nome).trim()) ||
              window.localStorage.getItem(ADMIN_NOME_STORAGE_KEY) ||
              "Consultor",
          );
        } else {
          setNome(null);
        }
      })
      .catch(() => {
        setNome(null);
      });
  }, []);

  useLayoutEffect(() => {
    sincronizar();
    const onStorage = (e: StorageEvent) => {
      if (
        e.key === ADMIN_TOKEN_STORAGE_KEY ||
        e.key === ADMIN_TOKEN_EXPIRES_AT_STORAGE_KEY ||
        e.key === ADMIN_NOME_STORAGE_KEY ||
        e.key === ADMIN_EMAIL_STORAGE_KEY ||
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
    clearPainelSessionLocal();
    router.push("/");
    router.refresh();
  };

  if (nome === null) {
    return (
      <div className="flex items-center gap-1.5 sm:gap-2" role="group" aria-label="Conta na plataforma">
        <Button variant="outline" size="sm" asChild className="shrink-0">
          <Link href="/cadastro">Cadastrar</Link>
        </Button>
        <Button size="sm" asChild className="shrink-0">
          <Link href={`/login?redirect=${encodeURIComponent("/dashboard/diagnosticos")}`}>Entrar</Link>
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
        <Link href="/dashboard/diagnosticos">Painel</Link>
      </Button>
      <Button variant="ghost" size="sm" type="button" className="shrink-0 text-destructive hover:text-destructive" onClick={sair}>
        Sair
      </Button>
    </div>
  );
}
