"use client";

import Link from "next/link";
import { useRouter } from "next/navigation";
import { useEffect, useMemo, useState } from "react";
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
  postDiagnosticoSelfService,
  postSelfServiceToken,
  postSolicitarCodigoEmail,
} from "@/lib/api/self_service_diagnostico";
import type { DiagnosticoPayload } from "@/lib/schemas/wizard";
import {
  clearPendingDiagnosticoFromStorage,
  loadPendingDiagnosticoFromStorage,
} from "@/lib/wizard/pending_diagnostico";
import { saveSelfServiceDiagnosticoResultado } from "@/lib/wizard/self_service_result";
import { clearWizardDraft } from "@/lib/wizard/wizard_draft";

/** Extrai campos exibidos na página de conclusão a partir da resposta JSON da API. */
function respostaApiParaResultado(data: unknown): {
  id: string;
  status: string;
  empresa_razao_social: string;
  locale_relatorio: string;
  score_geral: number | null;
} | null {
  if (!data || typeof data !== "object") return null;
  const o = data as Record<string, unknown>;
  const id = o["id"];
  const status = o["status"];
  const empresa_razao_social = o["empresa_razao_social"];
  const locale_relatorio = o["locale_relatorio"];
  if (typeof id !== "string" || typeof status !== "string") return null;
  if (typeof empresa_razao_social !== "string") return null;
  const loc = typeof locale_relatorio === "string" ? locale_relatorio : "pt-BR";
  let score_geral: number | null = null;
  const score = o["score"];
  if (score && typeof score === "object") {
    const sg = (score as Record<string, unknown>)["score_geral"];
    if (sg && typeof sg === "object") {
      const v = (sg as Record<string, unknown>)["valor"];
      if (typeof v === "number" && Number.isFinite(v)) score_geral = v;
    }
  }
  return { id, status, empresa_razao_social, locale_relatorio: loc, score_geral };
}

export default function DiagnosticoGravadoLocalPage() {
  const router = useRouter();
  const [payload, setPayload] = useState<DiagnosticoPayload | null>(null);
  const [codigoOtp, setCodigoOtp] = useState("");
  const [codigoEnviadoMsg, setCodigoEnviadoMsg] = useState<string | null>(null);
  const [enviandoCodigo, setEnviandoCodigo] = useState(false);
  const [gravando, setGravando] = useState(false);
  const [fluxoErro, setFluxoErro] = useState<string | null>(null);

  useEffect(() => {
    const p = loadPendingDiagnosticoFromStorage();
    if (!p) {
      router.replace("/wizard");
      return;
    }
    setPayload(p);
  }, [router]);

  const loginHref = "/login?redirect=/wizard";

  const jsonCompleto = useMemo(() => {
    if (!payload) return "";
    try {
      return JSON.stringify(payload, null, 2);
    } catch {
      return "";
    }
  }, [payload]);

  const emailRespondente = payload?.respondente.email?.trim() ?? "";

  async function aoEnviarCodigo() {
    if (!emailRespondente) return;
    setFluxoErro(null);
    setEnviandoCodigo(true);
    setCodigoEnviadoMsg(null);
    try {
      const r = await postSolicitarCodigoEmail(emailRespondente);
      setCodigoEnviadoMsg(r.mensagem);
    } catch (e) {
      setFluxoErro(e instanceof Error ? e.message : "Falha ao solicitar código.");
    } finally {
      setEnviandoCodigo(false);
    }
  }

  async function aoConfirmarEGravar() {
    if (!payload || !emailRespondente) return;
    const limpo = codigoOtp.trim().replace(/\s+/g, "");
    if (limpo.length < 4) {
      setFluxoErro("Informe o código recebido por e-mail (mínimo 4 dígitos).");
      return;
    }
    setFluxoErro(null);
    setGravando(true);
    try {
      const { access_token: token } = await postSelfServiceToken(emailRespondente, limpo);
      const raw = await postDiagnosticoSelfService(payload, token);
      const resumo = respostaApiParaResultado(raw);
      if (!resumo) {
        throw new Error("Resposta da API em formato inesperado.");
      }
      saveSelfServiceDiagnosticoResultado(resumo);
      clearPendingDiagnosticoFromStorage();
      clearWizardDraft();
      router.push("/diagnostico/concluido-self-service");
    } catch (e) {
      const msg = e instanceof Error ? e.message : "Falha ao gravar.";
      setFluxoErro(
        `${msg} Se o código já foi usado, solicite um novo e tente de novo.`,
      );
    } finally {
      setGravando(false);
    }
  }

  if (!payload) {
    return (
      <div className="container max-w-lg py-16 text-center text-sm text-muted-foreground">
        Carregando…
      </div>
    );
  }

  const { empresa, respondente, respostas, locale_relatorio } = payload;
  const nRespostas = respostas.length;

  return (
    <div className="container max-w-xl py-10 px-4 space-y-8">
      <div className="flex justify-center">
        <div className="flex h-16 w-16 items-center justify-center rounded-full bg-accent/15 text-accent">
          <CheckCircle2 className="h-8 w-8" aria-hidden />
        </div>
      </div>

      <div className="text-center space-y-2">
        <h1 className="text-2xl font-bold tracking-tight md:text-3xl">
          Diagnóstico guardado neste navegador
        </h1>
        <p className="text-muted-foreground text-sm leading-relaxed max-w-md mx-auto">
          Suas respostas estão neste dispositivo. Para <strong className="text-foreground">gravar na nuvem</strong>{" "}
          sem conta corporativa, confirme o mesmo e-mail do assistente com o código que enviamos. Alternativa: entrar
          com conta B2B no painel consultor (o assistente pode enviar o pendente após o login).
        </p>
      </div>

      <Card>
        <CardHeader className="pb-2">
          <CardTitle className="text-lg">Resumo</CardTitle>
          <CardDescription>O que será gravado na API</CardDescription>
        </CardHeader>
        <CardContent className="space-y-3 text-sm">
          <div className="rounded-lg border bg-muted/30 px-4 py-3 space-y-1">
            <p className="font-medium text-foreground">{empresa.razao_social}</p>
            {empresa.cnpj ? (
              <p className="text-muted-foreground tabular-nums">CNPJ: {empresa.cnpj}</p>
            ) : (
              <p className="text-muted-foreground">CNPJ não informado (entrada self-service)</p>
            )}
          </div>
          <div className="rounded-lg border bg-muted/30 px-4 py-3 space-y-1">
            <p className="text-foreground">
              <span className="font-medium">Respondente:</span> {respondente.nome}
            </p>
            <p className="text-muted-foreground">{respondente.email}</p>
            {respondente.telefone ? (
              <p className="text-muted-foreground tabular-nums">Tel.: {respondente.telefone}</p>
            ) : null}
          </div>
          <p className="text-muted-foreground">
            <span className="font-medium text-foreground">{nRespostas}</span>{" "}
            {nRespostas === 1 ? "resposta" : "respostas"} ao questionário adaptativo · idioma do relatório:{" "}
            <span className="font-medium text-foreground">{locale_relatorio}</span>
          </p>

          <div className="rounded-lg border border-dashed bg-muted/20 px-4 py-4 space-y-4">
            <p className="font-medium text-foreground text-sm">Gravar na nuvem (e-mail + código)</p>
            <p className="text-xs text-muted-foreground leading-relaxed">
              Usamos o mesmo mecanismo de verificação do assistente. O código expira em poucos minutos; aguarde ~45 s
              entre um envio e outro (anti-spam).
            </p>
            <div className="flex flex-col gap-2 sm:flex-row sm:items-end">
              <Button
                type="button"
                variant="secondary"
                className="w-full sm:w-auto shrink-0"
                disabled={enviandoCodigo || !emailRespondente}
                onClick={() => void aoEnviarCodigo()}
              >
                {enviandoCodigo ? "Enviando…" : "Enviar código ao e-mail"}
              </Button>
              {codigoEnviadoMsg ? (
                <p className="text-xs text-muted-foreground flex-1">{codigoEnviadoMsg}</p>
              ) : null}
            </div>
            <div className="space-y-2">
              <Label htmlFor="otp-self-service">Código numérico</Label>
              <Input
                id="otp-self-service"
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
              {gravando ? "Gravando…" : "Confirmar código e gravar na nuvem"}
            </Button>
          </div>
        </CardContent>
        <CardFooter className="flex-col gap-3 sm:flex-row sm:justify-stretch">
          <Button asChild size="lg" variant="outline" className="w-full bg-transparent">
            <Link href={loginHref}>Entrar ou cadastrar — painel B2B</Link>
          </Button>
          <Button asChild variant="outline" size="lg" className="w-full bg-transparent">
            <Link href="/wizard">Revisar no assistente</Link>
          </Button>
        </CardFooter>
      </Card>

      <details className="rounded-xl border bg-card text-sm">
        <summary className="cursor-pointer px-4 py-3 font-medium text-foreground select-none list-none flex items-center gap-2 [&::-webkit-details-marker]:hidden">
          <span aria-hidden className="text-muted-foreground">
            ▸
          </span>
          Ver conteúdo completo (técnico)
        </summary>
        <div className="px-4 pb-4 space-y-2 border-t pt-3">
          <p className="text-xs text-muted-foreground leading-relaxed">
            Estrutura enviada à API após confirmação — conferência ou suporte. Não compartilhe em canais inseguros
            (LGPD).
          </p>
          <pre className="max-h-[min(420px,55vh)] overflow-auto rounded-md border bg-muted/40 p-3 text-xs leading-snug">
            {jsonCompleto}
          </pre>
        </div>
      </details>

      <p className="text-center text-xs text-muted-foreground">
        Cadastro corporativo Tributiq conforme o canal acordado com o time comercial.
      </p>
    </div>
  );
}
