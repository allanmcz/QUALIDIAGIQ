"use client";

import { useCallback, useEffect, useState } from "react";
import { Loader2, Sparkles } from "lucide-react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { postExplicacaoScoreLlm, type ExplicacaoScoreLlmHttp } from "@/lib/api/explicacao_score_llm";

type Props = {
  diagnosticoId: string;
  diagnosticoStatus: string;
  /** Score geral 0–100 já persistido (GET); null = botão desativado. */
  scoreGeral: number | null;
  /** Snapshot da BD (GET) — hidratação sem novo POST. */
  inicial?: ExplicacaoScoreLlmHttp | null;
  className?: string;
};

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
  scoreGeral,
  inicial = null,
  className,
}: Props) {
  const [carregando, setCarregando] = useState(false);
  const [erro, setErro] = useState<string | null>(null);
  const [resposta, setResposta] = useState<ExplicacaoScoreLlmHttp | null>(inicial);

  useEffect(() => {
    setResposta(inicial);
  }, [inicial]);

  const podeGerar =
    diagnosticoStatus === "finalizado" && scoreGeral != null && Number.isFinite(scoreGeral);

  const gerar = useCallback(async () => {
    if (!podeGerar) return;
    setCarregando(true);
    setErro(null);
    try {
      const out = await postExplicacaoScoreLlm(diagnosticoId);
      setResposta(out);
    } catch (e) {
      setErro(e instanceof Error ? e.message : "Falha ao gerar explicação.");
    } finally {
      setCarregando(false);
    }
  }, [diagnosticoId, podeGerar]);

  const textoExibido =
    resposta?.blocked_by_guardrail && resposta.guardrail_reason
      ? resposta.guardrail_reason
      : resposta?.text ?? "";

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

        {!podeGerar ? (
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

        {resposta ? (
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
      </CardContent>
    </Card>
  );
}
