"use client";

import Link from "next/link";
import { useCallback, useEffect, useLayoutEffect, useRef, useState, type ReactNode } from "react";
import { createPortal } from "react-dom";
import { Controller, useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { useRouter } from "next/navigation";
import { Info } from "lucide-react";

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
import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";

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
import { ADMIN_PERFIL_CONTA_STORAGE_KEY, getAccessToken } from "@/lib/api/config";
import { postValidarAncora } from "@/lib/api/normativa";
import { fetchQuestionarioAdaptativo, type PerguntaCatalogo } from "@/lib/api/questionario";
import { rotulosEscalaParaPergunta } from "@/lib/wizard/escalaLabels";
import { STORAGE_PENDING_DIAGNOSTICO } from "@/lib/wizard/pending_diagnostico";
import {
  clearWizardDraft,
  loadWizardDraft,
  saveWizardDraft,
} from "@/lib/wizard/wizard_draft";
import { montarRotulosMultiplaEscolha } from "@/lib/wizard/multiplaLabels";

const TOTAL_STEPS = 3;

/**
 * Reserva linha para erro de validação — evita que uma coluna “puxe” o alinhamento vertical
 * do grid quando só um campo falha (ex.: Porte × Regime).
 */
function SlotMensagemErroCampo({ children }: { children?: ReactNode }) {
  return (
    <div className="min-h-[1.375rem] text-sm leading-tight text-destructive" aria-live="polite">
      {children}
    </div>
  );
}

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
  /** Evita gravar rascunho durante hidratação inicial (restore). */
  const skipPersistRef = useRef(false);
  /** Após ler/restaurar sessionStorage — só então passamos a persistir alterações. */
  const [draftHydrated, setDraftHydrated] = useState(false);

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
        clearWizardDraft();
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
      locale_relatorio: "pt-BR",
      plano: "gratuito",
      respostas: [],
      aceite_termos_privacidade: false,
    },
    mode: "onBlur",
  });

  useEffect(() => {
    if (typeof window === "undefined") return;
    const p = window.localStorage.getItem(ADMIN_PERFIL_CONTA_STORAGE_KEY);
    if (p === "avancado") {
      form.setValue("plano", "avancado");
    }
  }, [form]);

  const {
    register,
    control,
    trigger,
    watch,
    clearErrors,
    formState: { errors },
    getValues,
    reset,
  } = form;

  const [cnaeSugestoes, setCnaeSugestoes] = useState<CnaeSubclasseItem[]>([]);
  /** Texto no input (código ou busca por descrição); o formulário só guarda 7 dígitos após seleção/blur válido. */
  const [cnaeBuscaTexto, setCnaeBuscaTexto] = useState("");
  const cnaeBuscaTextoRef = useRef("");
  const [cnaeListaAberta, setCnaeListaAberta] = useState(false);
  const cnaeBlurFecharTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const cnaeAnchorRef = useRef<HTMLDivElement>(null);
  /** Posição em viewport (fixed) — portal evita cortes por overflow/transform do Card/animações. */
  const [cnaePopoverBox, setCnaePopoverBox] = useState<{
    top: number;
    left: number;
    width: number;
  } | null>(null);
  /** Evita sobrescrever a digitação: só alinha com RHF ao entrar no passo 2 (não a cada mudança de `getValues`). */
  const stepAnteriorCnaeRef = useRef<number | null>(null);

  const atualizarPosicaoListaCnae = useCallback(() => {
    const el = cnaeAnchorRef.current;
    if (!el || !cnaeListaAberta || cnaeSugestoes.length === 0 || step !== 2) {
      setCnaePopoverBox(null);
      return;
    }
    const r = el.getBoundingClientRect();
    const margin = 10;
    const vw = window.innerWidth;
    const minW = Math.min(420, vw - 2 * margin);
    const maxW = Math.min(Math.max(r.width, minW), vw - 2 * margin);
    let left = r.left;
    if (left + maxW > vw - margin) {
      left = Math.max(margin, vw - margin - maxW);
    }
    if (left < margin) left = margin;
    setCnaePopoverBox({ top: r.bottom + 6, left, width: maxW });
  }, [cnaeListaAberta, cnaeSugestoes.length, step]);

  useLayoutEffect(() => {
    if (step !== 2 || !cnaeListaAberta || cnaeSugestoes.length === 0) {
      setCnaePopoverBox(null);
      return;
    }
    atualizarPosicaoListaCnae();
    window.addEventListener("scroll", atualizarPosicaoListaCnae, true);
    window.addEventListener("resize", atualizarPosicaoListaCnae);
    return () => {
      window.removeEventListener("scroll", atualizarPosicaoListaCnae, true);
      window.removeEventListener("resize", atualizarPosicaoListaCnae);
    };
  }, [step, cnaeListaAberta, cnaeSugestoes, atualizarPosicaoListaCnae]);

  useEffect(() => {
    if (step !== 2) {
      setCnaeSugestoes([]);
      setCnaeListaAberta(false);
      stepAnteriorCnaeRef.current = step;
      return;
    }
    const anterior = stepAnteriorCnaeRef.current;
    stepAnteriorCnaeRef.current = step;
    if (anterior !== 2) {
      const v = getValues("empresa.cnae_principal") ?? "";
      setCnaeBuscaTexto(v);
      cnaeBuscaTextoRef.current = v;
    }
    // getValues omitido de deps de propósito — só queremos o snapshot ao transitar para o passo 2.
    // eslint-disable-next-line react-hooks/exhaustive-deps -- sincronizar apenas mudança de `step`
  }, [step]);

  useEffect(() => {
    if (step !== 2) {
      setCnaeSugestoes([]);
      return;
    }
    const bruto = (cnaeBuscaTexto ?? "").trim();
    const soDigitos = bruto.replace(/\D/g, "").slice(0, 7);
    const q = soDigitos.length >= 2 ? soDigitos : bruto.length >= 2 ? bruto : "";
    if (q.length < 2) {
      setCnaeSugestoes([]);
      return;
    }
    const t = setTimeout(() => {
      void fetchCnaeSubclasses(q, 12)
        .then((r) => setCnaeSugestoes(r.itens))
        .catch(() => setCnaeSugestoes([]));
    }, 380);
    return () => clearTimeout(t);
  }, [cnaeBuscaTexto, step]);

  useEffect(() => {
    return () => {
      if (cnaeBlurFecharTimerRef.current != null) clearTimeout(cnaeBlurFecharTimerRef.current);
    };
  }, []);

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

  /**
   * Restaura passo, questionário e respostas após navegação externa (ex.: política de privacidade).
   * Não disputa com o fluxo «JWT + diagnóstico pendente» que faz POST automático e redirect.
   */
  useEffect(() => {
    let cancelled = false;

    const skipRestore =
      typeof window !== "undefined" &&
      !!getAccessToken() &&
      !!sessionStorage.getItem(STORAGE_PENDING_DIAGNOSTICO);

    if (skipRestore) {
      setDraftHydrated(true);
      return () => {
        cancelled = true;
      };
    }

    skipPersistRef.current = true;

    void (async () => {
      try {
        const draft = loadWizardDraft();
        if (!draft) return;

        if (draft.step < 3) {
          reset({
            ...draft.form,
            respostas: Array.isArray(draft.form.respostas) ? draft.form.respostas : [],
          });
          setStep(draft.step);
          setIndicePerguntaAtual(draft.indicePerguntaAtual);
          return;
        }

        setCatalogLoading(true);
        try {
          const q = await fetchQuestionarioAdaptativo(draft.form.empresa);
          if (cancelled) return;
          const map = new Map(draft.form.respostas.map((r) => [r.pergunta_id, r.valor]));
          const merged = q.perguntas.map((pg) => ({
            pergunta_id: pg.id,
            valor: map.has(pg.id) ? map.get(pg.id)! : valorInicialPorTipo(pg.tipo),
          }));
          setPerguntas(q.perguntas);
          reset({
            ...draft.form,
            respostas: merged,
          });
          setStep(3);
          setIndicePerguntaAtual(
            Math.min(draft.indicePerguntaAtual, Math.max(0, q.perguntas.length - 1)),
          );
        } catch {
          if (!cancelled) {
            setPerguntas([]);
            setStep(2);
            reset({
              ...draft.form,
              respostas: [],
            });
            setIndicePerguntaAtual(0);
          }
        } finally {
          if (!cancelled) setCatalogLoading(false);
        }
      } finally {
        if (!cancelled) {
          skipPersistRef.current = false;
          setDraftHydrated(true);
        }
      }
    })();

    return () => {
      cancelled = true;
    };
  }, [reset]);

  /** Persiste rascunho com debounce — mesma origem que «Voltar ao diagnóstico» na política de privacidade. */
  useEffect(() => {
    if (!draftHydrated) return;

    /** DOM retorna handle numérico; tipagem Node (`Timeout`) conflita em builds Next — usar number. */
    let timeout: number | undefined;

    const persist = () => {
      if (skipPersistRef.current) return;
      if (typeof window === "undefined") return;
      if (getAccessToken() && sessionStorage.getItem(STORAGE_PENDING_DIAGNOSTICO)) return;

      saveWizardDraft({
        v: 1,
        step,
        indicePerguntaAtual,
        form: getValues(),
      });
    };

    const runDebounced = () => {
      if (timeout !== undefined) window.clearTimeout(timeout);
      timeout = window.setTimeout(persist, 400);
    };

    runDebounced();

    const sub = watch(() => {
      runDebounced();
    });

    return () => {
      sub.unsubscribe();
      if (timeout !== undefined) window.clearTimeout(timeout);
    };
  }, [
    draftHydrated,
    watch,
    getValues,
    step,
    indicePerguntaAtual,
  ]);

  /** Grava imediatamente ao sair da página (evita perder rascunho se o debounce não disparou). */
  useEffect(() => {
    if (!draftHydrated) return;

    const flush = () => {
      if (skipPersistRef.current) return;
      if (typeof window === "undefined") return;
      if (getAccessToken() && sessionStorage.getItem(STORAGE_PENDING_DIAGNOSTICO)) return;
      saveWizardDraft({
        v: 1,
        step,
        indicePerguntaAtual,
        form: getValues(),
      });
    };

    const onVisibility = () => {
      if (document.visibilityState === "hidden") flush();
    };

    window.addEventListener("pagehide", flush);
    document.addEventListener("visibilitychange", onVisibility);
    return () => {
      window.removeEventListener("pagehide", flush);
      document.removeEventListener("visibilitychange", onVisibility);
    };
  }, [
    draftHydrated,
    getValues,
    step,
    indicePerguntaAtual,
  ]);

  const renderPerguntaInput = (p: PerguntaCatalogo, index: number) => {
    const base = `respostas.${index}.valor` as const;
    const rowClass =
      "flex items-center space-x-3 cursor-pointer p-3 rounded border bg-background hover:bg-muted/50 transition-colors";
    const t = normalizarTipoPerguntaWizard(p.tipo);

    if (t === "escala_1_5") {
      const rotulos = rotulosEscalaParaPergunta(p.rotulos_escala);
      return (
        <div className="flex flex-col gap-2 pt-2" role="group" aria-label="Resposta em escala de 1 a 5">
          {[1, 2, 3, 4, 5].map((n) => (
            <Label
              key={n}
              className={`${rowClass} w-full flex-wrap items-start gap-3 py-3 sm:items-center`}
            >
              <div className="flex shrink-0 items-center gap-2">
                <input
                  type="radio"
                  value={String(n)}
                  className="h-4 w-4 text-primary focus:ring-primary"
                  {...register(base)}
                />
                <span className="inline-flex min-w-[1.5rem] justify-center rounded-md bg-muted px-2 py-0.5 text-sm font-semibold tabular-nums text-foreground">
                  {n}
                </span>
              </div>
              <span className="min-w-0 flex-1 text-sm font-normal leading-snug text-foreground">
                {rotulos[n - 1]}
              </span>
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
      const { labels: rowLabels, avisoRotulos } = montarRotulosMultiplaEscolha(
        total,
        p.opcoes ?? [],
        p.codigo,
      );
      if (total < 1) {
        return (
          <p className="text-sm text-destructive pt-2">
            Catálogo incompleto: multipla_total ausente ou inválido para {p.codigo}.
          </p>
        );
      }
      return (
        <>
          {avisoRotulos ? (
            <p
              className="text-sm text-amber-800 dark:text-amber-400 mt-2 rounded-md border border-amber-500/35 bg-amber-500/10 px-3 py-2"
              role="status"
            >
              {avisoRotulos}
            </p>
          ) : null}
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
        </>
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
      const total = perguntas[i]?.multipla_total ?? 0;
      if (total >= 1 && v.length > total) {
        return `Selecione no máximo ${total} opção(ões) antes de seguir.`;
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

    for (let i = 0; i < perguntas.length; i++) {
      const tipo = normalizarTipoPerguntaWizard(perguntas[i]?.tipo);
      if (tipo !== "multipla_escolha" && tipo !== "checklist") continue;
      const total = perguntas[i]?.multipla_total ?? 0;
      const v = respostas[i]?.valor;
      if (total >= 1 && Array.isArray(v) && v.length > total) {
        const cod = perguntas[i]?.codigo ?? "";
        setApiError(`Seleção inválida em «${cod}»: no máximo ${total} opção(ões).`);
        return null;
      }
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
    if (!getAccessToken()) {
      await gerarDiagnosticoLocalmente();
      return;
    }
    await onSubmit();
  };

  /** Valida, persiste em sessionStorage e abre a página de resumo (OTP / login B2B). */
  const gerarDiagnosticoLocalmente = async () => {
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
    setApiError(null);
    router.push("/diagnostico/gravado-local");
  };

  const onSubmit = async () => {
    const payload = await montarPayloadDiagnosticoValidado();
    if (!payload) return;

    if (!getAccessToken()) {
      setApiError("Sessão ausente — use «Gerar diagnóstico» e confirme por e-mail ou entre com conta B2B.");
      return;
    }

    try {
      setIsSubmitting(true);
      setApiError(null);
      await postDiagnostico(payload);
      clearWizardDraft();
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
  const progressBarPercent = progress;
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
              : ultimaPerguntaDoQuestionario && !hasToken
                ? "Gerar diagnóstico"
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
      <div className={cn("w-full min-w-0 space-y-2", step === 3 && "shrink-0")}>
        <div className="flex w-full justify-between gap-4 text-sm text-muted-foreground font-medium">
          <span className="min-w-0 truncate">
            Passo {step} de {TOTAL_STEPS}
          </span>
          <span className="shrink-0 tabular-nums">{Math.round(progressBarPercent)}% Concluído</span>
        </div>
        <Progress value={progressBarPercent} className="w-full" />
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
              : // Passos 1–2: Card padrão usa overflow-hidden — com flex min-h-0 no layout pai,
                // o rodapé (Voltar / Próxima) era cortado. visible permite o fluxo rolar no documento.
                "overflow-visible border-primary/10 shadow-lg",
          )}
        >
        <CardHeader
          className={cn(
            "space-y-1 bg-muted/30 border-b shrink-0",
            step === 3 ? "py-3 md:py-4" : "px-6 pb-4 pt-6 sm:px-6",
          )}
        >
          <CardTitle className={cn("text-primary", step === 3 ? "text-xl md:text-2xl" : "text-2xl")}>
            {step === 1 && "Identificação Inicial"}
            {step === 2 && "Perfil da Empresa"}
            {step === 3 && "Questionário adaptativo (Reforma + ABNT NBR 17301)"}
          </CardTitle>
          <CardDescription className={cn(step === 3 && "text-xs md:text-sm leading-snug")}>
            {step === 1 &&
              "Cadastro da empresa: CNPJ e razão social são obrigatórios (vínculo PJ ao diagnóstico). Responder ao assistente não exige sessão; gravar na API exige login após cadastro B2B. LGPD: consentimento abaixo."}
            {step === 2 &&
              "M01 — Motor adaptativo: porte × regime × setor × UF filtram perguntas (LC 214/2025 art. 5º — previsibilidade). A conclusão persiste na API após autenticação."}
            {step === 3 &&
              "Uma pergunta por tela — Seguir / Voltar. Sem conta B2B: «Gerar diagnóstico» salva e segue para confirmar o e-mail e gravar na nuvem; com login, «Finalizar Diagnóstico» envia direto."}
          </CardDescription>
        </CardHeader>

        <CardContent
          ref={painelPerguntasRef}
          className={cn(
            step === 3
              ? "flex flex-1 flex-col min-h-0 overflow-y-auto overscroll-contain px-4 pt-4 pb-2 md:pb-3 md:px-6"
              : "px-6 pb-4 pt-6 sm:px-6",
          )}
        >
          <form
            className={cn(step === 3 ? "flex flex-col flex-1 min-h-full gap-0" : "space-y-6")}
            onSubmit={(e) => e.preventDefault()}
          >
            {step === 1 && (
              <div className="space-y-4 animate-in fade-in slide-in-from-bottom-4 duration-500">
                <div>
                  <h3 className="text-sm font-semibold text-foreground tracking-tight">
                    Cadastro da empresa
                  </h3>
                  <p className="text-xs text-muted-foreground mt-1">
                    CNPJ (com dígitos verificadores válidos) e razão social conforme Receita Federal.
                  </p>
                </div>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="cnpj">CNPJ *</Label>
                    <Input
                      id="cnpj"
                      placeholder="00.000.000/0000-00"
                      inputMode="numeric"
                      autoComplete="organization"
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
                    M09 — Apenas DDD e número (sem +55). No relatório PDF (WeasyPrint), o bloco de captação de lead
                    mostra apenas e-mail e telefone.
                  </p>
                  <div className="space-y-2 max-w-md pt-2">
                    <Label htmlFor="locale_relatorio">Idioma do relatório PDF</Label>
                    <select
                      id="locale_relatorio"
                      className={cn(
                        "flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm",
                        "ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring",
                      )}
                      {...register("locale_relatorio")}
                    >
                      <option value="pt-BR">Português (Brasil)</option>
                      <option value="en">English (labels; partial PT narrative)</option>
                    </select>
                  </div>
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
                    <Label
                      htmlFor="lgpd"
                      className="block w-full min-w-0 font-normal text-sm leading-relaxed cursor-pointer text-left"
                    >
                      Declaro que li e aceito o tratamento dos dados informados para elaboração do diagnóstico,
                      nos termos da LGPD (Lei 13.709/2018). Consulte a{" "}
                      <Link
                        href="/privacidade"
                        className="text-primary underline underline-offset-2 hover:text-primary/90 inline"
                      >
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
                <p className="text-center text-sm md:text-base text-muted-foreground leading-relaxed pt-3 border-t border-border/60">
                  Em{" "}
                  <strong className="text-foreground font-semibold">cerca de 15 minutos</strong>,
                  identifique lacunas frente à Reforma Tributária do Consumo (EC 132/2023, LC 214/2025) e
                  receba um plano de ação objetivo para sua empresa.
                </p>
              </div>
            )}

            {step === 2 && (
              <div className="space-y-5 animate-in fade-in slide-in-from-bottom-4 duration-500">
                <span className="sr-only" aria-live="polite">
                  {catalogLoading ? "Carregando questionário adaptativo." : ""}
                </span>
                {!getAccessToken() && (
                  <div className="rounded-md border border-border bg-muted/30 px-4 py-3 text-xs text-muted-foreground md:text-sm leading-relaxed">
                    Sem login corporativo você pode concluir o assistente; na última pergunta,{" "}
                    <span className="font-medium text-foreground">Gerar diagnóstico</span> guarda as respostas e abre
                    a etapa seguinte: confirmação do e-mail (código) para gravar na nuvem ou login B2B para o painel
                    consultor.
                  </div>
                )}
                {catalogError && (
                  <div className="rounded-md border border-destructive/30 bg-destructive/10 p-3 text-sm text-destructive">
                    {catalogError}
                  </div>
                )}
                {/* Grid com colunas alinhadas: labels na mesma linha, selects na mesma linha; erros em faixa de altura fixa */}
                <div className="grid grid-cols-1 gap-x-6 gap-y-3 md:grid-cols-2 md:items-start">
                  <div className="flex min-w-0 flex-col gap-2">
                    <Label htmlFor="porte" className="text-foreground">
                      Porte da empresa (faturamento anual) *
                    </Label>
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
                      <option value="micro">Micro — faturamento anual até R$ 360 mil</option>
                      <option value="pequeno">Pequeno — faturamento anual até R$ 4,8 milhões</option>
                      <option value="medio">Médio — faturamento anual até R$ 500 milhões</option>
                      <option value="grande">Grande — faturamento anual acima de R$ 500 milhões</option>
                    </select>
                    <SlotMensagemErroCampo>
                      {errors.empresa?.porte ? errors.empresa.porte.message : null}
                    </SlotMensagemErroCampo>
                  </div>
                  <div className="flex min-w-0 flex-col gap-2">
                    <Label htmlFor="regime" className="text-foreground">
                      Regime tributário *
                    </Label>
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
                    <SlotMensagemErroCampo>
                      {errors.empresa?.regime ? errors.empresa.regime.message : null}
                    </SlotMensagemErroCampo>
                  </div>
                </div>
                <p className="-mt-1 text-xs text-muted-foreground leading-snug md:col-span-2">
                  Porte: classificação por receita bruta dos últimos 12 meses (autodeclarada — não substitui
                  enquadramento legal).
                </p>

                <div className="grid grid-cols-1 gap-x-6 gap-y-3 md:grid-cols-2 md:items-start">
                  <div className="flex min-w-0 flex-col gap-2">
                    <Label htmlFor="setor_macro" className="text-foreground">
                      Setor macro *
                    </Label>
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
                    <SlotMensagemErroCampo>
                      {errors.empresa?.setor_macro ? errors.empresa.setor_macro.message : null}
                    </SlotMensagemErroCampo>
                  </div>
                  <div className="flex min-w-0 flex-col gap-2">
                    <Label htmlFor="uf" className="text-foreground">
                      UF *
                    </Label>
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
                    <SlotMensagemErroCampo>
                      {errors.empresa?.uf ? errors.empresa.uf.message : null}
                    </SlotMensagemErroCampo>
                  </div>
                </div>

                <div className="space-y-2 border-t border-border/60 pt-5">
                  <Label htmlFor="cnae_principal">CNAE principal (7 dígitos) *</Label>
                  <Controller
                    name="empresa.cnae_principal"
                    control={control}
                    render={({ field, fieldState }) => (
                      <div ref={cnaeAnchorRef} className="relative z-20 w-full min-w-0">
                        <Input
                          id="cnae_principal"
                          placeholder="1234567 ou busque por texto (ex.: varejo)"
                          autoComplete="off"
                          aria-autocomplete="list"
                          aria-expanded={cnaeListaAberta && cnaeSugestoes.length > 0}
                          aria-controls="cnae-sugestoes-wizard-listbox"
                          value={cnaeBuscaTexto}
                          onChange={(e) => {
                            const v = e.target.value;
                            cnaeBuscaTextoRef.current = v;
                            setCnaeBuscaTexto(v);
                            const temLetras = /[a-zA-ZÀ-ÿ]/i.test(v);
                            const soDigitos = v.replace(/\D/g, "").slice(0, 7);
                            if (temLetras) {
                              field.onChange("");
                            } else {
                              field.onChange(soDigitos);
                            }
                          }}
                          onFocus={() => {
                            if (cnaeBlurFecharTimerRef.current != null) {
                              clearTimeout(cnaeBlurFecharTimerRef.current);
                              cnaeBlurFecharTimerRef.current = null;
                            }
                            setCnaeListaAberta(true);
                          }}
                          onBlur={() => {
                            field.onBlur();
                            const v = cnaeBuscaTextoRef.current;
                            const d = v.replace(/\D/g, "").slice(0, 7);
                            const temLetras = /[a-zA-ZÀ-ÿ]/i.test(v);
                            if (!temLetras && d.length === 7) {
                              field.onChange(d);
                              cnaeBuscaTextoRef.current = d;
                              setCnaeBuscaTexto(d);
                              clearErrors("empresa.cnae_principal");
                            } else if (temLetras) {
                              field.onChange("");
                              /* Mantém o texto de busca para continuar a pesquisa ou clicar na lista. */
                            } else if (!temLetras && d.length > 0 && d.length < 7) {
                              field.onChange(d);
                              cnaeBuscaTextoRef.current = d;
                              setCnaeBuscaTexto(d);
                            } else if (!temLetras && d.length === 0) {
                              field.onChange("");
                              cnaeBuscaTextoRef.current = "";
                              setCnaeBuscaTexto("");
                            }
                            cnaeBlurFecharTimerRef.current = setTimeout(() => {
                              setCnaeListaAberta(false);
                            }, 200);
                          }}
                          className={fieldState.error ? "border-destructive" : ""}
                        />
                        {typeof document !== "undefined" &&
                        cnaeListaAberta &&
                        cnaeSugestoes.length > 0 &&
                        cnaePopoverBox != null
                          ? createPortal(
                              <ul
                                id="cnae-sugestoes-wizard-listbox"
                                role="listbox"
                                data-testid="cnae-sugestoes-lista"
                                style={{
                                  position: "fixed",
                                  top: cnaePopoverBox.top,
                                  left: cnaePopoverBox.left,
                                  width: cnaePopoverBox.width,
                                  boxSizing: "border-box",
                                }}
                                className={cn(
                                  "z-[300] max-h-[min(18rem,50vh)] overflow-y-auto overscroll-contain rounded-md border",
                                  "border-border bg-popover p-0 text-popover-foreground shadow-lg",
                                )}
                              >
                                {cnaeSugestoes.map((s) => (
                                  <li
                                    key={s.subclasse_id}
                                    role="presentation"
                                    className="border-b border-border/40 last:border-b-0"
                                  >
                                    <button
                                      type="button"
                                      role="option"
                                      aria-selected={false}
                                      className={cn(
                                        "flex w-full min-w-0 flex-col gap-0.5 px-3 py-2.5 text-left text-sm transition-colors",
                                        "hover:bg-accent hover:text-accent-foreground focus-visible:bg-accent focus-visible:outline-none",
                                      )}
                                      onMouseDown={(e) => {
                                        e.preventDefault();
                                      }}
                                      onClick={() => {
                                        field.onChange(s.subclasse_id);
                                        cnaeBuscaTextoRef.current = s.subclasse_id;
                                        setCnaeBuscaTexto(s.subclasse_id);
                                        clearErrors("empresa.cnae_principal");
                                        setCnaeListaAberta(false);
                                      }}
                                    >
                                      <span className="shrink-0 font-mono text-xs font-semibold tabular-nums text-foreground">
                                        {s.subclasse_id}
                                      </span>
                                      <span className="min-w-0 whitespace-normal break-words text-xs leading-snug text-muted-foreground [overflow-wrap:anywhere]">
                                        {s.descricao}
                                      </span>
                                    </button>
                                  </li>
                                ))}
                              </ul>,
                              document.body,
                            )
                          : null}
                      </div>
                    )}
                  />
                  <p className="text-xs text-muted-foreground leading-snug">
                    Digite pelo menos 2 caracteres (início do código de 7 dígitos ou parte da descrição da
                    atividade). As sugestões aparecem <strong className="font-medium text-foreground">abaixo do campo</strong>,
                    com rolagem e texto completo. Tabela oficial{" "}
                    <abbr title="Classificação Nacional de Atividades Econômicas">CNAE</abbr> 2.3 (CONCLA/IBGE).
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
                        Framework ABNT (guia)
                      </Link>
                      <Link href="/metodologia" className="text-primary underline font-medium">
                        Metodologia e pesos
                      </Link>
                    </div>
                  </details>
                </div>
                {totalPerguntas > 0 && indicePerguntaAtual < totalPerguntas && (
                  <div
                    key={perguntas[indicePerguntaAtual].id}
                    data-testid="wizard-pergunta-atual"
                    className="mx-auto flex min-h-0 w-full max-w-xl flex-col justify-start space-y-3 rounded-lg border bg-muted/20 p-4 sm:p-5"
                  >
                    <p
                      role="status"
                      aria-live="polite"
                      aria-atomic="true"
                      className="text-sm font-medium text-muted-foreground"
                    >
                      Pergunta {indicePerguntaAtual + 1} de {totalPerguntas}
                    </p>
                    <div className="flex items-start gap-2">
                      <Label className="text-base font-semibold text-foreground/90 leading-tight block flex-1 min-w-0">
                        {indicePerguntaAtual + 1}. {perguntas[indicePerguntaAtual].texto}{" "}
                        <span className="text-muted-foreground font-normal text-xs">
                          ({perguntas[indicePerguntaAtual].codigo})
                        </span>
                      </Label>
                      {perguntas[indicePerguntaAtual].base_legal ? (
                        <Tooltip>
                          <TooltipTrigger asChild>
                            <button
                              type="button"
                              className="mt-0.5 shrink-0 rounded-md p-1 text-muted-foreground transition-colors hover:bg-muted hover:text-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                              aria-label={`Base legal: ${perguntas[indicePerguntaAtual].base_legal}`}
                            >
                              <Info className="h-5 w-5" aria-hidden />
                            </button>
                          </TooltipTrigger>
                          <TooltipContent side="left" className="max-w-xs text-left leading-snug">
                            <span className="font-medium text-foreground">Base legal (referência)</span>
                            <span className="mt-1 block text-muted-foreground">
                              {perguntas[indicePerguntaAtual].base_legal}
                            </span>
                          </TooltipContent>
                        </Tooltip>
                      ) : null}
                    </div>
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
          <CardFooter className="flex w-full min-w-0 shrink-0 flex-wrap justify-between gap-3 border-t bg-muted/10 p-6 pb-[max(1.5rem,env(safe-area-inset-bottom,0px))] sm:pb-6">
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
