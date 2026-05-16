"use client";

import Link from "next/link";
import { useCallback, useEffect, useMemo, useRef, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { fetchDiagnosticoDetalhe } from "@/lib/api/fetch_diagnostico_detalhe";
import {
  fetchDiagnosticosResumoTodasPaginasPorEmpresa,
  type DiagnosticoResumoApi,
} from "@/lib/api/lista_diagnosticos";
import { postRegistrarSolicitacaoLgpd } from "@/lib/api/privacidade_lgpd";
import { cn } from "@/lib/utils";
import { mascaraCnpj14 } from "@/lib/painel/formatar_cnpj";
import {
  agruparEmpresasDeDiagnosticos,
  carregarDiagnosticosParaIndiceEmpresas,
  filtrarEmpresasIndice,
  type EmpresaPrivacidadeIndice,
} from "@/lib/painel/privacidade_empresa_indice";

const ROTULO_TIPO: Record<string, string> = {
  acesso: "Acesso",
  correcao: "Correção",
  anonimizacao: "Anonimização",
  eliminacao: "Eliminação",
  portabilidade: "Portabilidade",
  oposicao: "Oposição",
};

type Props = {
  /** Pré-seleção via menu Ações ou URL `diagnostico_id`. */
  diagnosticoIdInicial?: string;
  onRegistrado?: () => void;
  onMensagem?: (msg: string) => void;
  onErro?: (msg: string) => void;
  /** Empresa escolhida — para filtrar a lista de solicitações no cartão inferior. */
  onEmpresaSelecionada?: (empresa: EmpresaPrivacidadeIndice | null) => void;
  /** Um único diagnóstico marcado — retificações WORM (cartão opcional no pai). */
  onDiagnosticoUnicoSelecionado?: (diag: DiagnosticoResumoApi | null) => void;
  /** IDs dos diagnósticos da empresa em foco — filtro da lista no pai. */
  onDiagnosticosEmpresaCarregados?: (lista: DiagnosticoResumoApi[]) => void;
};

function formatarData(iso: string | null | undefined): string {
  if (!iso) return "—";
  const d = iso.slice(0, 10);
  if (d.length !== 10) return iso;
  const [y, m, day] = d.split("-");
  return `${day}/${m}/${y}`;
}

export function PrivacidadeNovaSolicitacaoCard({
  diagnosticoIdInicial = "",
  onRegistrado,
  onMensagem,
  onErro,
  onEmpresaSelecionada,
  onDiagnosticoUnicoSelecionado,
  onDiagnosticosEmpresaCarregados,
}: Props) {
  const [indiceCarregando, setIndiceCarregando] = useState(true);
  const [empresasIndice, setEmpresasIndice] = useState<EmpresaPrivacidadeIndice[]>([]);

  const [buscaEmpresa, setBuscaEmpresa] = useState("");
  const [listaAberta, setListaAberta] = useState(false);
  const buscaRef = useRef<HTMLInputElement>(null);

  const [empresaSel, setEmpresaSel] = useState<EmpresaPrivacidadeIndice | null>(null);
  const [diagnosticos, setDiagnosticos] = useState<DiagnosticoResumoApi[]>([]);
  const [diagCarregando, setDiagCarregando] = useState(false);
  const [diagErro, setDiagErro] = useState<string | null>(null);

  const [marcados, setMarcados] = useState<Set<string>>(new Set());

  const [regTipo, setRegTipo] = useState("anonimizacao");
  const [regEmail, setRegEmail] = useState("");
  const [regMemo, setRegMemo] = useState("");
  const [regSalvando, setRegSalvando] = useState(false);

  const sugestoes = useMemo(
    () => filtrarEmpresasIndice(empresasIndice, buscaEmpresa),
    [empresasIndice, buscaEmpresa],
  );

  const idsMarcados = useMemo(() => [...marcados], [marcados]);

  const diagnosticoUnico = useMemo(() => {
    if (idsMarcados.length !== 1) return null;
    return diagnosticos.find((d) => d.id === idsMarcados[0]) ?? null;
  }, [idsMarcados, diagnosticos]);

  useEffect(() => {
    onDiagnosticoUnicoSelecionado?.(diagnosticoUnico);
  }, [diagnosticoUnico, onDiagnosticoUnicoSelecionado]);

  useEffect(() => {
    let cancelado = false;
    setIndiceCarregando(true);
    void carregarDiagnosticosParaIndiceEmpresas()
      .then((lista) => {
        if (cancelado) return;
        setEmpresasIndice(agruparEmpresasDeDiagnosticos(lista));
      })
      .catch((e) => {
        if (cancelado) return;
        onErro?.(e instanceof Error ? e.message : "Falha ao carregar empresas do tenant.");
      })
      .finally(() => {
        if (!cancelado) setIndiceCarregando(false);
      });
    return () => {
      cancelado = true;
    };
  }, [onErro]);

  const selecionarEmpresa = useCallback(
    async (empresa: EmpresaPrivacidadeIndice, preMarcarId?: string) => {
      setEmpresaSel(empresa);
      onEmpresaSelecionada?.(empresa);
      setBuscaEmpresa(`${mascaraCnpj14(empresa.cnpj14)} — ${empresa.razao_social}`);
      setListaAberta(false);
      setDiagCarregando(true);
      setDiagErro(null);
      setMarcados(new Set());
      try {
        const lista = await fetchDiagnosticosResumoTodasPaginasPorEmpresa(empresa.cnpj14);
        const ordenada = [...lista].sort((a, b) => {
          const na = a.numero_interno_grupo ?? 0;
          const nb = b.numero_interno_grupo ?? 0;
          return nb - na;
        });
        setDiagnosticos(ordenada);
        onDiagnosticosEmpresaCarregados?.(ordenada);
        if (preMarcarId && ordenada.some((d) => d.id === preMarcarId)) {
          setMarcados(new Set([preMarcarId]));
        }
      } catch (e) {
        setDiagnosticos([]);
        setDiagErro(e instanceof Error ? e.message : "Falha ao carregar diagnósticos da empresa.");
      } finally {
        setDiagCarregando(false);
      }
    },
    [onEmpresaSelecionada, onDiagnosticosEmpresaCarregados],
  );

  useEffect(() => {
    const id = diagnosticoIdInicial.trim();
    if (id.length < 32 || empresaSel != null) return;
    let cancelado = false;
    void fetchDiagnosticoDetalhe(id)
      .then((det) => {
        if (cancelado) return;
        const cnpj14 = (det.empresa_cnpj ?? "").replace(/\D/g, "");
        if (cnpj14.length !== 14) {
          onErro?.("Diagnóstico sem CNPJ — selecione a empresa manualmente.");
          return;
        }
        const empresa: EmpresaPrivacidadeIndice = {
          cnpj14,
          razao_social: det.empresa_razao_social?.trim() || "—",
        };
        void selecionarEmpresa(empresa, id);
      })
      .catch((e) => {
        if (!cancelado) onErro?.(e instanceof Error ? e.message : "Não foi possível abrir o diagnóstico.");
      });
    return () => {
      cancelado = true;
    };
  }, [diagnosticoIdInicial, empresaSel, onErro, selecionarEmpresa]);

  const toggleMarcado = (diagId: string) => {
    setMarcados((prev) => {
      const next = new Set(prev);
      if (next.has(diagId)) next.delete(diagId);
      else next.add(diagId);
      return next;
    });
  };

  const marcarTodos = () => {
    setMarcados(new Set(diagnosticos.map((d) => d.id)));
  };

  const limparMarcados = () => setMarcados(new Set());

  const limparEmpresa = () => {
    setEmpresaSel(null);
    onEmpresaSelecionada?.(null);
    setBuscaEmpresa("");
    setDiagnosticos([]);
    onDiagnosticosEmpresaCarregados?.([]);
    setMarcados(new Set());
    setDiagErro(null);
  };

  const registrar = async () => {
    const email = regEmail.trim();
    if (!email) {
      onErro?.("Informe o e-mail do solicitante.");
      return;
    }
    if (idsMarcados.length === 0) {
      onErro?.("Marque pelo menos um diagnóstico na grelha.");
      return;
    }
    setRegSalvando(true);
    try {
      const memo = regMemo.trim();
      for (const diagId of idsMarcados) {
        await postRegistrarSolicitacaoLgpd({
          tipo: regTipo,
          solicitante_email: email,
          diagnostico_id: diagId,
          payload: {
            origem: "painel_privacidade",
            ...(memo ? { memo_atendimento: memo } : {}),
          },
        });
      }
      const n = idsMarcados.length;
      onMensagem?.(
        n === 1 ? "Solicitação registrada." : `${n} solicitações registradas.`,
      );
      setRegMemo("");
      limparMarcados();
      onRegistrado?.();
    } catch (e) {
      onErro?.(e instanceof Error ? e.message : "Falha ao registrar.");
    } finally {
      setRegSalvando(false);
    }
  };

  const podeRegistrar = idsMarcados.length > 0 && regEmail.trim().length > 0 && !regSalvando;

  return (
    <Card className="mb-10" id="priv-lgpd-registrar">
      <CardHeader>
        <CardTitle className="text-lg">Nova solicitação</CardTitle>
        <CardDescription>
          Localize a empresa, marque um ou mais diagnósticos e registre o pedido do titular (art. 18).
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        <div className="space-y-2">
          <Label htmlFor="priv-busca-empresa">Empresa (consulta)</Label>
          <div className="relative">
            <Input
              id="priv-busca-empresa"
              ref={buscaRef}
              placeholder="CNPJ ou razão social (mín. 2 letras ou 3 dígitos)"
              autoComplete="off"
              aria-autocomplete="list"
              aria-expanded={listaAberta && sugestoes.length > 0}
              disabled={indiceCarregando}
              value={buscaEmpresa}
              onChange={(e) => {
                setBuscaEmpresa(e.target.value);
                setListaAberta(true);
                if (empresaSel) {
                  setEmpresaSel(null);
                  onEmpresaSelecionada?.(null);
                  setDiagnosticos([]);
                  setMarcados(new Set());
                }
              }}
              onFocus={() => setListaAberta(true)}
              onBlur={() => {
                window.setTimeout(() => setListaAberta(false), 200);
              }}
            />
            {listaAberta && sugestoes.length > 0 ? (
              <ul
                role="listbox"
                className="absolute z-30 mt-1 max-h-56 w-full overflow-auto rounded-md border bg-popover py-1 text-sm shadow-md"
              >
                {sugestoes.map((e) => (
                  <li key={e.cnpj14} role="option">
                    <button
                      type="button"
                      className="w-full px-3 py-2 text-left hover:bg-muted/60"
                      onMouseDown={(ev) => ev.preventDefault()}
                      onClick={() => void selecionarEmpresa(e)}
                    >
                      <span className="font-medium">{e.razao_social}</span>
                      <span className="block text-xs text-muted-foreground">
                        CNPJ {mascaraCnpj14(e.cnpj14)}
                      </span>
                    </button>
                  </li>
                ))}
              </ul>
            ) : null}
          </div>
          {indiceCarregando ? (
            <p className="text-xs text-muted-foreground">Carregando empresas do tenant…</p>
          ) : null}
          {empresaSel ? (
            <div className="flex flex-wrap items-center gap-2 text-sm">
              <span className="text-muted-foreground">Selecionada:</span>
              <span className="font-medium">{empresaSel.razao_social}</span>
              <Badge variant="outline">CNPJ {mascaraCnpj14(empresaSel.cnpj14)}</Badge>
              <Button type="button" variant="ghost" size="sm" className="h-7 text-xs" onClick={limparEmpresa}>
                Trocar empresa
              </Button>
              <Link
                href={`/dashboard/empresas/${empresaSel.cnpj14}`}
                className="text-primary underline text-xs"
              >
                Vista empresa
              </Link>
            </div>
          ) : null}
        </div>

        {empresaSel ? (
          <>
            <div className="space-y-3">
              <div className="flex flex-wrap items-center justify-between gap-2">
                <Label className="text-sm font-medium">Diagnósticos desta empresa</Label>
                <div className="flex gap-2">
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    disabled={diagCarregando || diagnosticos.length === 0}
                    onClick={marcarTodos}
                  >
                    Marcar todos
                  </Button>
                  <Button
                    type="button"
                    variant="outline"
                    size="sm"
                    disabled={marcados.size === 0}
                    onClick={limparMarcados}
                  >
                    Limpar
                  </Button>
                </div>
              </div>
              {diagErro ? (
                <p className="text-sm text-destructive" role="alert">
                  {diagErro}
                </p>
              ) : null}
              {diagCarregando ? (
                <p className="text-sm text-muted-foreground">Carregando diagnósticos…</p>
              ) : diagnosticos.length === 0 ? (
                <p className="text-sm text-muted-foreground">Nenhum diagnóstico para este CNPJ.</p>
              ) : (
                <div className="overflow-x-auto rounded-md border">
                  <table className="w-full text-sm">
                    <thead>
                      <tr className="border-b bg-muted/40 text-left">
                        <th className="p-3 w-10" scope="col">
                          <span className="sr-only">Marcar</span>
                        </th>
                        <th className="p-3 font-medium">Ciclo</th>
                        <th className="p-3 font-medium">Finalizado</th>
                        <th className="p-3 font-medium">Status</th>
                        <th className="p-3 font-medium">Score</th>
                        <th className="p-3 font-medium">Plano</th>
                        <th className="p-3 font-medium">Ficha</th>
                      </tr>
                    </thead>
                    <tbody>
                      {diagnosticos.map((d) => {
                        const checked = marcados.has(d.id);
                        return (
                          <tr
                            key={d.id}
                            className={cn(
                              "border-b border-muted last:border-0",
                              checked && "bg-primary/5",
                            )}
                          >
                            <td className="p-3 align-middle">
                              <input
                                type="checkbox"
                                checked={checked}
                                aria-label={`Marcar diagnóstico ciclo ${d.numero_interno_grupo ?? "—"}`}
                                onChange={() => toggleMarcado(d.id)}
                                className="h-4 w-4 rounded border-input"
                              />
                            </td>
                            <td className="p-3">{d.numero_interno_grupo ?? "—"}</td>
                            <td className="p-3">{formatarData(d.finalizado_em)}</td>
                            <td className="p-3">
                              <Badge variant="secondary">{d.status}</Badge>
                            </td>
                            <td className="p-3">
                              {d.score_geral != null ? Math.round(d.score_geral) : "—"}
                            </td>
                            <td className="p-3 capitalize">{d.plano}</td>
                            <td className="p-3">
                              <Link
                                href={`/dashboard/diagnosticos/${d.id}`}
                                className="text-primary underline text-xs"
                              >
                                Abrir
                              </Link>
                            </td>
                          </tr>
                        );
                      })}
                    </tbody>
                  </table>
                </div>
              )}
              {idsMarcados.length > 0 ? (
                <p className="text-xs text-muted-foreground">
                  {idsMarcados.length} diagnóstico(s) marcado(s) para registro.
                </p>
              ) : null}
            </div>

            <div className="rounded-lg border bg-muted/15 p-4 space-y-4">
              <p className="text-sm font-medium">Dados do pedido</p>
              <div className="grid gap-4 sm:grid-cols-2">
                <div className="space-y-2">
                  <Label htmlFor="lgpd-tipo">Tipo</Label>
                  <Select value={regTipo} onValueChange={(v: string | null) => setRegTipo(v ?? "")}>
                    <SelectTrigger id="lgpd-tipo">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {Object.entries(ROTULO_TIPO).map(([k, v]) => (
                        <SelectItem key={k} value={k}>
                          {v}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2">
                  <Label htmlFor="lgpd-email">E-mail do solicitante</Label>
                  <Input
                    id="lgpd-email"
                    type="email"
                    autoComplete="email"
                    placeholder="titular@empresa.com"
                    value={regEmail}
                    onChange={(e) => setRegEmail(e.target.value)}
                  />
                </div>
              </div>
              <div className="space-y-2">
                <Label htmlFor="lgpd-memo">Descrição / memo (atendimento)</Label>
                <textarea
                  id="lgpd-memo"
                  rows={4}
                  className="w-full min-h-[5rem] rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                  placeholder="Ex.: pedido recebido por e-mail; titular solicita anonimização do respondente."
                  value={regMemo}
                  onChange={(e) => setRegMemo(e.target.value)}
                />
              </div>
              <div className="flex flex-wrap items-center gap-3">
                <Button type="button" disabled={!podeRegistrar} onClick={() => void registrar()}>
                  {regSalvando
                    ? "Registrando…"
                    : idsMarcados.length > 1
                      ? `Registrar ${idsMarcados.length} solicitações`
                      : "Registrar solicitação"}
                </Button>
                {!podeRegistrar && idsMarcados.length === 0 ? (
                  <span className="text-xs text-muted-foreground">Marque ao menos um diagnóstico.</span>
                ) : null}
              </div>
            </div>
          </>
        ) : null}
      </CardContent>
    </Card>
  );
}
