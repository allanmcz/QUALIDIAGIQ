"use client";

import { useCallback, useEffect, useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import {
  fetchRetificacoesDiagnostico,
  postRetificacaoDiagnostico,
  type DiagnosticoRetificacaoHttp,
} from "@/lib/api/diagnostico_retificacao";

type Props = {
  diagnosticoId: string;
  diagnosticoStatus: string;
};

const MIN_MOTIVO = 10;

/**
 * Cadeia append-only de retificações (ADR-012 §5) — não altera o diagnóstico WORM original.
 */
export function RetificacaoDiagnosticoCard({ diagnosticoId, diagnosticoStatus }: Props) {
  const [linhas, setLinhas] = useState<DiagnosticoRetificacaoHttp[]>([]);
  const [carregando, setCarregando] = useState(true);
  const [erro, setErro] = useState<string | null>(null);
  const [mensagem, setMensagem] = useState<string | null>(null);
  const [motivo, setMotivo] = useState("");
  const [gravando, setGravando] = useState(false);

  const podeRegistar = diagnosticoStatus === "finalizado";

  const recarregar = useCallback(async () => {
    setCarregando(true);
    setErro(null);
    try {
      const lista = await fetchRetificacoesDiagnostico(diagnosticoId, { limit: 50 });
      setLinhas(lista);
    } catch (e) {
      setErro(e instanceof Error ? e.message : "Falha ao carregar retificações.");
      setLinhas([]);
    } finally {
      setCarregando(false);
    }
  }, [diagnosticoId]);

  useEffect(() => {
    void recarregar();
  }, [recarregar]);

  const registar = async () => {
    const m = motivo.trim();
    if (m.length < MIN_MOTIVO) {
      setErro(`Motivo deve ter pelo menos ${MIN_MOTIVO} caracteres.`);
      return;
    }
    setGravando(true);
    setErro(null);
    setMensagem(null);
    try {
      await postRetificacaoDiagnostico(diagnosticoId, {
        motivo_retificacao: m,
        payload_retificacao: {},
      });
      setMotivo("");
      setMensagem("Retificação registada na cadeia (append-only).");
      await recarregar();
    } catch (e) {
      setErro(e instanceof Error ? e.message : "Falha ao registar retificação.");
    } finally {
      setGravando(false);
    }
  };

  return (
    <Card className="mb-10">
      <CardHeader>
        <CardTitle className="text-lg">Retificações (compliance / LGPD)</CardTitle>
        <CardDescription>
          Modelo tipo CC-e (ADR-012 §5): nova linha com hash do original — sem alterar o diagnóstico
          finalizado na tabela principal. Exige evidência WORM (hash) no servidor.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-6">
        {erro ? (
          <p className="text-sm text-destructive" role="alert">
            {erro}
          </p>
        ) : null}
        {mensagem ? (
          <p className="text-sm text-muted-foreground" role="status">
            {mensagem}
          </p>
        ) : null}

        <div className="rounded-lg border bg-muted/15 p-4 space-y-3">
          <Label htmlFor="retif-motivo" className="text-sm font-medium">
            Novo motivo de retificação
          </Label>
          <textarea
            id="retif-motivo"
            rows={4}
            className="w-full min-h-[5rem] rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
            placeholder={`Texto obrigatório (mín. ${MIN_MOTIVO} caracteres) — ex.: correção documental após parecer interno.`}
            value={motivo}
            disabled={!podeRegistar || gravando}
            onChange={(e) => setMotivo(e.target.value)}
          />
          {!podeRegistar ? (
            <p className="text-xs text-amber-800">
              Só é possível registar retificação quando o diagnóstico está <strong>finalizado</strong> com hash de
              evidência.
            </p>
          ) : null}
          <Button type="button" disabled={!podeRegistar || gravando} onClick={() => void registar()}>
            {gravando ? "A gravar…" : "Registar retificação"}
          </Button>
        </div>

        <div>
          <h3 className="text-sm font-semibold mb-2">Cadeia registada</h3>
          {carregando ? (
            <p className="text-sm text-muted-foreground">A carregar…</p>
          ) : linhas.length === 0 ? (
            <p className="text-sm text-muted-foreground">Nenhuma retificação neste diagnóstico.</p>
          ) : (
            <ul className="space-y-3 list-none p-0 m-0">
              {linhas.map((r) => (
                <li
                  key={r.id}
                  className="rounded-lg border px-3 py-2 text-sm space-y-1 bg-muted/10"
                >
                  <div className="flex flex-wrap gap-2 items-center">
                    <Badge variant="outline" className="font-mono text-[10px]">
                      {(r.criado_em ?? "").slice(0, 19).replace("T", " ") || "—"} UTC
                    </Badge>
                    <span className="text-xs text-muted-foreground font-mono break-all">
                      hash: {r.hash_retificacao_sha256.slice(0, 16)}…
                    </span>
                  </div>
                  <p className="text-foreground whitespace-pre-wrap">{r.motivo_retificacao}</p>
                </li>
              ))}
            </ul>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
