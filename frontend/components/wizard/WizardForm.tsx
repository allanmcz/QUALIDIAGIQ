"use client";

import { useState } from "react";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { useRouter } from "next/navigation";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Progress } from "@/components/ui/progress";

import { DiagnosticoPayloadSchema, DiagnosticoPayload } from "@/lib/schemas/wizard";
import { postDiagnostico } from "@/lib/api/diagnostico";

const TOTAL_STEPS = 3;

// Mock questions according to ABNT NBR 17301
const MOCK_QUESTIONS = [
  {
    id: "11111111-1111-4111-a111-111111111111",
    label: "Sua empresa possui um departamento ou pessoa exclusivamente dedicada ao Compliance Tributário?",
    options: [
      { label: "Não possui", value: "1" },
      { label: "Possui, mas divide com outras tarefas", value: "3" },
      { label: "Sim, equipe/pessoa exclusiva", value: "5" }
    ]
  },
  {
    id: "22222222-2222-4222-a222-222222222222",
    label: "Como é feita a apuração dos tributos hoje?",
    options: [
      { label: "Totalmente manual (Planilhas)", value: "1" },
      { label: "Sistemas básicos com muita intervenção manual", value: "3" },
      { label: "ERP integrado e automatizado", value: "5" }
    ]
  },
  {
    id: "33333333-3333-4333-a333-333333333333",
    label: "A empresa já iniciou o mapeamento dos impactos da EC 132/2023 (Reforma Tributária)?",
    options: [
      { label: "Não iniciamos", value: "1" },
      { label: "Em fase de estudo preliminar", value: "3" },
      { label: "Sim, já temos um plano de transição", value: "5" }
    ]
  }
];

export function WizardForm() {
  const router = useRouter();
  const [step, setStep] = useState(1);
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [apiError, setApiError] = useState<string | null>(null);

  const form = useForm<DiagnosticoPayload>({
    resolver: zodResolver(DiagnosticoPayloadSchema),
    defaultValues: {
      empresa: {
        cnpj: "",
        razao_social: "",
        porte: "medio",
        regime: "lucro_real",
        cnae_principal: "",
        uf: "",
        setor_macro: "servicos",
      },
      respondente: {
        nome: "",
        email: "",
      },
      respostas: [
        { pergunta_id: MOCK_QUESTIONS[0].id, valor: "" },
        { pergunta_id: MOCK_QUESTIONS[1].id, valor: "" },
        { pergunta_id: MOCK_QUESTIONS[2].id, valor: "" },
      ]
    },
    mode: "onBlur",
  });

  const { register, trigger, formState: { errors }, getValues } = form;

  const nextStep = async () => {
    let fieldsToValidate: string[] = [];
    if (step === 1) {
      fieldsToValidate = [
        "empresa.cnpj", 
        "empresa.razao_social", 
        "respondente.nome", 
        "respondente.email"
      ];
    } else if (step === 2) {
      fieldsToValidate = [
        "empresa.porte", 
        "empresa.regime", 
        "empresa.cnae_principal", 
        "empresa.uf", 
        "empresa.setor_macro"
      ];
    }

    const isStepValid = await trigger(fieldsToValidate as any);
    if (isStepValid) {
      setStep((s) => Math.min(s + 1, TOTAL_STEPS));
      window.scrollTo({ top: 0, behavior: 'smooth' });
    } else {
      console.log("Validation Failed:", JSON.stringify(form.formState.errors, null, 2));
    }
  };

  const prevStep = () => {
    setStep((s) => Math.max(s - 1, 1));
    window.scrollTo({ top: 0, behavior: 'smooth' });
  };

  const onSubmit = async () => {
    const isValid = await trigger();
    if (!isValid) {
      console.log("Validation Failed on Submit:", JSON.stringify(form.formState.errors, null, 2));
      return;
    }
    
    // Validar se todas as perguntas foram respondidas
    const respostas = getValues("respostas");
    if (respostas.some(r => !r.valor)) {
      setApiError("Por favor, responda a todas as perguntas do questionário.");
      return;
    }

    try {
      setIsSubmitting(true);
      setApiError(null);
      const data = getValues();
      await postDiagnostico(data);
      router.push("/sucesso");
    } catch (err: any) {
      setApiError(err.message || "Ocorreu um erro ao enviar o diagnóstico.");
    } finally {
      setIsSubmitting(false);
    }
  };

  const progress = (step / TOTAL_STEPS) * 100;

  return (
    <div className="w-full max-w-3xl mx-auto space-y-6">
      <div className="space-y-2">
        <div className="flex justify-between text-sm text-muted-foreground font-medium">
          <span>Passo {step} de {TOTAL_STEPS}</span>
          <span>{Math.round(progress)}% Concluído</span>
        </div>
        <Progress value={progress} className="h-2" />
      </div>

      <Card className="shadow-lg border-primary/10">
        <CardHeader className="space-y-1 bg-muted/30 border-b">
          <CardTitle className="text-2xl text-primary">
            {step === 1 && "Identificação Inicial"}
            {step === 2 && "Perfil da Empresa"}
            {step === 3 && "Diagnóstico Express (ABNT NBR 17301)"}
          </CardTitle>
          <CardDescription>
            {step === 1 && "Preencha com os dados básicos para contato e registro."}
            {step === 2 && "Precisamos dessas informações para balizar seu Score."}
            {step === 3 && "Responda sinceramente para obter o retrato real da sua maturidade."}
          </CardDescription>
        </CardHeader>
        
        <CardContent className="pt-6">
          <form className="space-y-6" onSubmit={(e) => e.preventDefault()}>
            
            {/* STEP 1 */}
            {step === 1 && (
              <div className="space-y-4 animate-in fade-in slide-in-from-bottom-4 duration-500">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="cnpj">CNPJ *</Label>
                    <Input id="cnpj" placeholder="00.000.000/0000-00" {...register("empresa.cnpj")} className={errors.empresa?.cnpj ? "border-destructive" : ""} />
                    {errors.empresa?.cnpj && <p className="text-sm text-destructive">{errors.empresa.cnpj.message as string}</p>}
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="razao_social">Razão Social *</Label>
                    <Input id="razao_social" placeholder="Empresa Fictícia LTDA" {...register("empresa.razao_social")} className={errors.empresa?.razao_social ? "border-destructive" : ""} />
                    {errors.empresa?.razao_social && <p className="text-sm text-destructive">{errors.empresa.razao_social.message as string}</p>}
                  </div>
                </div>
                
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4 pt-4 border-t">
                  <div className="space-y-2">
                    <Label htmlFor="nome">Seu Nome *</Label>
                    <Input id="nome" placeholder="João da Silva" {...register("respondente.nome")} className={errors.respondente?.nome ? "border-destructive" : ""} />
                    {errors.respondente?.nome && <p className="text-sm text-destructive">{errors.respondente.nome.message as string}</p>}
                  </div>
                  <div className="space-y-2">
                    <Label htmlFor="email">E-mail Profissional *</Label>
                    <Input id="email" type="email" placeholder="joao@empresa.com.br" {...register("respondente.email")} className={errors.respondente?.email ? "border-destructive" : ""} />
                    {errors.respondente?.email && <p className="text-sm text-destructive">{errors.respondente.email.message as string}</p>}
                  </div>
                </div>
              </div>
            )}

            {/* STEP 2 */}
            {step === 2 && (
              <div className="space-y-4 animate-in fade-in slide-in-from-bottom-4 duration-500">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                  <div className="space-y-2">
                    <Label htmlFor="porte">Porte da Empresa *</Label>
                    <select 
                      id="porte" 
                      className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
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
                      className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
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
                      className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
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
                    <Label htmlFor="uf">Estado (UF) *</Label>
                    <select 
                      id="uf" 
                      className="flex h-10 w-full rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                      {...register("empresa.uf")}
                    >
                      <option value="">Selecione...</option>
                      <option value="SP">São Paulo</option>
                      <option value="RJ">Rio de Janeiro</option>
                      <option value="MG">Minas Gerais</option>
                      <option value="PR">Paraná</option>
                      <option value="SC">Santa Catarina</option>
                      <option value="RS">Rio Grande do Sul</option>
                      <option value="BA">Bahia</option>
                      <option value="GO">Goiás</option>
                      {/* Outros UFs omitidos por brevidade */}
                    </select>
                    {errors.empresa?.uf && <p className="text-sm text-destructive">{errors.empresa.uf.message as string}</p>}
                  </div>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="cnae_principal">CNAE Principal (Somente Números) *</Label>
                  <Input id="cnae_principal" placeholder="1234567" {...register("empresa.cnae_principal")} className={errors.empresa?.cnae_principal ? "border-destructive" : ""} />
                  {errors.empresa?.cnae_principal && <p className="text-sm text-destructive">{errors.empresa.cnae_principal.message as string}</p>}
                </div>
              </div>
            )}

            {/* STEP 3 */}
            {step === 3 && (
              <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
                {apiError && (
                  <div className="p-4 bg-destructive/10 border border-destructive/20 text-destructive rounded-md text-sm">
                    {apiError}
                  </div>
                )}
                
                {MOCK_QUESTIONS.map((q, qIndex) => (
                  <div key={q.id} className="space-y-3 bg-muted/20 p-4 rounded-lg border">
                    <Label className="text-base font-semibold text-foreground/90 leading-tight">
                      {qIndex + 1}. {q.label}
                    </Label>
                    <div className="flex flex-col space-y-2 pt-2">
                      {q.options.map((opt, oIndex) => (
                        <Label key={oIndex} className="flex items-center space-x-3 cursor-pointer p-3 rounded border bg-background hover:bg-muted/50 transition-colors">
                          <input 
                            type="radio" 
                            value={opt.value} 
                            className="w-4 h-4 text-primary focus:ring-primary"
                            {...register(`respostas.${qIndex}.valor`)}
                          />
                          <span className="font-normal text-sm leading-none peer-disabled:cursor-not-allowed peer-disabled:opacity-70">{opt.label}</span>
                        </Label>
                      ))}
                    </div>
                  </div>
                ))}
              </div>
            )}

          </form>
        </CardContent>

        <CardFooter className="flex justify-between border-t p-6 bg-muted/10">
          <Button 
            type="button"
            variant="outline" 
            onClick={prevStep} 
            disabled={step === 1 || isSubmitting}
          >
            Voltar
          </Button>
          
          {step < TOTAL_STEPS ? (
            <Button type="button" onClick={nextStep}>Próxima Etapa</Button>
          ) : (
            <Button 
              type="button"
              onClick={onSubmit} 
              disabled={isSubmitting}
              className="bg-accent text-accent-foreground hover:bg-accent/90"
            >
              {isSubmitting ? "Enviando e Gerando PDF..." : "Finalizar Diagnóstico"}
            </Button>
          )}
        </CardFooter>
      </Card>
    </div>
  );
}
