import Link from "next/link"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"
import { Badge } from "@/components/ui/badge"

export default function DashboardPage() {
  // Mock data para a lista de diagnósticos
  const mockDiagnosticos = [
    {
      id: "71e5d710-1c88-4c6e-826c-d2c6c0e5a871",
      empresa: "Acme Corp S/A",
      plano: "AVANCADO",
      score: 75.5,
      data: "30/04/2026"
    },
    {
      id: "82f6e821-2d99-5d7f-937d-e3d7d1f6b982",
      empresa: "Tech Solutions Ltda",
      plano: "GRATUITO",
      score: 42.0,
      data: "29/04/2026"
    }
  ]

  return (
    <div className="container py-10">
      <div className="flex flex-col gap-8">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Assessoria B2B</h1>
          <p className="text-muted-foreground">
            Gerencie os diagnósticos e planos de ação dos seus clientes.
          </p>
        </div>

        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
          {mockDiagnosticos.map((diag) => (
            <Link key={diag.id} href={`/dashboard/diagnosticos/${diag.id}`}>
              <Card className="hover:border-primary/50 transition-colors cursor-pointer h-full">
                <CardHeader className="pb-2">
                  <div className="flex justify-between items-start">
                    <CardTitle className="text-lg">{diag.empresa}</CardTitle>
                    <Badge variant={diag.plano === "AVANCADO" ? "default" : "secondary"}>
                      {diag.plano}
                    </Badge>
                  </div>
                  <CardDescription>Realizado em {diag.data}</CardDescription>
                </CardHeader>
                <CardContent>
                  <div className="flex flex-col gap-1 mt-2">
                    <span className="text-sm font-medium text-muted-foreground">Score Geral</span>
                    <span className="text-2xl font-bold">{diag.score.toFixed(1)}/100</span>
                    <div className="h-2 rounded-full bg-muted overflow-hidden mt-3" aria-hidden="true">
                      <div
                        className="h-full rounded-full transition-all"
                        style={{
                          width: `${Math.min(100, Math.max(0, diag.score))}%`,
                          backgroundColor:
                            diag.score >= 72
                              ? "rgb(22 163 74)"
                              : diag.score >= 48
                                ? "rgb(234 179 8)"
                                : "rgb(220 38 38)",
                        }}
                      />
                    </div>
                    <span className="text-[10px] text-muted-foreground mt-1">M05 — prévia rápida de gap</span>
                  </div>
                </CardContent>
              </Card>
            </Link>
          ))}
        </div>
      </div>
    </div>
  )
}
