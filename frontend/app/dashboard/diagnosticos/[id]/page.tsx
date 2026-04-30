import Link from "next/link"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card"

// Tipos baseados no backend
type Acao = { descricao: string; responsavel: string; prazo: string; criticidade: string }
type Frente = { nome: string; acoes: Acao[] }
type DiagnosticoData = {
  id: string
  empresa_razao_social: string
  plano: string
  status: string
  checklist: Frente[] | null
}

async function getDiagnostico(id: string): Promise<DiagnosticoData> {
  try {
    const res = await fetch(`http://127.0.0.1:8000/diagnosticos/${id}`, {
      headers: { "X-Tenant-ID": "11111111-1111-1111-1111-111111111111" },
      cache: "no-store"
    })
    
    if (res.ok) {
      return await res.json()
    }
  } catch (e) {
    console.error("Erro ao buscar API, usando mock", e)
  }

  // Fallback Mock para UX (para funcionar mesmo sem backend ativo no exato momento)
  const isAvancado = id.startsWith("7")
  return {
    id,
    empresa_razao_social: isAvancado ? "Acme Corp S/A" : "Tech Solutions Ltda",
    plano: isAvancado ? "avancado" : "gratuito",
    status: "finalizado",
    checklist: isAvancado ? [
      {
        nome: "Governança e Comitê",
        acoes: [
          { descricao: "Constituir Comitê Tributário Reforma", responsavel: "Diretoria", prazo: "Out/2025", criticidade: "Crítica" },
          { descricao: "Aprovar plano-mestre de implantação", responsavel: "Comitê", prazo: "Nov/2025", criticidade: "Alta" }
        ]
      },
      {
        nome: "TI / ERP / Sistema Fiscal",
        acoes: [
          { descricao: "Levantar gap funcional do ERP", responsavel: "TI / Fiscal", prazo: "Dez/2025", criticidade: "Crítica" }
        ]
      }
    ] : null
  }
}

export default async function DiagnosticoDetalhePage({ params }: { params: { id: string } }) {
  const data = await getDiagnostico(params.id)
  const isFree = data.plano === "gratuito"

  return (
    <div className="container py-10">
      <div className="mb-8">
        <Link href="/dashboard" className="text-sm text-primary hover:underline mb-4 inline-block">
          &larr; Voltar para Dashboard
        </Link>
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold">{data.empresa_razao_social}</h1>
            <p className="text-muted-foreground">ID do Diagnóstico: {data.id}</p>
          </div>
          <Badge variant={isFree ? "secondary" : "default"} className="text-sm px-4 py-1">
            PLANO {data.plano.toUpperCase()}
          </Badge>
        </div>
      </div>

      {isFree ? (
        <div className="relative rounded-xl border bg-card text-card-foreground shadow overflow-hidden">
          {/* Efeito de Blur / Paywall */}
          <div className="absolute inset-0 z-10 bg-background/50 backdrop-blur-[6px] flex flex-col items-center justify-center p-6 text-center">
            <h2 className="text-2xl font-bold mb-2">Desbloqueie o Plano de Ação Completo</h2>
            <p className="text-muted-foreground mb-6 max-w-md">
              Faça o upgrade para o plano Avançado e tenha acesso à matriz de impacto departamental e ao quadro interativo Kanban gerado exclusivamente para a sua empresa pela nossa IA.
            </p>
            <Button size="lg" className="font-bold">
              Fazer Upgrade Agora
            </Button>
          </div>
          
          {/* Fundo borrado imitando o Kanban */}
          <div className="p-8 opacity-40 select-none pointer-events-none">
            <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
              {[1, 2, 3].map(i => (
                <div key={i} className="bg-slate-100 p-4 rounded-lg min-h-[400px]">
                  <div className="h-4 w-32 bg-slate-300 rounded mb-4"></div>
                  <div className="bg-white p-4 rounded shadow-sm mb-3">
                    <div className="h-3 w-full bg-slate-200 rounded mb-2"></div>
                    <div className="h-3 w-2/3 bg-slate-200 rounded"></div>
                  </div>
                  <div className="bg-white p-4 rounded shadow-sm mb-3">
                    <div className="h-3 w-full bg-slate-200 rounded mb-2"></div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      ) : (
        <div className="space-y-8">
          <div className="flex justify-between items-center">
            <h2 className="text-2xl font-bold tracking-tight">Quadro Kanban de Implantação</h2>
            <Button variant="outline">Exportar para CSV</Button>
          </div>

          <div className="flex gap-6 overflow-x-auto pb-4">
            {/* Coluna: A Fazer */}
            <div className="flex-1 min-w-[320px] bg-slate-100 rounded-lg p-4">
              <h3 className="font-semibold text-slate-700 mb-4 flex items-center justify-between">
                A Fazer 
                <Badge variant="secondary">{data.checklist?.reduce((acc, f) => acc + f.acoes.length, 0) || 0}</Badge>
              </h3>
              
              <div className="space-y-3">
                {data.checklist?.map((frente, i) => (
                  <div key={i}>
                    <div className="text-xs font-bold text-slate-500 uppercase mb-2 mt-4 first:mt-0">{frente.nome}</div>
                    {frente.acoes.map((acao, j) => (
                      <Card key={j} className="mb-2 cursor-grab active:cursor-grabbing hover:border-primary/50 transition-colors">
                        <CardHeader className="p-4 pb-2">
                          <CardTitle className="text-sm font-medium leading-tight">
                            {acao.descricao}
                          </CardTitle>
                        </CardHeader>
                        <CardContent className="p-4 pt-0">
                          <div className="flex justify-between items-center mt-4">
                            <span className="text-xs text-muted-foreground">{acao.responsavel}</span>
                            <Badge variant={acao.criticidade === "Crítica" ? "destructive" : "secondary"} className="text-[10px]">
                              {acao.criticidade}
                            </Badge>
                          </div>
                        </CardContent>
                      </Card>
                    ))}
                  </div>
                ))}
              </div>
            </div>

            {/* Coluna: Em Andamento */}
            <div className="flex-1 min-w-[320px] bg-slate-100 rounded-lg p-4">
              <h3 className="font-semibold text-slate-700 mb-4 flex items-center justify-between">
                Em Andamento
                <Badge variant="secondary">0</Badge>
              </h3>
              <div className="h-full flex items-center justify-center border-2 border-dashed border-slate-300 rounded-lg">
                <span className="text-sm text-slate-400">Arraste cards para cá</span>
              </div>
            </div>

            {/* Coluna: Concluído */}
            <div className="flex-1 min-w-[320px] bg-slate-100 rounded-lg p-4">
              <h3 className="font-semibold text-slate-700 mb-4 flex items-center justify-between">
                Concluído
                <Badge variant="secondary">0</Badge>
              </h3>
              <div className="h-full flex items-center justify-center border-2 border-dashed border-slate-300 rounded-lg">
                <span className="text-sm text-slate-400">Arraste cards para cá</span>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
