"use client"

import Link from "next/link"
import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"

import {
  ADMIN_NOME_STORAGE_KEY,
  getAccessToken,
} from "@/lib/api/config"
import { clearPainelSessionLocal } from "@/lib/auth/painel_session"
import { setPainelSessionCookiePresent } from "@/lib/auth/session_cookie"

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const router = useRouter()
  const [nome, setNome] = useState<string | null>(null)

  useEffect(() => {
    let cancelado = false

    async function validarSessao(): Promise<void> {
      try {
        const r = await fetch("/api/auth/session", { credentials: "same-origin" })
        const j = (await r.json()) as {
          authenticated?: boolean
          nome?: string | null
          perfil_conta?: string
        }
        if (cancelado) return
        if (j.authenticated) {
          setNome(
            (j.nome && String(j.nome).trim()) ||
              (typeof window !== "undefined"
                ? window.localStorage.getItem(ADMIN_NOME_STORAGE_KEY)
                : null) ||
              "Admin",
          )
          setPainelSessionCookiePresent(true)
          return
        }
      } catch {
        /* rede / BFF indisponível — cai no legado localStorage */
      }
      if (cancelado) return
      const legacy = getAccessToken()
      if (legacy) {
        setNome(
          (typeof window !== "undefined" && window.localStorage.getItem(ADMIN_NOME_STORAGE_KEY)) ||
            "Admin",
        )
        setPainelSessionCookiePresent(true)
        return
      }
      setPainelSessionCookiePresent(false)
      router.push("/login")
    }

    void validarSessao()
    return () => {
      cancelado = true
    }
  }, [router])

  if (!nome) {
    return (
      <div className="flex min-h-screen flex-col bg-slate-50">
        <header className="sticky top-0 z-40 w-full border-b bg-white">
          <div className="container flex h-16 items-center justify-between">
            <div className="h-5 w-36 animate-pulse rounded bg-slate-200" aria-hidden />
            <div className="h-9 w-28 animate-pulse rounded-md bg-slate-200" aria-hidden />
          </div>
        </header>
        <main className="flex-1 p-6">
          <div className="mx-auto max-w-4xl space-y-3">
            <div className="h-8 w-2/3 max-w-md animate-pulse rounded bg-slate-200" aria-hidden />
            <div className="h-36 animate-pulse rounded-lg bg-slate-200" aria-hidden />
          </div>
        </main>
      </div>
    )
  }

  return (
    <div className="flex min-h-screen flex-col bg-slate-50">
      <header className="sticky top-0 z-40 w-full border-b bg-white">
        <div className="container flex h-16 items-center space-x-4 sm:justify-between sm:space-x-0">
          <div className="flex flex-wrap items-center gap-x-6 gap-y-2 md:gap-x-10">
            <Link href="/dashboard/diagnosticos" className="flex items-center space-x-2 font-bold">
              QualiDiagIQ
            </Link>
            <nav className="flex items-center gap-4 text-sm">
              <Link
                href="/dashboard/diagnosticos"
                className="text-slate-600 hover:text-slate-900 underline-offset-4 hover:underline"
              >
                Diagnósticos
              </Link>
              <Link
                href="/dashboard/privacidade"
                className="text-slate-600 hover:text-slate-900 underline-offset-4 hover:underline"
              >
                Privacidade LGPD
              </Link>
            </nav>
          </div>
          <div className="flex flex-1 items-center justify-end space-x-4">
            <nav className="flex items-center space-x-4">
              <span className="text-sm text-slate-500">Olá, {nome}</span>
              <button
                type="button"
                onClick={() => {
                  clearPainelSessionLocal()
                  router.push("/login")
                }}
                className="text-sm font-medium text-red-500 hover:underline"
              >
                Sair
              </button>
            </nav>
          </div>
        </div>
      </header>
      <main className="flex-1">
        {children}
      </main>
    </div>
  )
}
