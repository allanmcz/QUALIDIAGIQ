"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { Loader2, Sparkles } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { ADMIN_PERFIL_CONTA_STORAGE_KEY } from "@/lib/api/config";
import {
  getExplicacaoScoreLlmHistorico,
  postExplicacaoScoreLlm,
  type ExplicacaoScoreLlmHttp,
} from "@/lib/api/explicacao_score_llm";
import {
  historicoAnterioresAExibicao,
  textoExibicaoExplicacao,
} from "@/lib/api/explicacao_score_llm_historico";

type Props = {
  diagnosticoId: string;
  diagnosticoStatus: string;
  /** Plano persistido do diagnóstico (`avancado` desbloqueia sem perfil avançado). */
  planoDiagnostico?: string | null;
  /** Score geral 0–100 já persistido (GET); null = botão desativado. */
  scoreGeral: number | null;
  /** Snapshot da BD (GET) — hidratação sem novo POST. */
  inicial?: ExplicacaoScoreLlmHttp | null;
  className?: string;
};

function sessaoPodeExplicacaoScore(perfilConta: string | null, plano: string | null): boolean {
  const p = (perfilConta || "").trim().toLowerCase();
  if (p === "avancado" || p === "admin") return true;
  return (plano || "").trim().toLowerCase() === "avancado";
}

function formatarGeradoEmPtBr(iso: string | null | undefined): string | null {
  const s = (iso || "").trim();
  if (!s) return null;
  const d = new Date(s);
  if (Number.isNaN(d.getTime())) return s;
  return d.toLocaleString("pt-BR", { dateStyle: "short", timeStyle: "short" });
}

/**
 * Bloco painel — explicação IA do score via gateway governado (ADR-022).
 * Não substitui o motor determinístico; apenas narrativa sobre o valor já calculado.
 */
export function ExplicacaoScoreLlmCard({
  diagnosticoId,
  diagnosticoStatus,
  planoDiagnostico = null,
  scoreGeral,
  inicial = null,
  className,
}: Props) {
  const [carregando, setCarregando] = useState(false);
  const [erro, setErro] = useState<string | null>(null);
  const [resposta, setResposta] = useState<ExplicacaoScoreLlmHttp | null>(inicial);
  const [historico, setHistorico] = useState<ExplicacaoScoreLlmHttp[]>([]);
  const [historicoCarregando, setHistoricoCarregando] = useState(false);
  const [historicoErro, setHistoricoErro] = useState<string | null>(null);
  const [perfilConta, setPerfilConta] = useState<string | null>(null);

  useEffect(() => {
    setResposta(inicial);
  }, [inicial]);

  useEffect(() => {
    if (typeof window === "undefined") return;
    setPerfilConta(window.localStorage.getItem(ADMIN_PERFIL_CONTA_STORAGE_KEY));
  }, []);

  const podeAcessar = sessaoPodeExplicacaoScore(perfilConta, planoDiagnostico);
  const podeGerar =
    podeAcessar &&
    diagnosticoStatus === "finalizado" &&
    scoreGeral != null &&
    Number.isFinite(scoreGeral);

  const carregarHistorico = useCallback(async () => {
    if (!podeAcessar) return;
    setHistoricoCarregando(true);
    setHistoricoErro(null);
    try {
      const items = await getExplicacaoScoreLlmHistorico(diagnosticoId);
      setHistorico(items);
    } catch (e) {
      setHistorico([]);
      setHistoricoErro(e instanceof Error ? e.message : "Falha ao carregar histórico.");
    } finally {
      setHistoricoCarregando(false);
    }
  }, [diagnosticoId, podeAcessar]);

  useEffect(() => {
    void carregarHistorico();
  }, [carregarHistorico]);

  const gerar = useCallback(async () => {
    if (!podeGerar) return;
    setCarregando(true);
    setErro(null);
    try {
      const out = await postExplicacaoScoreLlm(diagnosticoId);
      setResposta(out);
      await carregarHistorico();
    } catch (e) {
      setErro(e instanceof Error ? e.message : "Falha ao gerar explicação.");
    } finally {
      setCarregando(false);
    }
  }, [carregarHistorico, diagnosticoId, podeGerar]);

  const anteriores = useMemo(
    () => historicoAnterioresAExibicao(historico, resposta),
    [historico, resposta],
  );

  const textoExibido = resposta ? textoExibicaoExplicacao(resposta) : "";

  const rotuloGerado = formatarGeradoEmPtBr(resposta?.gerado_em);

  return (
    <Card id="diag-explicacao-score-llm" className={className ?? "mb-10 scroll-mt-24"}>
      <CardHeader>
        <CardTitle className="text-lg flex items-center gap-2">
          <Sparkles className="h-5 w-5 shrink-0 text-primary" aria-hidden />
          Explicação do score (IA)
        </CardTitle>
        <CardDescription>
          Narrativa sobre o score geral já calculado pelo motor auditável (0–100). Com guardrails e
          política de roteamento LLM (ADR-022); não altera o valor numérico. Não substitui a
          recomendação gerada na finalização do diagnóstico.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {erro ? (
          <p className="text-sm text-destructive" role="alert">
            {erro}
          </p>
        ) : null}

        {!podeAcessar ? (
          <p className="text-sm text-muted-foreground">
            Explicação do score por IA está disponível no <strong>plano avançado</strong> da conta na
            plataforma ou em diagnósticos com plano avançado. Faça upgrade para desbloquear.
          </p>
        ) : !podeGerar ? (
          <p className="text-sm text-muted-foreground">
            Disponível quando o diagnóstico está <strong>finalizado</strong> com score persistido.
          </p>
        ) : (
          <Button
            type="button"
            variant="default"
            size="sm"
            disabled={carregando}
            onClick={() => void gerar()}
            className="gap-2"
          >
            {carregando ? (
              <Loader2 className="h-4 w-4 animate-spin shrink-0" aria-hidden />
            ) : (
              <Sparkles className="h-4 w-4 shrink-0" aria-hidden />
            )}
            {resposta ? "Gerar novamente" : "Gerar explicação"}
          </Button>
        )}

        {podeAcessar && resposta ? (
          <div className="space-y-3 rounded-lg border bg-muted/20 p-4">
            {resposta.blocked_by_guardrail ? (
              <Badge variant="destructive">Bloqueado por guardrail</Badge>
            ) : (
              <Badge variant="secondary">Resposta gerada</Badge>
            )}
            {rotuloGerado ? (
              <p className="text-xs text-muted-foreground">Última geração: {rotuloGerado}</p>
            ) : null}
            <div
              className="text-sm leading-relaxed whitespace-pre-wrap text-foreground"
              role="region"
              aria-label="Texto da explicação do score"
            >
              {textoExibido || "—"}
            </div>
            <p className="text-xs text-muted-foreground">
              {resposta.provider} · {resposta.model} · política {resposta.policy_version}
              {resposta.latency_ms > 0 ? ` · ${resposta.latency_ms} ms` : ""}
              {resposta.output_tokens > 0 ? ` · ${resposta.output_tokens} tokens saída` : ""}
            </p>
          </div>
        ) : null}

        {podeAcessar ? (
          <div className="space-y-2">
            {historicoCarregando ? (
              <p className="text-xs text-muted-foreground flex items-center gap-2">
                <Loader2 className="h-3 w-3 animate-spin shrink-0" aria-hidden />
                Carregando histórico…
              </p>
            ) : null}
            {historicoErro ? (
              <p className="text-xs text-destructive" role="alert">
                {historicoErro}
              </p>
            ) : null}
            {!historicoCarregando && anteriores.length > 0 ? (
              <details className="rounded-md border bg-muted/30 px-3 py-2 text-sm group">
                <summary className="cursor-pointer font-medium text-muted-foreground list-none flex items-center gap-2 select-none [&::-webkit-details-marker]:hidden">
                  Gerações anteriores ({anteriores.length})
                </summary>
                <ul
                  className="mt-3 space-y-3 border-t pt-3"
                  aria-label="Histórico de explicações do score"
                >
                  {anteriores.map((item, idx) => {
                    const quando = formatarGeradoEmPtBr(item.gerado_em);
                    const key = `${item.gerado_em ?? "sem-data"}-${idx}`;
                    return (
                      <li key={key} className="rounded-md border bg-background/80 p-3 space-y-2">
                        <div className="flex flex-wrap items-center gap-2">
                          {item.blocked_by_guardrail ? (
                            <Badge variant="destructive" className="text-xs">
                              Guardrail
                            </Badge>
                          ) : (
                            <Badge variant="outline" className="text-xs">
                              Geração
                            </Badge>
                          )}
                          {quando ? (
                            <span className="text-xs text-muted-foreground">{quando}</span>
                          ) : null}
                        </div>
                        <p className="text-sm leading-relaxed whitespace-pre-wrap text-foreground">
                          {textoExibicaoExplicacao(item)}
                        </p>
                        <p className="text-xs text-muted-foreground">
                          {item.provider} · {item.model}
                        </p>
                      </li>
                    );
                  })}
                </ul>
              </details>
            ) : null}
          </div>
        ) : null}
      </CardContent>
    </Card>
  );
}
