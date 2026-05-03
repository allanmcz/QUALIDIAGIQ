"use client";

import { Suspense, useState } from "react";
import Link from "next/link";
import { useRouter, useSearchParams } from "next/navigation";
import {
  ADMIN_NOME_STORAGE_KEY,
  ADMIN_PERFIL_CONTA_STORAGE_KEY,
  ADMIN_TOKEN_STORAGE_KEY,
  getApiUrlForFetch,
} from "@/lib/api/config";
import { QDI_AUTH_CHANGED_EVENT } from "@/lib/auth/auth_events";
import { mensagemErroHttp } from "@/lib/api/http_errors";
import { destinoSeguroAposLogin } from "@/lib/auth/safe_redirect_after_login";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";

function CadastroPageContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [nome, setNome] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const base = getApiUrlForFetch().replace(/\/$/, "");
      const res = await fetch(`${base}/auth/cadastro`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ nome: nome.trim(), email: email.trim(), password }),
      });

      const raw = await res.text();
      if (!res.ok) {
        throw new Error(mensagemErroHttp(res.status, raw));
      }

      let data: { access_token?: string; nome?: string | null; perfil_conta?: string };
      try {
        data = JSON.parse(raw) as { access_token?: string; nome?: string | null; perfil_conta?: string };
      } catch {
        throw new Error(mensagemErroHttp(res.status, raw));
      }
      if (!data.access_token || typeof data.access_token !== "string") {
        throw new Error("Resposta sem token. Confira a versão da API.");
      }
      localStorage.setItem(ADMIN_TOKEN_STORAGE_KEY, data.access_token);
      localStorage.setItem(ADMIN_NOME_STORAGE_KEY, data.nome || nome.trim() || "Consultor");
      const perfil =
        data.perfil_conta === "avancado" || data.perfil_conta === "gratuito"
          ? data.perfil_conta
          : "gratuito";
      localStorage.setItem(ADMIN_PERFIL_CONTA_STORAGE_KEY, perfil);
      window.dispatchEvent(new Event(QDI_AUTH_CHANGED_EVENT));

      const destino = destinoSeguroAposLogin(searchParams.get("redirect"));
      router.push(destino);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Falha no cadastro");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex h-screen w-full items-center justify-center bg-slate-50 p-4">
      <Card className="w-full max-w-[400px]">
        <CardHeader className="text-center">
          <CardTitle className="text-2xl font-bold">Criar conta B2B</CardTitle>
          <CardDescription>
            Nome, e-mail e senha — mesmo acesso ao painel de diagnósticos que o login. Senha com no mínimo 8
            caracteres.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="nome">Nome</Label>
              <Input
                id="nome"
                type="text"
                autoComplete="name"
                value={nome}
                onChange={(e) => setNome(e.target.value)}
                required
                minLength={1}
                maxLength={255}
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="email">E-mail</Label>
              <Input
                id="email"
                type="email"
                autoComplete="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="password">Senha</Label>
              <Input
                id="password"
                type="password"
                autoComplete="new-password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
                minLength={8}
                maxLength={256}
              />
            </div>
            {error && <div className="text-sm text-red-500 font-medium">{error}</div>}
            <Button type="submit" className="w-full" disabled={loading}>
              {loading ? "Criando conta…" : "Cadastrar e entrar"}
            </Button>
            <p className="text-center text-sm text-muted-foreground">
              Já tem conta?{" "}
              <Link href="/login" className="text-primary font-medium underline underline-offset-2">
                Entrar
              </Link>
            </p>
            <p className="text-xs text-muted-foreground leading-relaxed border-t pt-4">
              MVP: sessão no navegador (localStorage). Em produção o cadastro pode ser desligado na API
              (`QDI_CADASTRO_CONSULTOR_B2B_HABILITADO=false`).
            </p>
          </form>
        </CardContent>
      </Card>
    </div>
  );
}

export default function CadastroPage() {
  return (
    <Suspense
      fallback={
        <div className="flex h-screen w-full items-center justify-center bg-slate-50 text-muted-foreground">
          Carregando…
        </div>
      }
    >
      <CadastroPageContent />
    </Suspense>
  );
}
