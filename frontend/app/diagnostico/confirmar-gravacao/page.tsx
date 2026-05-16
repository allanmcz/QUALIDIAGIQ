"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useCallback, useEffect, useState } from "react";
import { CheckCircle2 } from "lucide-react";

import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardFooter,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  getRascunhoDiagnosticoSelfServiceResumo,
  postConcluirRascunhoDiagnosticoSelfService,
  postRascunhoDiagnosticoSelfService,
  postSolicitarCodigoEmail,
} from "@/lib/api/self_service_diagnostico";
import {
  clearPendingDiagnosticoFromStorage,
  loadPendingDiagnosticoFromStorage,
} from "@/lib/wizard/pending_diagnostico";
import {
  saveRascunhoResgateTokenParaLogin,
  clearRascunhoResgateToken,
  loadRascunhoResgateToken,
} from "@/lib/wizard/rascunho_resgate_token";
import { scoresPorDimensaoFromApiScore, type ScorePorDimensaoItem } from "@/lib/wizard/self_service_result";
import { clearWizardDraft } from "@/lib/wizard/wizard_draft";

function extrairValorScoreGeral(score: unknown): number | null {
  if (!score || typeof score !== "object") return null;
  const sg = (score as Record<string, unknown>)["score_geral"];
  if (!sg || typeof sg !== "object") return null;
  const v = (sg as Record<string, unknown>)["valor"];
  if (typeof v === "number" && Number.isFinite(v)) return v;
  if (typeof v === "string") {
    const n = Number(v.trim());
    return Number.isFinite(n) ? n : null;
  }
  return null;
}

function respostaApiParaResultado(data: unknown): {
  id: string;
  status: string;
  empresa_razao_social: string;
  locale_relatorio: string;
  score_geral: number | null;
  scores_por_dimensao: ScorePorDimensaoItem[];
} | null {
  if (!data || typeof data !== "object") return null;
  const o = data as Record<string, unknown>;
  const idRaw = o["id"];
  const id =
    typeof idRaw === "string"
      ? idRaw
      : typeof idRaw === "number" && Number.isFinite(idRaw)
        ? String(idRaw)
        : null;
  const status = o["status"];
  const empresa_razao_social = o["empresa_razao_social"];
  const locale_relatorio = o["locale_relatorio"];
  if (id === null || typeof status !== "string") return null;
  if (typeof empresa_razao_social !== "string") return null;
  const loc = typeof locale_relatorio === "string" ? locale_relatorio : "pt-BR";
  const scoreRaw = o["score"];
  const score_geral = extrairValorScoreGeral(scoreRaw);
  const scores_por_dimensao = scoresPorDimensaoFromApiScore(scoreRaw);
  return { id, status, empresa_razao_social, locale_relatorio: loc, score_geral, scores_por_dimensao };
}

export default function DiagnosticoConfirmarGravacaoPage() {
  const router = useRouter();
  const [resgateToken, setResgateToken] = useState<string | null>(null);
  const [resumo, setResumo] = useState<{
    empresa_razao_social: string;
    empresa_cnpj: string;
    email_mascarado: string;
    respondente_email: string;
    expira_em: string;
  } | null>(null);
  const [initErro, setInitErro] = useState<string | null>(null);
  const [codigoOtp, setCodigoOtp] = useState("");
  const [codigoEnviadoMsg, setCodigoEnviadoMsg] = useState<string | null>(null);
  const [enviandoCodigo, setEnviandoCodigo] = useState(false);
  const [gravando, setGravando] = useState(false);
  const [fluxoErro, setFluxoErro] = useState<string | null>(null);

  const carregarResumo = useCallback(async (token: string) => {
    const r = await getRascunhoDiagnosticoSelfServiceResumo(token);
    setResumo(r);
    setCodigoEnviadoMsg(
      "Um código foi enviado ao e-mail informado. Você pode reenviar abaixo se necessário.",
    );
  }, []);

  useEffect(() => {
    let cancelado = false;
    void (async () => {
      setInitErro(null);
      const fromStore = (loadRascunhoResgateToken() ?? "").trim();
      const rawHash =
        typeof window !== "undefined" ? window.location.hash.replace(/^#/, "").trim() : "";
      const fromHash = rawHash ? decodeURIComponent(rawHash).trim() : "";
      let token = fromHash || fromStore;
      if (!token) {
        const legacy = loadPendingDiagnosticoFromStorage();
        if (legacy) {
          try {
            const criado = await postRascunhoDiagnosticoSelfService(legacy);
            clearPendingDiagnosticoFromStorage();
            token = criado.resgate_token.trim();
            if (typeof window !== "undefined") {
              window.history.replaceState(null, "", `${window.location.pathname}#${encodeURIComponent(token)}`);
            }
          } catch (e) {
            if (!cancelado) {
              setInitErro(e instanceof Error ? e.message : "Não foi possível preparar seus dados para confirmação.");
            }
            return;
          }
        }
      }
      if (!token) {
        if (!cancelado) router.replace("/wizard");
        return;
      }
      if (fromStore) {
        clearRascunhoResgateToken();
      }
      if (!cancelado) {
        setResgateToken(token);
      }
      try {
        await carregarResumo(token);
      } catch (e) {
        if (!cancelado) {
          setInitErro(e instanceof Error ? e.message : "Rascunho inválido ou expirado.");
        }
      }
    })();
    return () => {
      cancelado = true;
    };
    // carregarResumo é estável (useCallback); omitir das deps evita re-fetch desnecessário.
    // eslint-disable-next-line react-hooks/exhaustive-deps -- intencional: montagem + redirect
  }, [router]);

  const loginHref = "/login?redirect=/wizard";

  async function aoEnviarCodigo() {
    const email = resumo?.respondente_email?.trim();
    if (!email) return;
    setFluxoErro(null);
    setEnviandoCodigo(true);
    setCodigoEnviadoMsg(null);
    try {
      const r = await postSolicitarCodigoEmail(email);
      setCodigoEnviadoMsg(r.mensagem);
    } catch (e) {
      setFluxoErro(e instanceof Error ? e.message : "Falha ao solicitar código.");
    } finally {
      setEnviandoCodigo(false);
    }
  }

  async function aoConfirmarEGravar() {
    if (!resgateToken) return;
    const limpo = codigoOtp.trim().replace(/\s+/g, "");
    if (limpo.length < 4) {
      setFluxoErro("Informe o código recebido por e-mail (mínimo 4 dígitos).");
      return;
    }
    setFluxoErro(null);
    setGravando(true);
    try {
      const raw = await postConcluirRascunhoDiagnosticoSelfService(resgateToken, limpo);
      const parsed = respostaApiParaResultado(raw);
      const leitura =
        raw !== null && typeof raw === "object" && "leitura_token" in raw
          ? String((raw as Record<string, unknown>)["leitura_token"] ?? "").trim()
          : "";
      if (!parsed || !leitura) {
        throw new Error(
          "Não foi possível abrir a visualização do resultado agora. Tente novamente em instantes ou acione o suporte.",
        );
      }
      clearWizardDraft();
      const q = new URLSearchParams();
      q.set("diagnostico_id", parsed.id);
      q.set("leitura_token", leitura);
      router.push(`/diagnostico/concluido-self-service?${q.toString()}`);
    } catch (e) {
      const msg = e instanceof Error ? e.message : "Falha ao gravar.";
      setFluxoErro(
        `${msg} Se o código já foi usado, solicite um novo e tente de novo.`,
      );
    } finally {
      setGravando(false);
    }
  }

  function aoIrLogin() {
    if (resgateToken) {
      saveRascunhoResgateTokenParaLogin(resgateToken);
    }
    router.push(loginHref);
  }

  if (initErro) {
    return (
      <div className="container max-w-lg py-16 space-y-4 text-center">
        <p className="text-sm text-destructive" role="alert">
          {initErro}
        </p>
        <Button asChild variant="outline">
          <Link href="/wizard">Voltar ao assistente</Link>
        </Button>
      </div>
    );
  }

  if (!resumo || !resgateToken) {
    return (
      <div className="container max-w-lg py-16 text-center text-sm text-muted-foreground">
        Carregando…
      </div>
    );
  }

  return (
    <div className="container max-w-xl py-10 px-4 space-y-8">
      <div className="flex justify-center">
        <div className="flex h-16 w-16 items-center justify-center rounded-full bg-accent/15 text-accent">
          <CheckCircle2 className="h-8 w-8" aria-hidden />
        </div>
      </div>

      <div className="text-center space-y-2">
        <h1 className="text-2xl font-bold tracking-tight md:text-3xl">Confirme seu e-mail para finalizar</h1>
        <p className="text-muted-foreground text-sm leading-relaxed max-w-md mx-auto">
          Suas respostas foram recebidas e aguardam confirmação do e-mail. Introduza o código
          enviado para <strong className="text-foreground">{resumo.email_mascarado}</strong> para concluir a gravação
          do diagnóstico.
        </p>
      </div>

      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-lg">Resumo</CardTitle>
          <CardDescription>Diagnóstico aguardando confirmação</CardDescription>
        </CardHeader>
        <CardContent className="space-y-3 text-sm">
          <div className="rounded-lg border bg-muted/30 px-4 py-3 space-y-1">
            <p className="font-medium text-foreground">{resumo.empresa_razao_social}</p>
            <p className="text-muted-foreground text-xs tabular-nums">
              Validade do rascunho: {new Date(resumo.expira_em).toLocaleString("pt-BR")}
            </p>
          </div>

          <div className="rounded-lg border border-dashed bg-muted/20 px-4 py-4 space-y-4">
            <p className="font-medium text-foreground text-sm">Confirmar e-mail (código)</p>
            <p className="text-xs text-muted-foreground leading-relaxed">
              Anti-spam: aguarde ~45 s entre reenvios. O código expira em poucos minutos.
            </p>
            <div className="flex flex-col gap-2 sm:flex-row sm:items-end">
              <Button
                type="button"
                variant="secondary"
                className="w-full sm:w-auto shrink-0"
                disabled={enviandoCodigo}
                onClick={() => void aoEnviarCodigo()}
              >
                {enviandoCodigo ? "Enviando…" : "Enviar código ao e-mail"}
              </Button>
              {codigoEnviadoMsg ? (
                <p className="text-xs text-muted-foreground flex-1">{codigoEnviadoMsg}</p>
              ) : null}
            </div>
            <div className="space-y-2">
              <Label htmlFor="otp-rascunho">Código numérico</Label>
              <Input
                id="otp-rascunho"
                inputMode="numeric"
                autoComplete="one-time-code"
                placeholder="ex.: 123456"
                value={codigoOtp}
                onChange={(ev) => setCodigoOtp(ev.target.value)}
                disabled={gravando}
                className="max-w-xs font-mono tabular-nums"
              />
            </div>
            {fluxoErro ? (
              <p className="text-sm text-destructive" role="alert">
                {fluxoErro}
              </p>
            ) : null}
            <Button
              type="button"
              className="w-full sm:w-auto"
              disabled={gravando || !codigoOtp.trim()}
              onClick={() => void aoConfirmarEGravar()}
            >
              {gravando ? "Gravando…" : "Confirmar código e gravar diagnóstico final"}
            </Button>
          </div>
        </CardContent>
        <CardFooter className="flex flex-col gap-3 sm:flex-row sm:items-stretch sm:gap-3">
          {resumo.empresa_cnpj.length !== 14 ? (
            <div
              className="w-full rounded-lg border border-amber-500/40 bg-amber-500/10 px-4 py-3 text-sm text-foreground leading-relaxed"
              role="status"
            >
              <strong className="font-medium text-foreground">Vincular ao painel após o login:</strong> é necessário um{" "}
              <strong className="font-medium text-foreground">CNPJ válido (14 dígitos)</strong> nas respostas.
              Sem CNPJ, use <strong className="font-medium text-foreground">«Revisar no assistente»</strong>, preencha o
              passo 1 e grave o rascunho outra vez antes de entrar na plataforma — ou conclua só com o código por e-mail
              (OTP), sem levar este resultado ao painel neste momento.
            </div>
          ) : null}
          <Button
            type="button"
            size="lg"
            variant="outline"
            className="w-full min-w-0 bg-transparent sm:flex-1"
            onClick={aoIrLogin}
          >
            Entrar ou cadastrar — conta na plataforma
          </Button>
          <Button asChild variant="outline" size="lg" className="w-full min-w-0 sm:flex-1">
            <Link href="/wizard">Revisar no assistente</Link>
          </Button>
        </CardFooter>
      </Card>

      <p className="text-center text-xs text-muted-foreground">
        Cadastro corporativo Tributiq conforme o canal acordado com o time comercial.
      </p>
    </div>
  );
}
