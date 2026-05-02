"use client"

import { Suspense, useState } from "react"
import { useRouter, useSearchParams } from "next/navigation"
import { getApiUrlForFetch } from "@/lib/api/config"
import { mensagemErroHttp } from "@/lib/api/http_errors"
import { destinoSeguroAposLogin } from "@/lib/auth/safe_redirect_after_login"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"

function LoginPageContent() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const [email, setEmail] = useState("allan@tributolab.com.br")
  const [password, setPassword] = useState("admin123")
  const [error, setError] = useState("")
  const [loading, setLoading] = useState(false)

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    setError("")
    setLoading(true)

    try {
      const base = getApiUrlForFetch().replace(/\/$/, "")
      const res = await fetch(`${base}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, password })
      })

      const raw = await res.text()
      if (!res.ok) {
        throw new Error(mensagemErroHttp(res.status, raw))
      }

      let data: { access_token?: string; nome?: string | null }
      try {
        data = JSON.parse(raw) as { access_token?: string; nome?: string | null }
      } catch {
        throw new Error(mensagemErroHttp(res.status, raw))
      }
      if (!data.access_token || typeof data.access_token !== "string") {
        throw new Error("Resposta de login sem token. Confira a versão da API.")
      }
      // Salva em localStorage (apenas para o MVP/Dev)
      localStorage.setItem("admin_token", data.access_token)
      localStorage.setItem("admin_nome", data.nome || "Admin")

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
          <CardTitle className="text-2xl font-bold">QualiDiagIQ B2B</CardTitle>
          <CardDescription>
            Acesse o painel do consultor. Conta corporativa após cadastro no ecossistema Tributiq — o login
            desbloqueia gravar o diagnóstico na API e a fase 2 (painel).
          </CardDescription>
        </CardHeader>
        <CardContent>
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
