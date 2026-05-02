"use client";

import Link from "next/link";
import { useEffect, useRef, useState } from "react";
import { Controller, useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { useRouter } from "next/navigation";

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
import { Progress } from "@/components/ui/progress";

import {
  DiagnosticoPayloadSchema,
  MENSAGEM_SELECT_PERFIL_EMPRESA,
  type DiagnosticoPayload,
  type DiagnosticoPayloadFormInput,
  UFS_BR,
} from "@/lib/schemas/wizard";
import { cn } from "@/lib/utils";
import { mascaraTelefoneBR } from "@/lib/utils/mascaraTelefoneBr";
import { fetchCnaeSubclasses, type CnaeSubclasseItem } from "@/lib/api/cnae";
import { postDiagnostico } from "@/lib/api/diagnostico";
import { getAccessToken, getApiUrl } from "@/lib/api/config";
import { postValidarAncora } from "@/lib/api/normativa";
import { fetchQuestionarioAdaptativo, type PerguntaCatalogo } from "@/lib/api/questionario";
import { STORAGE_PENDING_DIAGNOSTICO } from "@/lib/wizard/pending_diagnostico";

const TOTAL_STEPS = 3;

/** API pode devolver tipo com variações — unifica para o wizard não cair no ramo errado (ex.: ternária). */
function normalizarTipoPerguntaWizard(tipo: string | undefined): string {
  return (tipo ?? "").trim().toLowerCase();
}

function tipoEhEscalaLikert15(tipo: string | undefined): boolean {
  return normalizarTipoPerguntaWizard(tipo) === "escala_1_5";
}

function tipoEhNumericaWizard(tipo: string | undefined): boolean {
  return normalizarTipoPerguntaWizard(tipo) === "numerica";
}

function normativaWizardPainelAtivo(): boolean {
  /**
   * Painel P8 (POST /normativa/validar-ancora).
   * Colchetes em `process.env` evitam substituição estática no bundle em `next dev`
   * quando o Playwright injeta `NEXT_PUBLIC_WIZARD_NORMATIVA` no subprocesso.
   */
  return process.env["NEXT_PUBLIC_WIZARD_NORMATIVA"] === "true";
}

export function WizardForm() {
  const router = useRouter();
  const [step, setStep] = useState(1);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [catalogLoading, setCatalogLoading] = useState(false);
  const [catalogError, setCatalogError] = useState<string | null>(null);
  const [perguntas, setPerguntas] = useState<PerguntaCatalogo[]>([]);
  const [apiError, setApiError] = useState<string | null>(null);
  const [tokenChecked, setTokenChecked] = useState(false);
  const [normaTexto, setNormaTexto] = useState("");
  const [normaFeedback, setNormaFeedback] = useState<string | null>(null);
  const [normaCarregando, setNormaCarregando] = useState(false);
  /** Índice da pergunta exibida no passo 3 (uma por página). */
  const [indicePerguntaAtual, setIndicePerguntaAtual] = useState(0);
  /** Área rolável do questionário — volta ao topo a cada pergunta para não “ficar” no fim do scroll. */
  const painelPerguntasRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    setTokenChecked(true);
  }, []);

  useEffect(() => {
    if (step !== 3) return;
    painelPerguntasRef.current?.scrollTo({ top: 0, behavior: "auto" });
  }, [step, indicePerguntaAtual]);

  /**
   * Após login com `redirect=/wizard`: envia o payload guardado em sessionStorage (gravar na API).
   */
  useEffect(() => {
    if (!tokenChecked) return;
    if (!getAccessToken()) return;
    const raw = sessionStorage.getItem(STORAGE_PENDING_DIAGNOSTICO);
    if (!raw) return;
    let payload: DiagnosticoPayload;
    try {
      payload = JSON.parse(raw) as DiagnosticoPayload;
    } catch {
      sessionStorage.removeItem(STORAGE_PENDING_DIAGNOSTICO);
      return;
    }
    let cancelled = false;
    void (async () => {
      try {
        setIsSubmitting(true);
        setApiError(null);
        await postDiagnostico(payload);
        sessionStorage.removeItem(STORAGE_PENDING_DIAGNOSTICO);
        if (!cancelled) router.replace("/sucesso");
      } catch (err: unknown) {
        const msg = err instanceof Error ? err.message : "Falha ao gravar diagnóstico na API.";
        if (!cancelled) setApiError(msg);
      } finally {
        if (!cancelled) setIsSubmitting(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [tokenChecked, router]);

  const form = useForm<DiagnosticoPayloadFormInput>({
    resolver: zodResolver(DiagnosticoPayloadSchema),
    defaultValues: {
      empresa: {
        cnpj: "",
        razao_social: "",
        porte: "",
        regime: "",
        cnae_principal: "",
        uf: "",
        setor_macro: "",
      },
      respondente: {
        nome: "",
        email: "",
        telefone: "",
      },
      respostas: [],
      aceite_termos_privacidade: false,
    },
    mode: "onBlur",
  });

  const {
    register,
    control,
    trigger,
    watch,
    formState: { errors },
    getValues,
    reset,
  } = form;

  const [cnaeSugestoes, setCnaeSugestoes] = useState<CnaeSubclasseItem[]>([]);
  const cnaeBusca = watch("empresa.cnae_principal");

  useEffect(() => {
    if (step !== 2) {
      setCnaeSugestoes([]);
      return;
    }
    const bruto = (cnaeBusca ?? "").trim();
    const soDigitos = bruto.replace(/\D/g, "").slice(0, 7);
    const q = soDigitos.length >= 2 ? soDigitos : bruto.length >= 2 ? bruto : "";
    if (q.length < 2) {
      setCnaeSugestoes([]);
      return;
    }
    const t = setTimeout(() => {
      if (!getAccessToken()) {
        setCnaeSugestoes([]);
        return;
      }
      void fetchCnaeSubclasses(q, 12)
        .then((r) => setCnaeSugestoes(r.itens))
        .catch(() => setCnaeSugestoes([]));
    }, 380);
    return () => clearTimeout(t);
  }, [cnaeBusca, step]);

  /** Perfil empresa (passo 2): selects sem valor real exibem placeholder com o mesmo tom do UF. */
  const empresaPerfil = watch("empresa");
  const selectPerfilVazio = (v: string | undefined) => v == null || v === "";
  const classSelectPerfil = (erro: boolean, vazio: boolean) =>
    cn(
      "flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
      vazio && "text-muted-foreground",
      erro && "border-destructive",
    );

  const valorInicialPorTipo = (tipo: string): string | number | string[] => {
    const t = normalizarTipoPerguntaWizard(tipo);
    if (t === "multipla_escolha" || t === "checklist") return [];
    return "";
  };

  const renderPerguntaInput = (p: PerguntaCatalogo, index: number) => {
    const base = `respostas.${index}.valor` as const;
    const rowClass =
      "flex items-center space-x-3 cursor-pointer p-3 rounded border bg-background hover:bg-muted/50 transition-colors";
    const t = normalizarTipoPerguntaWizard(p.tipo);

    if (t === "escala_1_5") {
      return (
        <div
          className="flex flex-wrap gap-2 sm:gap-3 pt-2"
          role="group"
          aria-label="Resposta em escala de 1 a 5"
        >
          {[1, 2, 3, 4, 5].map((n) => (
            <Label
              key={n}
              className={`${rowClass} min-w-[2.75rem] shrink-0 justify-center px-3 py-2.5`}
            >
              <input
                type="radio"
                value={String(n)}
                className="w-4 h-4 text-primary focus:ring-primary"
                {...register(base)}
              />
              <span className="font-normal text-sm tabular-nums">{n}</span>
            </Label>
          ))}
        </div>
      );
    }

    if (t === "binaria") {
      const opts = [
        { v: "sim", l: "Sim" },
        { v: "nao", l: "Não" },
      ];
      return (
        <div className="flex flex-col space-y-2 pt-2">
          {opts.map((o) => (
            <Label key={o.v} className={rowClass}>
              <input
                type="radio"
                value={o.v}
                className="w-4 h-4 text-primary focus:ring-primary"
                {...register(base)}
              />
              <span className="font-normal text-sm">{o.l}</span>
            </Label>
          ))}
        </div>
      );
    }

    if (t === "numerica") {
      return (
        <Input
          type="number"
          min={0}
          max={100}
          step={1}
          placeholder="Ex.: 72"
          className="max-w-xs mt-2"
          {...register(base)}
        />
      );
    }

    if (t === "multipla_escolha" || t === "checklist") {
      const total = p.multipla_total ?? 0;
      const baseLabels =
        p.opcoes && p.opcoes.length > 0 ? p.opcoes : [];
      const rowLabels = Array.from({ length: total }, (_, i) => baseLabels[i] ?? `Item ${i + 1}`);
      if (total < 1) {
        return (
          <p className="text-sm text-destructive pt-2">
            Catálogo incompleto: multipla_total ausente para {p.codigo}.
          </p>
        );
      }
      return (
        <Controller
          name={base}
          control={control}
          render={({ field }) => {
            const selected = Array.isArray(field.value) ? field.value : [];
            return (
              <div className="flex flex-col space-y-2 pt-2">
                {rowLabels.map((label, i) => {
                  const key = `opt_${i + 1}`;
                  const checked = selected.includes(key);
                  return (
                    <Label key={key} className={rowClass}>
                      <input
                        type="checkbox"
                        className="w-4 h-4 rounded border-input text-primary"
                        checked={checked}
                        onChange={(e) => {
                          const cur = Array.isArray(field.value) ? [...field.value] : [];
                          if (e.target.checked) field.onChange([...cur, key]);
                          else field.onChange(cur.filter((x) => x !== key));
                        }}
                      />
                      <span className="font-normal text-sm">{label}</span>
                    </Label>
                  );
                })}
              </div>
            );
          }}
        />
      );
    }

    /* ternaria */
    const opts = [
      { v: "sim", l: "Sim" },
      { v: "parcialmente", l: "Parcialmente" },
      { v: "nao", l: "Não" },
      { v: "nao_se_aplica", l: "Não se aplica ao meu negócio" },
    ];
    return (
      <div className="flex flex-col space-y-2 pt-2">
        {opts.map((o) => (
          <Label key={o.v} className={rowClass}>
            <input
              type="radio"
              value={o.v}
              className="w-4 h-4 text-primary focus:ring-primary"
              {...register(base)}
            />
            <span className="font-normal text-sm">{o.l}</span>
          </Label>
        ))}
      </div>
    );
  };

  const nextStep = async () => {
    let fieldsToValidate: (keyof DiagnosticoPayloadFormInput | string)[] = [];
    if (step === 1) {
      fieldsToValidate = [
        "empresa.cnpj",
        "empresa.razao_social",
        "respondente.nome",
        "respondente.email",
        /* telefone opcional: máscara pode estar incompleta ao avançar — valida só no envio final */
        "aceite_termos_privacidade",
      ];
    } else if (step === 2) {
      fieldsToValidate = [
        "empresa.porte",
        "empresa.regime",
        "empresa.cnae_principal",
        "empresa.uf",
        "empresa.setor_macro",
      ];
    }

    const isStepValid = await trigger(fieldsToValidate as never);
    if (!isStepValid) return;

    if (step === 2) {
      setCatalogError(null);
      setCatalogLoading(true);
      try {
        const empresa = getValues("empresa");
        const q = await fetchQuestionarioAdaptativo(empresa);
        setPerguntas(q.perguntas);
        setIndicePerguntaAtual(0);
        reset({
          ...getValues(),
          respostas: q.perguntas.map((pg) => ({
            pergunta_id: pg.id,
            valor: valorInicialPorTipo(pg.tipo),
          })),
        });
        setStep(3);
        window.scrollTo({ top: 0, behavior: "smooth" });
      } catch (e: unknown) {
        const msg = e instanceof Error ? e.message : "Falha ao carregar questionário.";
        setCatalogError(msg);
      } finally {
        setCatalogLoading(false);
      }
      return;
    }

    setStep((s) => Math.min(s + 1, TOTAL_STEPS));
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const prevStep = () => {
    setStep((s) => Math.max(s - 1, 1));
    window.scrollTo({ top: 0, behavior: "smooth" });
  };

  const validarRespostaNoIndice = (i: number): string | null => {
    const tipo = normalizarTipoPerguntaWizard(perguntas[i]?.tipo);
    const lista = getValues("respostas");
    const v = lista[i]?.valor;
    if (tipo === "multipla_escolha" || tipo === "checklist") {
      if (!Array.isArray(v) || v.length === 0) {
        return "Selecione ao menos uma opção antes de seguir.";
      }
      return null;
    }
    if (tipo === "numerica") {
      const s = v === undefined || v === null ? "" : String(v).trim();
      if (s === "") return "Informe um número antes de seguir.";
      const n = typeof v === "string" ? parseFloat(v) : Number(v);
      if (!Number.isFinite(n) || n < 0 || n > 100) {
        return "Use um número entre 0 e 100.";
      }
      return null;
    }
    if (v === "" || v === undefined || v === null) {
      return "Responda esta pergunta antes de seguir.";
    }
    return null;
  };

  const voltarWizard = () => {
    if (isSubmitting) return;
    setApiError(null);
    if (step === 3 && indicePerguntaAtual > 0) {
      setIndicePerguntaAtual((x) => x - 1);
      window.scrollTo({ top: 0, behavior: "smooth" });
      return;
    }
    prevStep();
  };

  /**
   * Valida o formulário completo e monta o payload do POST (mesmo contrato da API).
   * Retorna null se inválido (mensagem em `apiError`).
   */
  const montarPayloadDiagnosticoValidado = async (): Promise<DiagnosticoPayload | null> => {
    const isValid = await trigger();
    if (!isValid) return null;

    const raw = getValues();
    const respostas = raw.respostas;

    const incompleto = respostas.some((r, i) => {
      const tipo = normalizarTipoPerguntaWizard(perguntas[i]?.tipo);
      const v = r.valor;
      if (tipo === "multipla_escolha" || tipo === "checklist") {
        return !Array.isArray(v) || v.length === 0;
      }
      if (tipo === "numerica") {
        const s = v === undefined || v === null ? "" : String(v).trim();
        return s === "";
      }
      return v === "" || v === undefined || v === null;
    });
    if (incompleto) {
      setApiError("Por favor, responda a todas as perguntas do questionário.");
      return null;
    }

    const respostasNorm = respostas.map((r, i) => {
      const tipo = normalizarTipoPerguntaWizard(perguntas[i]?.tipo);
      const v = r.valor;
      if (tipo === "numerica") {
        const n = typeof v === "string" ? parseFloat(v) : Number(v);
        return { ...r, valor: n };
      }
      return r;
    });

    for (let i = 0; i < perguntas.length; i++) {
      if (normalizarTipoPerguntaWizard(perguntas[i]?.tipo) === "numerica") {
        const v = respostasNorm[i].valor as number;
        if (!Number.isFinite(v) || v < 0 || v > 100) {
          setApiError("Valores numericos devem estar entre 0 e 100.");
          return null;
        }
      }
    }

    setApiError(null);
    try {
      return DiagnosticoPayloadSchema.parse({ ...raw, respostas: respostasNorm });
    } catch {
      setApiError("Não foi possível validar os dados para envio. Revise o formulário.");
      return null;
    }
  };

  const seguirOuFinalizarQuestionario = async () => {
    const n = perguntas.length;
    if (n === 0) return;
    const msgErro = validarRespostaNoIndice(indicePerguntaAtual);
    if (msgErro) {
      setApiError(msgErro);
      return;
    }
    setApiError(null);
    if (indicePerguntaAtual < n - 1) {
      setIndicePerguntaAtual((x) => x + 1);
      window.scrollTo({ top: 0, behavior: "smooth" });
      return;
    }
    await onSubmit();
  };

  /** Guarda o payload, redireciona ao login; ao voltar com JWT o envio à API é automático. */
  const irParaLoginComDiagnosticoPendente = async () => {
    const payload = await montarPayloadDiagnosticoValidado();
    if (!payload) return;
    try {
      sessionStorage.setItem(STORAGE_PENDING_DIAGNOSTICO, JSON.stringify(payload));
    } catch {
      setApiError(
        "Não foi possível guardar o diagnóstico no navegador (sessionStorage). Verifique modo privado ou espaço em disco.",
      );
      return;
    }
    router.push("/login?redirect=/wizard");
  };

  const onSubmit = async () => {
    const payload = await montarPayloadDiagnosticoValidado();
    if (!payload) return;

    if (!getAccessToken()) {
      setApiError(
        "Para gravar na API é necessário cadastro/login B2B. Use «Entrar para gravar diagnóstico».",
      );
      return;
    }

    try {
      setIsSubmitting(true);
      setApiError(null);
      await postDiagnostico(payload);
      router.push("/sucesso");
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Ocorreu um erro ao enviar o diagnóstico.";
      setApiError(msg);
    } finally {
      setIsSubmitting(false);
    }
  };

  const totalPerguntas = perguntas.length;
  const progress =
    step < TOTAL_STEPS
      ? (step / TOTAL_STEPS) * 100
      : totalPerguntas > 0
        ? ((2 + (indicePerguntaAtual + 1) / totalPerguntas) / TOTAL_STEPS) * 100
        : (step / TOTAL_STEPS) * 100;
  const hasToken = tokenChecked && !!getAccessToken();
  const ultimaPerguntaDoQuestionario =
    step === 3 && totalPerguntas > 0 && indicePerguntaAtual >= totalPerguntas - 1;

  /** Botões Voltar / Seguir — reutilizados no rodapé do cartão (passos 1–2) e na barra fixa do passo 3. */
  const renderBotoesNavegacao = (opts: { larguraCheiaEmMobile: boolean }) => {
    const clsBotao = cn(opts.larguraCheiaEmMobile && "w-full sm:w-auto shrink-0");
    return (
      <>
        <Button
          type="button"
          variant="outline"
          onClick={voltarWizard}
          disabled={step === 1 || isSubmitting}
          className={clsBotao}
        >
          Voltar
        </Button>

        {step < TOTAL_STEPS ? (
          <Button
            type="button"
            onClick={() => void nextStep()}
            disabled={catalogLoading}
            className={clsBotao}
          >
            {catalogLoading ? "Carregando perguntas…" : "Próxima Etapa"}
          </Button>
        ) : ultimaPerguntaDoQuestionario && !hasToken ? (
          <Button
            type="button"
            onClick={() => void irParaLoginComDiagnosticoPendente()}
            disabled={isSubmitting || totalPerguntas === 0}
            className={cn(
              "bg-accent text-accent-foreground hover:bg-accent/90",
              clsBotao,
            )}
          >
            Entrar para gravar diagnóstico
          </Button>
        ) : (
          <Button
            type="button"
            onClick={() => void seguirOuFinalizarQuestionario()}
            disabled={isSubmitting || totalPerguntas === 0}
            className={cn(
              "bg-accent text-accent-foreground hover:bg-accent/90",
              clsBotao,
            )}
          >
            {isSubmitting
              ? "Enviando…"
              : ultimaPerguntaDoQuestionario
                ? "Finalizar Diagnóstico"
                : "Seguir"}
          </Button>
        )}
      </>
    );
  };

  return (
    <div
      className={cn(
        "w-full max-w-3xl mx-auto flex flex-col min-h-0",
        step === 3 ? "flex-1 gap-3" : "space-y-6",
      )}
    >
      <div className={cn("space-y-2", step === 3 && "shrink-0")}>
        <div className="flex justify-between text-sm text-muted-foreground font-medium">
          <span>
            Passo {step} de {TOTAL_STEPS}
            {step === 3 && totalPerguntas > 0 && (
              <span className="text-foreground/80">
                {" "}
                · Pergunta {indicePerguntaAtual + 1} de {totalPerguntas}
              </span>
            )}
          </span>
          <span>{Math.round(progress)}% Concluído</span>
        </div>
        <Progress value={progress} className="h-2" />
      </div>

      <div
        className={cn(
          step === 3 &&
            "flex min-h-0 w-full flex-1 flex-col overflow-hidden rounded-xl border border-primary/10 bg-card text-sm shadow-lg ring-1 ring-foreground/10",
          step !== 3 && "contents",
        )}
      >
        <Card
          className={cn(
            "min-h-0",
            step === 3
              ? "flex flex-1 flex-col gap-0 overflow-hidden rounded-none border-0 bg-transparent py-0 text-card-foreground shadow-none ring-0"
              : "border-primary/10 shadow-lg",
          )}
        >
        <CardHeader
          className={cn("space-y-1 bg-muted/30 border-b shrink-0", step === 3 && "py-3 md:py-4")}
        >
          <CardTitle className={cn("text-primary", step === 3 ? "text-xl md:text-2xl" : "text-2xl")}>
            {step === 1 && "Identificação Inicial"}
            {step === 2 && "Perfil da Empresa"}
            {step === 3 && "Questionário adaptativo (Reforma + ABNT NBR 17301)"}
          </CardTitle>
          <CardDescription className={cn(step === 3 && "text-xs md:text-sm leading-snug")}>
            {step === 1 &&
              "M09 — Lead B2B: CNPJ é opcional (minimização de dados). Responder ao assistente não exige sessão; gravar na API exige login após cadastro B2B. LGPD: consentimento abaixo."}
            {step === 2 &&
              "M01 — Motor adaptativo: porte × regime × setor × UF filtram perguntas (LC 214/2025 art. 5º — previsibilidade). A conclusão persiste na API após autenticação."}
            {step === 3 &&
              "Uma pergunta por tela — Seguir / Voltar. Na última pergunta: login para gravar na API; a fase 2 (painel) continua após cadastro/login. Links no bloco recolhível."}
          </CardDescription>
        </CardHeader>

        <CardContent
          ref={painelPerguntasRef}
          className={cn(
            "pt-6",
            step === 3 &&
              "flex flex-1 flex-col min-h-0 overflow-y-auto overscroll-contain pt-4 pb-2 md:pb-3",
          )}
        >
          <form
            className={cn(step === 3 ? "flex flex-col flex-1 min-h-full gap-0" : "space-y-6")}
            onSubmit={(e) => e.preventDefault()}
          >
            {step === 1 && (
              <div className="space-y-4 animate-in fade-in slide-in-from-bottom-4 duration-500">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="cnpj">CNPJ (opcional)</Label>
                    <Input
                      id="cnpj"
                      placeholder="Deixe em branco ou informe 14 dígitos"
                      {...register("empresa.cnpj")}
                      className={errors.empresa?.cnpj ? "border-destructive" : ""}
                    />
                    {errors.empresa?.cnpj && (
                      <p className="text-sm text-destructive">{errors.empresa.cnpj.message}</p>
                    )}
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="razao_social">Razão Social *</Label>
                    <Input
                      id="razao_social"
                      placeholder="Empresa Fictícia LTDA"
                      {...register("empresa.razao_social")}
                      className={errors.empresa?.razao_social ? "border-destructive" : ""}
                    />
                    {errors.empresa?.razao_social && (
                      <p className="text-sm text-destructive">{errors.empresa.razao_social.message}</p>
                    )}
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-4 border-t">
                  <div className="space-y-2">
                    <Label htmlFor="nome">Seu Nome *</Label>
                    <Input
                      id="nome"
                      placeholder="João da Silva"
                      {...register("respondente.nome")}
                      className={errors.respondente?.nome ? "border-destructive" : ""}
                    />
                    {errors.respondente?.nome && (
                      <p className="text-sm text-destructive">{errors.respondente.nome.message}</p>
                    )}
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="email">E-mail Profissional *</Label>
                    <Input
                      id="email"
                      type="email"
                      placeholder="joao@empresa.com.br"
                      autoComplete="email"
                      {...register("respondente.email")}
                      className={errors.respondente?.email ? "border-destructive" : ""}
                    />
                    {errors.respondente?.email && (
                      <p className="text-sm text-destructive">{errors.respondente.email.message}</p>
                    )}
                  </div>
                </div>

                <div className="space-y-2 max-w-md">
                  <Label htmlFor="telefone">Telefone (opcional)</Label>
                  <Controller
                    name="respondente.telefone"
                    control={control}
                    render={({ field }) => (
                      <Input
                        id="telefone"
                        type="tel"
                        inputMode="numeric"
                        autoComplete="tel-national"
                        placeholder="(11) 98765-4321"
                        maxLength={15}
                        aria-describedby="hint-telefone"
                        value={field.value ?? ""}
                        onBlur={field.onBlur}
                        onChange={(e) => field.onChange(mascaraTelefoneBR(e.target.value))}
                      />
                    )}
                  />
                  <p id="hint-telefone" className="text-xs text-muted-foreground">
                    M09 — Apenas DDD e número (sem +55). Facilita recontato B2B; opcional na API MVP.
                  </p>
                  {errors.respondente?.telefone != null &&
                    typeof errors.respondente.telefone === "object" &&
                    "message" in errors.respondente.telefone && (
                      <p className="text-sm text-destructive">
                        {errors.respondente.telefone.message as string}
                      </p>
                    )}
                </div>

                <div className="rounded-md border p-4 space-y-2 bg-muted/20">
                  <div className="flex items-start gap-3">
                    <Controller
                      name="aceite_termos_privacidade"
                      control={control}
                      render={({ field }) => (
                        <input
                          type="checkbox"
                          id="lgpd"
                          className="mt-1 h-4 w-4"
                          checked={field.value}
                          onChange={(e) => field.onChange(e.target.checked)}
                        />
                      )}
                    />
                    <Label htmlFor="lgpd" className="font-normal text-sm leading-snug cursor-pointer">
                      Declaro que li e aceito o tratamento dos dados informados para elaboração do
                      diagnóstico, nos termos da LGPD (Lei 13.709/2018). Consulte a{" "}
                      <Link href="/privacidade" className="text-primary underline">
                        política de privacidade (QDI)
                      </Link>
                      .
                    </Label>
                  </div>
                  {errors.aceite_termos_privacidade && (
                    <p className="text-sm text-destructive">
                      {errors.aceite_termos_privacidade.message}
                    </p>
                  )}
                </div>
              </div>
            )}

            {step === 2 && (
              <div className="space-y-4 animate-in fade-in slide-in-from-bottom-4 duration-500">
                <span className="sr-only" aria-live="polite">
                  {catalogLoading ? "Carregando questionário adaptativo." : ""}
                </span>
                {!getAccessToken() && (
                  <div className="rounded-md border border-border bg-muted/30 px-3 py-2 text-xs text-muted-foreground md:text-sm">
                    Você pode preencher o assistente sem sessão. Para{" "}
                    <span className="font-medium text-foreground">gravar o diagnóstico na API</span>, na
                    última pergunta use{" "}
                    <span className="font-medium text-foreground">Entrar para gravar diagnóstico</span>{" "}
                    (cadastro/login B2B).
                  </div>
                )}
                {catalogError && (
                  <div className="rounded-md border border-destructive/30 bg-destructive/10 p-3 text-sm text-destructive">
                    {catalogError}
                  </div>
                )}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="porte">Porte da Empresa *</Label>
                    <select
                      id="porte"
                      className={classSelectPerfil(
                        !!errors.empresa?.porte,
                        selectPerfilVazio(empresaPerfil.porte),
                      )}
                      {...register("empresa.porte")}
                    >
                      <option value="" disabled>
                        {MENSAGEM_SELECT_PERFIL_EMPRESA}
                      </option>
                      <option value="micro">Micro (Até R$ 360 mil)</option>
                      <option value="pequeno">Pequeno (Até R$ 4,8 mi)</option>
                      <option value="medio">Médio (Até R$ 500 mi)</option>
                      <option value="grande">Grande (Até R$ 5 bi)</option>
                      <option value="enterprise">Enterprise (Acima de R$ 5 bi)</option>
                    </select>
                    {errors.empresa?.porte && (
                      <p className="text-sm text-destructive">{errors.empresa.porte.message}</p>
                    )}
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="regime">Regime Tributário *</Label>
                    <select
                      id="regime"
                      className={classSelectPerfil(
                        !!errors.empresa?.regime,
                        selectPerfilVazio(empresaPerfil.regime),
                      )}
                      {...register("empresa.regime")}
                    >
                      <option value="" disabled>
                        {MENSAGEM_SELECT_PERFIL_EMPRESA}
                      </option>
                      <option value="simples_nacional">Simples Nacional</option>
                      <option value="lucro_presumido">Lucro Presumido</option>
                      <option value="lucro_real">Lucro Real</option>
                      <option value="mei">MEI</option>
                    </select>
                    {errors.empresa?.regime && (
                      <p className="text-sm text-destructive">{errors.empresa.regime.message}</p>
                    )}
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="setor_macro">Setor Macro *</Label>
                    <select
                      id="setor_macro"
                      className={classSelectPerfil(
                        !!errors.empresa?.setor_macro,
                        selectPerfilVazio(empresaPerfil.setor_macro),
                      )}
                      {...register("empresa.setor_macro")}
                    >
                      <option value="" disabled>
                        {MENSAGEM_SELECT_PERFIL_EMPRESA}
                      </option>
                      <option value="comercio">Comércio</option>
                      <option value="industria">Indústria</option>
                      <option value="servicos">Serviços</option>
                      <option value="agro">Agro</option>
                      <option value="consumo">Consumo</option>
                    </select>
                    {errors.empresa?.setor_macro && (
                      <p className="text-sm text-destructive">{errors.empresa.setor_macro.message}</p>
                    )}
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="uf">UF *</Label>
                    <select
                      id="uf"
                      className={classSelectPerfil(!!errors.empresa?.uf, selectPerfilVazio(empresaPerfil.uf))}
                      {...register("empresa.uf")}
                    >
                      <option value="" disabled>
                        {MENSAGEM_SELECT_PERFIL_EMPRESA}
                      </option>
                      {UFS_BR.map((uf) => (
                        <option key={uf} value={uf}>
                          {uf}
                        </option>
                      ))}
                    </select>
                    {errors.empresa?.uf && (
                      <p className="text-sm text-destructive">{errors.empresa.uf.message}</p>
                    )}
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="cnae_principal">CNAE Principal (7 dígitos) *</Label>
                  <datalist id="cnae-sugestoes-wizard">
                    {cnaeSugestoes.map((s) => (
                      <option key={s.subclasse_id} value={s.subclasse_id}>
                        {s.descricao}
                      </option>
                    ))}
                  </datalist>
                  <Input
                    id="cnae_principal"
                    placeholder="1234567 ou busque por texto"
                    list="cnae-sugestoes-wizard"
                    autoComplete="off"
                    {...register("empresa.cnae_principal")}
                    className={errors.empresa?.cnae_principal ? "border-destructive" : ""}
                  />
                  <p className="text-xs text-muted-foreground">
                    Com sessão ativa e API com Postgres (DATABASE_URL), digite 2+ caracteres para sugestões
                    CONCLA/IBGE (GET /referencia/cnae/subclasses).
                  </p>
                  {errors.empresa?.cnae_principal && (
                    <p className="text-sm text-destructive">{errors.empresa.cnae_principal.message}</p>
                  )}
                </div>
              </div>
            )}

                {step === 3 && (
              <div className="flex min-h-0 flex-1 flex-col gap-3 animate-in fade-in slide-in-from-bottom-4 duration-500">
                <div className="shrink-0 space-y-2">
                  {normativaWizardPainelAtivo() && (
                    <div
                      data-testid="wizard-p8-normativa"
                      className="rounded-lg border bg-muted/10 p-3 space-y-2"
                    >
                      <p className="text-sm font-semibold text-foreground">
                        P8 — Protótipo: checagem leve de redação normativa (não é Lexiq / RAG completo)
                      </p>
                      <p className="text-xs text-muted-foreground leading-relaxed">
                        Ferramenta didática apenas: heurísticas simples sobre citações (ex.: LC 214/2025, EC 132/2023).
                        Não gera parecer jurídico, não substitui análise profissional e não garante suficiência
                        perante auditorias formais (LC 214/2025 — boa fé informacional ao contribuinte). Endpoint{" "}
                        <span className="font-mono">POST /normativa/validar-ancora</span> sem login.
                      </p>
                      <textarea
                        value={normaTexto}
                        onChange={(e) => setNormaTexto(e.target.value)}
                        rows={3}
                        className="w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                        placeholder="Ex.: Esta prática deve ser revisada conforme LC 214/2025 art. 5º."
                      />
                      <div className="flex gap-2 items-center flex-wrap">
                        <Button
                          type="button"
                          variant="secondary"
                          size="sm"
                          disabled={normaCarregando || normaTexto.trim().length < 3}
                          onClick={async () => {
                            setNormaFeedback(null);
                            setNormaCarregando(true);
                            try {
                              const r = await postValidarAncora(normaTexto.trim());
                              setNormaFeedback(
                                r.valido ? "Aceito — âncora normativa reconhecível." : (r.motivo_rejeicao ?? "Sem âncora."),
                              );
                            } catch (err) {
                              setNormaFeedback(err instanceof Error ? err.message : "Erro ao validar.");
                            } finally {
                              setNormaCarregando(false);
                            }
                          }}
                        >
                          {normaCarregando ? "Validando…" : "Validar texto"}
                        </Button>
                        {normaFeedback && (
                          <span className="text-xs text-muted-foreground" role="status">
                            {normaFeedback}
                          </span>
                        )}
                      </div>
                    </div>
                  )}
                  {!hasToken && ultimaPerguntaDoQuestionario && (
                    <div className="rounded-md border border-border bg-muted/30 px-3 py-2 text-xs text-muted-foreground md:text-sm">
                      O diagnóstico só é registrado na API após{" "}
                      <span className="font-medium text-foreground">cadastro e login</span>. Use «Entrar para
                      gravar diagnóstico» — o envio ocorre logo após a autenticação. A fase 2 (painel
                      consultor) fica disponível com a mesma sessão.
                    </div>
                  )}
                  {apiError && (
                    <div className="px-3 py-2 bg-destructive/10 border border-destructive/20 text-destructive rounded-md text-xs md:text-sm">
                      {apiError}
                    </div>
                  )}
                  <details className="rounded-md border bg-muted/30 px-3 py-2 text-xs shrink-0 group">
                    <summary className="cursor-pointer font-medium text-muted-foreground list-none flex items-center gap-2 select-none [&::-webkit-details-marker]:hidden">
                      <span aria-hidden className="text-[10px] opacity-70 group-open:rotate-90 transition-transform">
                        ▸
                      </span>
                      Metodologia e transparência (links)
                    </summary>
                    <div className="mt-2 flex flex-wrap gap-x-3 gap-y-1 text-muted-foreground pt-1 border-t border-border/50">
                      <Link href="/abnt-framework" className="text-primary underline font-medium">
                        M11 — ABNT (guia)
                      </Link>
                      <a
                        href={`${getApiUrl().replace(/\/$/, "")}/diagnosticos/manifesto-pesos`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-primary underline font-medium"
                      >
                        Manifesto (JSON)
                      </a>
                      <Link href="/metodologia" className="text-primary underline font-medium">
                        Metodologia (painel)
                      </Link>
                      <a
                        href={`${getApiUrl().replace(/\/$/, "")}/diagnosticos/metodologia`}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-primary underline font-medium"
                      >
                        Metodologia (JSON)
                      </a>
                    </div>
                  </details>
                </div>
                {totalPerguntas > 0 && indicePerguntaAtual < totalPerguntas && (
                  <div
                    key={perguntas[indicePerguntaAtual].id}
                    data-testid="wizard-pergunta-atual"
                    className="mx-auto flex min-h-0 w-full max-w-xl flex-col justify-start space-y-3 rounded-lg border bg-muted/20 p-4 sm:p-5"
                  >
                    <Label className="text-base font-semibold text-foreground/90 leading-tight block">
                      {indicePerguntaAtual + 1}. {perguntas[indicePerguntaAtual].texto}{" "}
                      <span className="text-muted-foreground font-normal text-xs">
                        ({perguntas[indicePerguntaAtual].codigo})
                      </span>
                    </Label>
                    {perguntas[indicePerguntaAtual].base_legal && (
                      <p className="text-xs text-muted-foreground">
                        Base legal (referência): {perguntas[indicePerguntaAtual].base_legal}
                      </p>
                    )}
                    {tipoEhEscalaLikert15(perguntas[indicePerguntaAtual].tipo) && (
                      <p className="text-sm text-muted-foreground leading-snug">
                        Escala Likert (1 a 5): 1 = menor aderência, 5 = maior aderência à prática perguntada.
                      </p>
                    )}
                    {tipoEhNumericaWizard(perguntas[indicePerguntaAtual].tipo) && (
                      <p className="text-sm text-muted-foreground leading-snug">
                        Escala numérica: informe um inteiro de 0 a 100 (conforme o enunciado).
                      </p>
                    )}
                    {renderPerguntaInput(perguntas[indicePerguntaAtual], indicePerguntaAtual)}
                  </div>
                )}
              </div>
            )}
          </form>
        </CardContent>

        {step !== 3 ? (
          <CardFooter className="flex w-full min-w-0 shrink-0 flex-wrap justify-between gap-3 border-t bg-muted/10 p-6">
            {renderBotoesNavegacao({ larguraCheiaEmMobile: false })}
          </CardFooter>
        ) : null}
      </Card>
      {step === 3 ? (
        <div
          role="toolbar"
          aria-label="Navegação do questionário"
          className="flex w-full shrink-0 flex-col-reverse gap-3 border-t border-primary/10 bg-muted/50 px-4 py-4 pb-[max(1rem,env(safe-area-inset-bottom))] sm:flex-row sm:flex-wrap sm:items-center sm:justify-between md:px-6"
        >
          {renderBotoesNavegacao({ larguraCheiaEmMobile: true })}
        </div>
      ) : null}
      </div>
    </div>
  );
}
