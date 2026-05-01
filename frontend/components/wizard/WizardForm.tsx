"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
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

import { DiagnosticoPayloadSchema, DiagnosticoPayload, UFS_BR } from "@/lib/schemas/wizard";
import { postDiagnostico } from "@/lib/api/diagnostico";
import { getAccessToken, getApiUrl } from "@/lib/api/config";
import { postValidarAncora } from "@/lib/api/normativa";
import { fetchQuestionarioAdaptativo, type PerguntaCatalogo } from "@/lib/api/questionario";

const TOTAL_STEPS = 3;

const NORMA_WIZARD_ATIVO =
  typeof process.env.NEXT_PUBLIC_WIZARD_NORMATIVA === "string" &&
  process.env.NEXT_PUBLIC_WIZARD_NORMATIVA === "true";

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

  useEffect(() => {
    setTokenChecked(true);
  }, []);

  const form = useForm<DiagnosticoPayload>({
    resolver: zodResolver(DiagnosticoPayloadSchema),
    defaultValues: {
      empresa: {
        cnpj: "",
        razao_social: "",
        porte: "medio",
        regime: "lucro_real",
        cnae_principal: "",
        uf: "SP",
        setor_macro: "servicos",
      },
      respondente: {
        nome: "",
        email: "",
        telefone: undefined,
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
    formState: { errors },
    getValues,
    reset,
  } = form;

  const valorInicialPorTipo = (tipo: string): string | number | string[] => {
    if (tipo === "multipla_escolha" || tipo === "checklist") return [];
    return "";
  };

  const renderPerguntaInput = (p: PerguntaCatalogo, index: number) => {
    const base = `respostas.${index}.valor` as const;
    const rowClass =
      "flex items-center space-x-3 cursor-pointer p-3 rounded border bg-background hover:bg-muted/50 transition-colors";

    if (p.tipo === "escala_1_5") {
      return (
        <div className="flex flex-col space-y-2 pt-2">
          {[1, 2, 3, 4, 5].map((n) => (
            <Label key={n} className={rowClass}>
              <input
                type="radio"
                value={String(n)}
                className="w-4 h-4 text-primary focus:ring-primary"
                {...register(base)}
              />
              <span className="font-normal text-sm">
                {n} - escala (1 menor a 5 maior aderencia)
              </span>
            </Label>
          ))}
        </div>
      );
    }

    if (p.tipo === "binaria") {
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

    if (p.tipo === "numerica") {
      return (
        <Input
          type="number"
          min={0}
          max={100}
          step={1}
          placeholder="Informe um numero de 0 a 100"
          className="max-w-xs mt-2"
          {...register(base)}
        />
      );
    }

    if (p.tipo === "multipla_escolha" || p.tipo === "checklist") {
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
    let fieldsToValidate: (keyof DiagnosticoPayload | string)[] = [];
    if (step === 1) {
      fieldsToValidate = [
        "empresa.cnpj",
        "empresa.razao_social",
        "respondente.nome",
        "respondente.email",
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

  const onSubmit = async () => {
    const isValid = await trigger();
    if (!isValid) return;

    const raw = getValues();
    const respostas = raw.respostas;

    const incompleto = respostas.some((r, i) => {
      const tipo = perguntas[i]?.tipo;
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
      return;
    }

    const respostasNorm = respostas.map((r, i) => {
      const tipo = perguntas[i]?.tipo;
      const v = r.valor;
      if (tipo === "numerica") {
        const n = typeof v === "string" ? parseFloat(v) : Number(v);
        return { ...r, valor: n };
      }
      return r;
    });

    for (let i = 0; i < perguntas.length; i++) {
      if (perguntas[i]?.tipo === "numerica") {
        const v = respostasNorm[i].valor as number;
        if (!Number.isFinite(v) || v < 0 || v > 100) {
          setApiError("Valores numericos devem estar entre 0 e 100.");
          return;
        }
      }
    }

    try {
      setIsSubmitting(true);
      setApiError(null);
      await postDiagnostico({ ...raw, respostas: respostasNorm });
      router.push("/sucesso");
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : "Ocorreu um erro ao enviar o diagnóstico.";
      setApiError(msg);
    } finally {
      setIsSubmitting(false);
    }
  };

  const progress = (step / TOTAL_STEPS) * 100;
  const hasToken = tokenChecked && !!getAccessToken();

  return (
    <div className="w-full max-w-3xl mx-auto space-y-6">
      <div className="space-y-2">
        <div className="flex justify-between text-sm text-muted-foreground font-medium">
          <span>
            Passo {step} de {TOTAL_STEPS}
          </span>
          <span>{Math.round(progress)}% Concluído</span>
        </div>
        <Progress value={progress} className="h-2" />
      </div>

      <Card className="shadow-lg border-primary/10">
        <CardHeader className="space-y-1 bg-muted/30 border-b">
          <CardTitle className="text-2xl text-primary">
            {step === 1 && "Identificação Inicial"}
            {step === 2 && "Perfil da Empresa"}
            {step === 3 && "Questionário adaptativo (Reforma + ABNT NBR 17301)"}
          </CardTitle>
          <CardDescription>
            {step === 1 &&
              "M09 — Captura para lead magnet B2B: faça login após esta etapa para enviar respostas. LGPD: consentimento abaixo."}
            {step === 2 &&
              "M01 — Motor adaptativo: porte × regime × setor × UF filtram perguntas exibidas (LC 214/2025 art. 5º — previsibilidade)."}
            {step === 3 &&
              "Respostas sinceras geram score e relatório. Envio exige login B2B (JWT). Transparência: manifesto público na API (/diagnosticos/manifesto-pesos)."}
          </CardDescription>
        </CardHeader>

        <CardContent className="pt-6">
          <form className="space-y-6" onSubmit={(e) => e.preventDefault()}>
            {step === 1 && (
              <div className="space-y-4 animate-in fade-in slide-in-from-bottom-4 duration-500">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="cnpj">CNPJ *</Label>
                    <Input
                      id="cnpj"
                      placeholder="00.000.000/0000-00"
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
                  <Input
                    id="telefone"
                    placeholder="DDI + número (uso operacional)"
                    {...register("respondente.telefone")}
                    aria-describedby="hint-telefone"
                  />
                  <p id="hint-telefone" className="text-xs text-muted-foreground">
                    M09 — Facilita recontato pela assessoria B2B; não obrigatório na API MVP.
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
                {catalogError && (
                  <div className="p-3 text-sm text-destructive border border-destructive/30 rounded-md bg-destructive/10">
                    {catalogError}
                  </div>
                )}
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="porte">Porte da Empresa *</Label>
                    <select
                      id="porte"
                      className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                      {...register("empresa.porte")}
                    >
                      <option value="micro">Micro (Até R$ 360 mil)</option>
                      <option value="pequeno">Pequeno (Até R$ 4,8 mi)</option>
                      <option value="medio">Médio (Até R$ 500 mi)</option>
                      <option value="grande">Grande (Até R$ 5 bi)</option>
                      <option value="enterprise">Enterprise (Acima de R$ 5 bi)</option>
                    </select>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="regime">Regime Tributário *</Label>
                    <select
                      id="regime"
                      className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                      {...register("empresa.regime")}
                    >
                      <option value="simples_nacional">Simples Nacional</option>
                      <option value="lucro_presumido">Lucro Presumido</option>
                      <option value="lucro_real">Lucro Real</option>
                      <option value="mei">MEI</option>
                    </select>
                  </div>
                </div>

                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="setor_macro">Setor Macro *</Label>
                    <select
                      id="setor_macro"
                      className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                      {...register("empresa.setor_macro")}
                    >
                      <option value="comercio">Comércio</option>
                      <option value="industria">Indústria</option>
                      <option value="servicos">Serviços</option>
                      <option value="agro">Agro</option>
                      <option value="consumo">Consumo</option>
                    </select>
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="uf">UF *</Label>
                    <select
                      id="uf"
                      className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring"
                      {...register("empresa.uf")}
                    >
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
                  <Input
                    id="cnae_principal"
                    placeholder="1234567"
                    {...register("empresa.cnae_principal")}
                    className={errors.empresa?.cnae_principal ? "border-destructive" : ""}
                  />
                  {errors.empresa?.cnae_principal && (
                    <p className="text-sm text-destructive">{errors.empresa.cnae_principal.message}</p>
                  )}
                </div>
              </div>
            )}

                {step === 3 && (
              <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
                {NORMA_WIZARD_ATIVO && (
                  <div className="rounded-lg border bg-muted/10 p-4 space-y-3">
                    <p className="text-sm font-semibold text-foreground">
                      P8 — Checagem rápida de âncora normativa (Lexiq / guardrail)
                    </p>
                    <p className="text-xs text-muted-foreground">
                      Cole um trecho de justificativa; o motor verifica se há referência reconhecível
                      (ex.: LC 214/2025, EC 132/2023). Endpoint público:{" "}
                      <span className="font-mono">POST /normativa/validar-ancora</span>.
                    </p>
                    <textarea
                      value={normaTexto}
                      onChange={(e) => setNormaTexto(e.target.value)}
                      rows={4}
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
                {!hasToken && (
                  <div className="p-4 border border-amber-500/40 bg-amber-500/10 rounded-md text-sm">
                    Para enviar o diagnóstico você precisa estar autenticado.{" "}
                    <Link href="/login" className="text-primary font-medium underline">
                      Fazer login
                    </Link>
                  </div>
                )}
                {apiError && (
                  <div className="p-4 bg-destructive/10 border border-destructive/20 text-destructive rounded-md text-sm">
                    {apiError}
                  </div>
                )}
                <p className="text-sm text-muted-foreground">
                  <Link href="/abnt-framework" className="text-primary underline font-medium">
                    M11 — PDCA e pilares ABNT (guia rápido)
                  </Link>
                  {" · "}
                  <a
                    href={`${getApiUrl().replace(/\/$/, "")}/diagnosticos/manifesto-pesos`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-primary underline font-medium"
                  >
                    Manifesto de pesos (JSON)
                  </a>
                  {" · "}
                  <a
                    href={`${getApiUrl().replace(/\/$/, "")}/diagnosticos/metodologia`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="text-primary underline font-medium"
                  >
                    Metodologia (JSON)
                  </a>
                </p>
                {perguntas.map((p, qIndex) => (
                  <div key={p.id} className="space-y-3 bg-muted/20 p-4 rounded-lg border">
                    <Label className="text-base font-semibold text-foreground/90 leading-tight">
                      {qIndex + 1}. {p.texto}{" "}
                      <span className="text-muted-foreground font-normal text-xs">({p.codigo})</span>
                    </Label>
                    {p.base_legal && (
                      <p className="text-xs text-muted-foreground">
                        Base legal (referência): {p.base_legal}
                      </p>
                    )}
                    {renderPerguntaInput(p, qIndex)}
                  </div>
                ))}
              </div>
            )}
          </form>
        </CardContent>

        <CardFooter className="flex justify-between border-t p-6 bg-muted/10">
          <Button type="button" variant="outline" onClick={prevStep} disabled={step === 1 || isSubmitting}>
            Voltar
          </Button>

          {step < TOTAL_STEPS ? (
            <Button type="button" onClick={nextStep} disabled={catalogLoading}>
              {catalogLoading ? "Carregando perguntas…" : "Próxima Etapa"}
            </Button>
          ) : (
            <Button
              type="button"
              onClick={onSubmit}
              disabled={isSubmitting || !hasToken}
              className="bg-accent text-accent-foreground hover:bg-accent/90"
            >
              {isSubmitting ? "Enviando…" : "Finalizar Diagnóstico"}
            </Button>
          )}
        </CardFooter>
      </Card>
    </div>
  );
}
