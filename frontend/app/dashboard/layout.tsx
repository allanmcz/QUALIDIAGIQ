"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"

import {
  ADMIN_NOME_STORAGE_KEY,
  ADMIN_PERFIL_CONTA_STORAGE_KEY,
  ADMIN_TOKEN_STORAGE_KEY,
} from "@/lib/api/config"
import { QDI_AUTH_CHANGED_EVENT } from "@/lib/auth/auth_events"

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const router = useRouter()
  const [nome, setNome] = useState<string | null>(null)

  useEffect(() => {
    const token = localStorage.getItem(ADMIN_TOKEN_STORAGE_KEY)
    if (!token) {
      router.push("/login")
    } else {
      setNome(localStorage.getItem(ADMIN_NOME_STORAGE_KEY) || "Admin")
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
          <div className="flex gap-6 md:gap-10">
            <a href="/dashboard" className="flex items-center space-x-2">
              <span className="inline-block font-bold">QualiDiagIQ B2B</span>
            </a>
          </div>
          <div className="flex flex-1 items-center justify-end space-x-4">
            <nav className="flex items-center space-x-4">
              <span className="text-sm text-slate-500">Olá, {nome}</span>
              <button
                type="button"
                onClick={() => {
                  localStorage.removeItem(ADMIN_TOKEN_STORAGE_KEY)
                  localStorage.removeItem(ADMIN_NOME_STORAGE_KEY)
                  localStorage.removeItem(ADMIN_PERFIL_CONTA_STORAGE_KEY)
                  window.dispatchEvent(new Event(QDI_AUTH_CHANGED_EVENT))
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
