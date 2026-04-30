"use client"

import { useEffect, useState } from "react"
import { useRouter } from "next/navigation"

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
  const router = useRouter()
  const [nome, setNome] = useState<string | null>(null)

  useEffect(() => {
    const token = localStorage.getItem("admin_token")
    if (!token) {
      router.push("/login")
    } else {
      setNome(localStorage.getItem("admin_nome") || "Admin")
    }
  }, [router])

  if (!nome) return null // ou um skeleton/loading spinner

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
                onClick={() => { localStorage.clear(); router.push("/login") }}
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
