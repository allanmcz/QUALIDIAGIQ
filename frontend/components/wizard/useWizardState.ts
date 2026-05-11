"use client";

import { useCallback, useEffect, useLayoutEffect, useRef, useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { useRouter } from "next/navigation";

import {
  DiagnosticoPayloadSchema,
  type DiagnosticoPayload,
  type DiagnosticoPayloadFormInput,
} from "@/lib/schemas/wizard";
import { cn } from "@/lib/utils";
import {
  ADMIN_EMAIL_STORAGE_KEY,
  ADMIN_NOME_STORAGE_KEY,
  ADMIN_PERFIL_CONTA_STORAGE_KEY,
  getAccessToken,
} from "@/lib/api/config";
import { postConsultarCnpjAutenticado, rotuloFonteConsultaCnpj } from "@/lib/api/consulta_cnpj";
import { postDiagnostico } from "@/lib/api/diagnostico";
import { aplicarCanonicoNoFormularioEmpresa } from "@/lib/cnpj/canonical_merge";
import {
  postRascunhoDiagnosticoSelfService,
  postVincularRascunhoContaPlataforma,
} from "@/lib/api/self_service_diagnostico";
import { fetchQuestionarioAdaptativo, type PerguntaCatalogo } from "@/lib/api/questionario";
import {
  clearPendingDiagnosticoFromStorage,
  hasPendingDiagnosticoInBrowser,
  loadPendingDiagnosticoFromStorage,
  parsePendingDiagnosticoFromStorage,
} from "@/lib/wizard/pending_diagnostico";
import {
  clearRascunhoResgateToken,
  loadRascunhoResgateToken,
} from "@/lib/wizard/rascunho_resgate_token";
import {
  clearWizardDraft,
  loadWizardDraft,
  saveWizardDraft,
  wizardDraftHasProgress,
  type WizardDraftV1,
} from "@/lib/wizard/wizard_draft";
import { fetchCnaeSubclasses, type CnaeSubclasseItem } from "@/lib/api/cnae";
import { DEFAULT_WIZARD_FORM_VALUES, TOTAL_STEPS } from "@/lib/wizard/wizardFormDefaults";
import {
  normalizarTipoPerguntaWizard,
  valorInicialPorTipoPergunta,
} from "@/lib/wizard/perguntaTipo";

/**
 * Estado e efeitos do assistente de diagnóstico (react-hook-form + passos + rascunho).
 *
 * Camada: hook — sem JSX (W2 roadmap).
 */
export function useWizardState() {
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
  /** Query `empresa_cnpj` / `empresa_razao_social` — aplicar pré-preenchimento uma vez por ciclo de overlay. */
  const wizardQueryEmpresaPrefillAppliedRef = useRef(false);
  /** Após ler/restaurar cache local (localStorage) — só então passamos a persistir alterações. */
  const [draftHydrated, setDraftHydrated] = useState(false);
  /** Há rascunho e/ou diagnóstico pendente — pergunta continuar vs reiniciar antes de hidratar. */
  const [cacheResumePrompt, setCacheResumePrompt] = useState<{
    hasDraft: boolean;
    hasPending: boolean;
  } | null>(null);
  /** Pré-consulta CNPJ (`POST /referencia/cnpj/consulta_cnpj`) com sessão na plataforma. */
  const [consultaCnpjLoading, setConsultaCnpjLoading] = useState(false);
  const [consultaCnpjFeedback, setConsultaCnpjFeedback] = useState<string | null>(null);
  const [forceRefreshConsultaCnpjUi, setForceRefreshConsultaCnpjUi] = useState(false);

  useEffect(() => {
    setTokenChecked(true);
  }, []);

  useEffect(() => {
    if (step !== 3) return;
    painelPerguntasRef.current?.scrollTo({ top: 0, behavior: "auto" });
  }, [step, indicePerguntaAtual]);

  /**
   * Após login com `redirect=/wizard`: vincula rascunho (token) ou envia payload legado em localStorage.
   */
  useEffect(() => {
    if (!tokenChecked) return;
    const tokenJwt = getAccessToken();
    if (!tokenJwt) return;

    const rt = loadRascunhoResgateToken();
    if (rt) {
      let cancelled = false;
      void (async () => {
        try {
          setIsSubmitting(true);
          setApiError(null);
          await postVincularRascunhoContaPlataforma(rt, tokenJwt);
          clearRascunhoResgateToken();
          clearPendingDiagnosticoFromStorage();
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
    }

    const pendingResult = parsePendingDiagnosticoFromStorage();
    if (!pendingResult.ok) {
      if (pendingResult.reason !== "missing") {
        setApiError(
          "Os dados do diagnóstico guardados neste navegador estão inválidos ou desactualizados. " +
            "Volte ao assistente (/wizard), complete o passo 1 e envie novamente — ou limpe o cache do diagnóstico no diálogo de retomada.",
        );
      }
      return;
    }
    const payload = pendingResult.data;
    let cancelled = false;
    void (async () => {
      try {
        setIsSubmitting(true);
        setApiError(null);
        await postDiagnostico(payload);
        clearPendingDiagnosticoFromStorage();
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
    defaultValues: DEFAULT_WIZARD_FORM_VALUES,
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
    setValue,
  } = form;

  /** Com JWT ativo, preenche nome/e-mail do respondente a partir do login (sem sobrescrever rascunho já preenchido). */
  const aplicarRespondenteDaConta = useCallback(() => {
    if (typeof window === "undefined") return;
    if (!getAccessToken()) return;
    const nomeLs = window.localStorage.getItem(ADMIN_NOME_STORAGE_KEY)?.trim() ?? "";
    const emailLs = window.localStorage.getItem(ADMIN_EMAIL_STORAGE_KEY)?.trim() ?? "";
    if (!nomeLs && !emailLs) return;
    const curNome = (getValues("respondente.nome") ?? "").trim();
    const curEmail = (getValues("respondente.email") ?? "").trim();
    if (!curNome && nomeLs) {
      setValue("respondente.nome", nomeLs, { shouldDirty: true, shouldValidate: false });
    }
    if (!curEmail && emailLs) {
      setValue("respondente.email", emailLs, { shouldDirty: true, shouldValidate: false });
    }
  }, [getValues, setValue]);

  const consultarCnpjNoWizard = useCallback(async () => {
    if (!getAccessToken()) {
      setConsultaCnpjFeedback(
        "Para buscar dados públicos pelo CNPJ, inicie sessão na plataforma (este passo não substitui rascunho + OTP).",
      );
      return;
    }
    const okCnpj = await trigger("empresa.cnpj");
    if (!okCnpj) return;

    const cnpj14 = String(getValues("empresa.cnpj") ?? "").replace(/\D/g, "");
    if (cnpj14.length !== 14) {
      setConsultaCnpjFeedback("Informe um CNPJ com 14 dígitos e DV válidos antes de buscar.");
      return;
    }

    setConsultaCnpjLoading(true);
    setConsultaCnpjFeedback(null);
    try {
      const data = await postConsultarCnpjAutenticado({
        cnpj14,
        forceRefresh: forceRefreshConsultaCnpjUi,
      });
      aplicarCanonicoNoFormularioEmpresa(data.canonico, setValue);
      await trigger([
        "empresa.razao_social",
        "empresa.porte",
        "empresa.regime",
        "empresa.cnae_principal",
        "empresa.uf",
        "empresa.setor_macro",
      ]);
      setConsultaCnpjFeedback(
        `Campos da empresa atualizados (fonte: ${rotuloFonteConsultaCnpj(data.fonte)}). Verifique o perfil no passo seguinte.`,
      );
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Falha na consulta CNPJ.";
      setConsultaCnpjFeedback(msg);
    } finally {
      setConsultaCnpjLoading(false);
    }
  }, [trigger, getValues, setValue, forceRefreshConsultaCnpjUi]);

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
    const blurTimerRef = cnaeBlurFecharTimerRef;
    return () => {
      const blurTimerId = blurTimerRef.current;
      if (blurTimerId != null) clearTimeout(blurTimerId);
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

  /**
   * Aplica rascunho já validado (passos 1–2 ou passo 3 com catálogo da API).
   */
  const aplicarRascunhoWizard = useCallback(
    async (draft: WizardDraftV1) => {
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
      setCatalogError(null);
      try {
        const q = await fetchQuestionarioAdaptativo(draft.form.empresa);
        const respostasSalvas = Array.isArray(draft.form.respostas) ? draft.form.respostas : [];
        const map = new Map(respostasSalvas.map((r) => [r.pergunta_id, r.valor]));
        const merged = q.perguntas.map((pg) => ({
          pergunta_id: pg.id,
          valor: map.has(pg.id) ? map.get(pg.id)! : valorInicialPorTipoPergunta(pg.tipo),
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
        setPerguntas([]);
        setStep(2);
        reset({
          ...draft.form,
          respostas: [],
        });
        setIndicePerguntaAtual(0);
      } finally {
        setCatalogLoading(false);
      }
    },
    [reset],
  );

  const handleCacheContinuar = useCallback(() => {
    setCacheResumePrompt(null);
    skipPersistRef.current = true;
    void (async () => {
      try {
        const draft = loadWizardDraft();
        const temRascunho = !!(draft && wizardDraftHasProgress(draft));
        if (temRascunho && draft) {
          await aplicarRascunhoWizard(draft);
        } else if (!getAccessToken() && loadPendingDiagnosticoFromStorage()) {
          router.push("/diagnostico/confirmar-gravacao");
        }
      } finally {
        skipPersistRef.current = false;
        setDraftHydrated(true);
      }
    })();
  }, [aplicarRascunhoWizard, router]);

  const handleCacheReiniciar = useCallback(() => {
    clearWizardDraft();
    clearPendingDiagnosticoFromStorage();
    reset({ ...DEFAULT_WIZARD_FORM_VALUES });
    setStep(1);
    setIndicePerguntaAtual(0);
    setPerguntas([]);
    setCatalogError(null);
    setApiError(null);
    setCacheResumePrompt(null);
    skipPersistRef.current = false;
    wizardQueryEmpresaPrefillAppliedRef.current = false;
    setDraftHydrated(true);
    aplicarRespondenteDaConta();
  }, [reset, aplicarRespondenteDaConta]);

  /**
   * Na abertura: se há JWT + pendente de POST, não restaura rascunho (fluxo automático existente).
   * Se há rascunho com progresso e/ou diagnóstico pendente sem sessão, pergunta antes de hidratar.
   */
  useEffect(() => {
    if (typeof window === "undefined") {
      setDraftHydrated(true);
      return;
    }

    const skipRestore =
      !!getAccessToken() && (hasPendingDiagnosticoInBrowser() || !!loadRascunhoResgateToken());

    if (skipRestore) {
      setDraftHydrated(true);
      return;
    }

    skipPersistRef.current = true;

    let draft = loadWizardDraft();
    if (draft && !wizardDraftHasProgress(draft)) {
      clearWizardDraft();
      draft = null;
    }

    const pendenteOk =
      !getAccessToken() ? loadPendingDiagnosticoFromStorage() : null;
    const hasDraft = !!(draft && wizardDraftHasProgress(draft));
    const hasPending = pendenteOk != null;

    if (!hasDraft && !hasPending) {
      skipPersistRef.current = false;
      setDraftHydrated(true);
      return;
    }

    setCacheResumePrompt({ hasDraft, hasPending });
  }, []);

  useEffect(() => {
    if (!draftHydrated) return;
    aplicarRespondenteDaConta();
  }, [draftHydrated, aplicarRespondenteDaConta]);

  /** Painel — `/wizard?empresa_cnpj=&empresa_razao_social=` preenche passo 1 se campos ainda vazios (ADR-013). */
  useEffect(() => {
    if (!draftHydrated || cacheResumePrompt !== null) return;
    if (wizardQueryEmpresaPrefillAppliedRef.current) return;
    if (typeof window === "undefined") return;

    const sp = new URLSearchParams(window.location.search);
    const cnpjQ = sp.get("empresa_cnpj")?.replace(/\D/g, "") ?? "";
    const razaoQ = sp.get("empresa_razao_social")?.trim() ?? "";
    if (cnpjQ.length !== 14 && razaoQ.length < 3) return;

    wizardQueryEmpresaPrefillAppliedRef.current = true;

    const curCnpj = (getValues("empresa.cnpj") ?? "").replace(/\D/g, "");
    const curRazao = (getValues("empresa.razao_social") ?? "").trim();

    if (cnpjQ.length === 14 && curCnpj === "") {
      setValue("empresa.cnpj", cnpjQ, { shouldDirty: false, shouldValidate: false });
    }
    if (razaoQ.length >= 3 && curRazao === "") {
      setValue("empresa.razao_social", razaoQ, { shouldDirty: false, shouldValidate: false });
    }
  }, [draftHydrated, cacheResumePrompt, getValues, setValue]);

  /** Persiste rascunho com debounce — mesma origem que «Voltar ao diagnóstico» na política de privacidade. */
  useEffect(() => {
    if (!draftHydrated) return;

    /** DOM retorna handle numérico; tipagem Node (`Timeout`) conflita em builds Next — usar number. */
    let timeout: number | undefined;

    const persist = () => {
      if (skipPersistRef.current) return;
      if (typeof window === "undefined") return;
      if (getAccessToken() && (hasPendingDiagnosticoInBrowser() || loadRascunhoResgateToken())) return;

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
      if (getAccessToken() && (hasPendingDiagnosticoInBrowser() || loadRascunhoResgateToken())) return;
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
            valor: valorInicialPorTipoPergunta(pg.tipo),
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

  /** Valida e grava rascunho na API (Postgres); redireciona para confirmação por OTP ou conta na plataforma. */
  const gerarDiagnosticoLocalmente = async () => {
    const payload = await montarPayloadDiagnosticoValidado();
    if (!payload) return;
    setApiError(null);
    setIsSubmitting(true);
    try {
      const { resgate_token } = await postRascunhoDiagnosticoSelfService(payload);
      clearPendingDiagnosticoFromStorage();
      clearWizardDraft();
      router.push(`/diagnostico/confirmar-gravacao#${encodeURIComponent(resgate_token)}`);
    } catch (err: unknown) {
      const msg =
        err instanceof Error ? err.message : "Falha ao gravar o rascunho na API. Tente novamente.";
      setApiError(msg);
    } finally {
      setIsSubmitting(false);
    }
  };

  const onSubmit = async () => {
    const payload = await montarPayloadDiagnosticoValidado();
    if (!payload) return;

    if (!getAccessToken()) {
      setApiError(
        "Sessão ausente — use «Gerar diagnóstico» e confirme por e-mail ou entre com a sua conta na plataforma.",
      );
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

  return {
    router,
    step,
    setStep,
    isSubmitting,
    catalogLoading,
    catalogError,
    perguntas,
    apiError,
    tokenChecked,
    normaTexto,
    setNormaTexto,
    normaFeedback,
    setNormaFeedback,
    normaCarregando,
    setNormaCarregando,
    indicePerguntaAtual,
    setIndicePerguntaAtual,
    painelPerguntasRef,
    draftHydrated,
    cacheResumePrompt,
    register,
    control,
    trigger,
    watch,
    clearErrors,
    errors,
    getValues,
    reset,
    setValue,
    cnaeSugestoes,
    setCnaeSugestoes,
    cnaeBuscaTexto,
    setCnaeBuscaTexto,
    cnaeBuscaTextoRef,
    cnaeListaAberta,
    setCnaeListaAberta,
    cnaeBlurFecharTimerRef,
    cnaeAnchorRef,
    cnaePopoverBox,
    empresaPerfil,
    selectPerfilVazio,
    classSelectPerfil,
    handleCacheContinuar,
    handleCacheReiniciar,
    nextStep,
    prevStep,
    voltarWizard,
    montarPayloadDiagnosticoValidado,
    seguirOuFinalizarQuestionario,
    gerarDiagnosticoLocalmente,
    onSubmit,
    totalPerguntas,
    progressBarPercent,
    hasToken,
    ultimaPerguntaDoQuestionario,
    TOTAL_STEPS,
    consultaCnpjLoading,
    consultaCnpjFeedback,
    consultarCnpjNoWizard,
    forceRefreshConsultaCnpjUi,
    setForceRefreshConsultaCnpjUi,
  };
}
