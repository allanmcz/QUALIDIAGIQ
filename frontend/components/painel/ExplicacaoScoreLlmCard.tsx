"use client";

import {
  forwardRef,
  useCallback,
  useEffect,
  useImperativeHandle,
  useMemo,
  useState,
} from "react";
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
  explicacaoScoreTemParecerExibivel,
  historicoAnterioresAExibicao,
  textoExibicaoExplicacao,
} from "@/lib/api/explicacao_score_llm_historico";

/** API imperativa para o atalho «Explicação IA» na barra da ficha (scroll + POST). */
export type ExplicacaoScoreLlmCardHandle = {
  scrollParaSecao: () => void;
  solicitarGeracao: () => void;
};

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
export const ExplicacaoScoreLlmCard = forwardRef<ExplicacaoScoreLlmCardHandle, Props>(
  function ExplicacaoScoreLlmCard(
    {
      diagnosticoId,
      diagnosticoStatus,
      planoDiagnostico = null,
      scoreGeral,
      inicial = null,
      className,
    },
    ref,
  ) {
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
      if (!explicacaoScoreTemParecerExibivel(out)) {
        setResposta(null);
        setErro(textoExibicaoExplicacao(out));
        return;
      }
      setResposta(out);
      void carregarHistorico();
    } catch (e) {
      setErro(e instanceof Error ? e.message : "Falha ao gerar explicação.");
    } finally {
      setCarregando(false);
    }
  }, [carregarHistorico, diagnosticoId, podeGerar]);

  const scrollParaSecao = useCallback(() => {
    if (typeof document === "undefined") return;
    document.getElementById("diag-explicacao-score-llm")?.scrollIntoView({
      behavior: "smooth",
      block: "start",
    });
  }, []);

  useImperativeHandle(
    ref,
    () => ({
      scrollParaSecao,
      solicitarGeracao: () => {
        void gerar();
      },
    }),
    [gerar, scrollParaSecao],
  );

  const anteriores = useMemo(
    () => historicoAnterioresAExibicao(historico, resposta),
    [historico, resposta],
  );

  const parecerOk = resposta ? explicacaoScoreTemParecerExibivel(resposta) : false;
  const textoExibido = resposta && parecerOk ? textoExibicaoExplicacao(resposta) : "";
  const fontesRag = (resposta?.fontes_rag ?? []).filter((f) => (f.trecho || "").trim().length > 0);
  const ragStatus = (resposta?.rag_status || "").trim();

  const rotuloGerado = formatarGeradoEmPtBr(resposta?.gerado_em);

  return (
    <Card id="diag-explicacao-score-llm" className={className ?? "mb-10 scroll-mt-24"}>
      <CardHeader>
        <CardTitle className="text-lg flex items-center gap-2">
          <Sparkles className="h-5 w-5 shrink-0 text-primary" aria-hidden />
          Explicação do score (IA)
        </CardTitle>
        <CardDescription>
          O modelo lê o diagnóstico finalizado (scores por dimensão, porte, regime) e redige um
          parecer consultivo em português — não recalcula o 0–100. Com guardrails Lexiq (ADR-022).
          Não substitui a recomendação gerada na finalização do diagnóstico.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
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
          <div className="space-y-2">
            <Button
              type="button"
              variant="default"
              size="sm"
              disabled={carregando}
              onClick={() => void gerar()}
              className="gap-2"
              aria-busy={carregando}
            >
              {carregando ? (
                <Loader2 className="h-4 w-4 animate-spin shrink-0" aria-hidden />
              ) : (
                <Sparkles className="h-4 w-4 shrink-0" aria-hidden />
              )}
              {resposta ? "Gerar novamente" : "Gerar explicação"}
            </Button>
            {carregando ? (
              <p className="text-sm text-muted-foreground" role="status">
                A gerar narrativa com IA — pode levar até 2 minutos na primeira vez (Ollama).
              </p>
            ) : null}
          </div>
        )}

        {erro ? (
          <p
            className="text-sm text-destructive rounded-md border border-destructive/30 bg-destructive/5 px-3 py-2"
            role="alert"
          >
            {erro}
          </p>
        ) : null}

        {podeAcessar && resposta && parecerOk ? (
          <div className="space-y-3 rounded-lg border bg-muted/20 p-4">
            <Badge variant="secondary">Parecer gerado</Badge>
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
            {ragStatus === "base_insuficiente" ? (
              <p className="text-xs text-amber-700 dark:text-amber-400" role="status">
                Base normativa recuperada com baixa confiança — o parecer pode omitir detalhes
                legislativos; consulte as fontes abaixo quando disponíveis.
              </p>
            ) : null}
            {fontesRag.length > 0 ? (
              <details className="rounded-md border bg-background/60 px-3 py-2 text-sm">
                <summary className="cursor-pointer font-medium text-muted-foreground select-none">
                  Fontes consultadas ({fontesRag.length})
                </summary>
                <ul className="mt-2 space-y-2 border-t pt-2" aria-label="Trechos RAG citáveis">
                  {fontesRag.map((fonte, idx) => (
                    <li key={`${fonte.fonte}-${idx}`} className="text-xs leading-relaxed">
                      <span className="font-medium text-foreground">
                        {fonte.fonte}
                        {fonte.dispositivo ? ` · ${fonte.dispositivo}` : ""}
                        {typeof fonte.score === "number" && fonte.score > 0
                          ? ` · relevância ${(fonte.score * 100).toFixed(0)}%`
                          : ""}
                      </span>
                      <p className="mt-1 text-muted-foreground whitespace-pre-wrap">{fonte.trecho}</p>
                    </li>
                  ))}
                </ul>
              </details>
            ) : null}
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
                        {(item.fontes_rag ?? []).length > 0 ? (
                          <p className="text-xs text-muted-foreground">
                            Fontes:{" "}
                            {(item.fontes_rag ?? [])
                              .map((f) => f.fonte)
                              .filter(Boolean)
                              .join(", ")}
                          </p>
                        ) : null}
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
  },
);

ExplicacaoScoreLlmCard.displayName = "ExplicacaoScoreLlmCard";
