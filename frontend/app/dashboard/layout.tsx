import { Metadata } from "next"

export const metadata: Metadata = {
  title: "Dashboard | QualiDiagIQ",
  description: "Gerencie as frentes de trabalho da Reforma Tributária",
}

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode
}) {
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
            <nav className="flex items-center space-x-1">
              <span className="text-sm text-slate-500">Logado como Admin</span>
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
