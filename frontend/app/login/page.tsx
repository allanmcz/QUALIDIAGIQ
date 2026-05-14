"use client"

import Link from "next/link"
import { Suspense, useState } from "react"
import { useRouter, useSearchParams } from "next/navigation"
import { persistPainelSessionMetadataOnly } from "@/lib/api/config"
import { QDI_AUTH_CHANGED_EVENT } from "@/lib/auth/auth_events"
import { mensagemErroHttp } from "@/lib/api/http_errors"
import { setPainelSessionCookiePresent } from "@/lib/auth/session_cookie"
import { destinoSeguroAposLogin } from "@/lib/auth/safe_redirect_after_login"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"

function LoginPageContent() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const [email, setEmail] = useState("")
  const [password, setPassword] = useState("")
  const [error, setError] = useState("")
  const [loading, setLoading] = useState(false)

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    setError("")
    setLoading(true)

    try {
      /** BFF: JWT fica em cookie httpOnly — ver `app/api/auth/login/route.ts`. */
      const res = await fetch("/api/auth/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        credentials: "same-origin",
        body: JSON.stringify({ email, password }),
      })

      const raw = await res.text()
      if (!res.ok) {
        throw new Error(mensagemErroHttp(res.status, raw))
      }

      let data: { ok?: boolean; nome?: string | null; perfil_conta?: string; email?: string }
      try {
        data = JSON.parse(raw) as { ok?: boolean; nome?: string | null; perfil_conta?: string; email?: string }
      } catch {
        throw new Error(mensagemErroHttp(res.status, raw))
      }
      if (!data.ok) {
        throw new Error("Resposta de login inválida. Confira a versão do BFF.")
      }
      const perfil =
        data.perfil_conta === "avancado" || data.perfil_conta === "gratuito"
          ? data.perfil_conta
          : "gratuito"
      persistPainelSessionMetadataOnly({
        nome: data.nome || "Admin",
        email: (data.email ?? email).trim(),
        perfilConta: perfil,
      })
      window.dispatchEvent(new Event(QDI_AUTH_CHANGED_EVENT))
      setPainelSessionCookiePresent(true)

      const destino = destinoSeguroAposLogin(searchParams.get("redirect"))
      router.push(destino)
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Falha na autenticação")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="flex h-screen w-full items-center justify-center bg-slate-50">
      <Card className="w-[400px]">
        <CardHeader className="text-center">
          <CardTitle className="text-2xl font-bold">QualiDiagIQ — conta na plataforma</CardTitle>
          <CardDescription>
            Acesse o painel. Após cadastro no ecossistema Tributiq, o login desbloqueia gravar o diagnóstico na API e a
            fase 2 (painel).
          </CardDescription>
        </CardHeader>
        <CardContent>
          {searchParams.get("sessao") === "expirada" && (
            <div
              className="mb-4 rounded-md border border-amber-500/40 bg-amber-500/10 px-3 py-2 text-sm text-foreground"
              role="status"
              aria-live="polite"
            >
              A sua sessão no painel expirou ou o servidor passou a usar outra chave de assinatura (JWT).
              Entre novamente com e-mail e senha.
            </div>
          )}
          <form onSubmit={handleLogin} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="email">E-mail Corporativo</Label>
              <Input 
                id="email" 
                type="email" 
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
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required 
              />
            </div>
            {error && <div className="text-sm text-red-500 font-medium">{error}</div>}
            <Button type="submit" className="w-full" disabled={loading}>
              {loading ? "Entrando..." : "Entrar no Dashboard"}
            </Button>
            <p className="text-center text-sm text-muted-foreground">
              Ainda não tem conta?{" "}
              <Link href="/cadastro" className="text-primary font-medium underline underline-offset-2">
                Cadastrar
              </Link>
            </p>
            <p className="text-xs text-muted-foreground leading-relaxed border-t pt-4 mt-4">
              MVP/desenvolvimento: sessão mantida no navegador (localStorage). Não é o modelo previsto
              para Enterprise (cookie httpOnly — ver ADR-004). Informações exibidas seguem boa-fé
              informacional (LC 214/2025); não substituem assessoria jurídica.
            </p>
          </form>
        </CardContent>
      </Card>
    </div>
  )
}

export default function LoginPage() {
  return (
    <Suspense
      fallback={
        <div className="flex h-screen w-full items-center justify-center bg-slate-50 text-muted-foreground">
          Carregando…
        </div>
      }
    >
      <LoginPageContent />
    </Suspense>
  )
}
