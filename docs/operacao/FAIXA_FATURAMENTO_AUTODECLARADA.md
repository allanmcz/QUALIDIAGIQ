# Faixa de faturamento bruto anual — autodeclaração opcional (MVP QDI)

Documento de **produto e operação**: define o significado das faixas no wizard/API, limites do MVP e relação com outros campos. **Não** substitui parecer jurídico nem regra fiscal para enquadramento legal.

**Implementação técnica:** enum `FaixaFaturamentoDeclarada` em `src/domain/entities/diagnostico.py`, coluna `diagnosticos.empresa_faixa_faturamento` (migração **`0017`**), campos opcionais em POST `/diagnosticos/` e query GET `/diagnosticos/questionario`.

---

## 1. Finalidade e LGPD

- Campo **opcional**: o respondente pode escolher **“Prefiro não informar”** (valor ausente / `null`).
- Valor tratado como **autodeclaração** para **segmentação**, contexto do relatório e estatística agregada futura — **não** é montante auditado, **não** substitui escrituração nem fiscalização.
- Texto orientador ao utilizador: ver wizard (passo perfil empresa) e **`/privacidade`** (bullet sobre faturamento opcional).

---

## 2. Catálogo canónico (slugs ↔ faixas em R$)

Os **slugs** são estáveis na API e no JSON persistido; os **rótulos** em PT-BR na UI podem ser ajustados por copy sem mudar o slug.

| Slug (`empresa_faixa_faturamento`) | Faixa descritiva (referência para o utilizador) |
|-----------------------------------|-----------------------------------------------|
| `ate_360_mil` | Até R$ 360 mil |
| `entre_360_mil_e_4_8_mi` | De R$ 360 mil a R$ 4,8 milhões |
| `entre_4_8_mi_e_10_mi` | De R$ 4,8 milhões a R$ 10 milhões |
| `entre_10_mi_e_60_mi` | De R$ 10 milhões a R$ 60 milhões |
| `entre_60_mi_e_100_mi` | De R$ 60 milhões a R$ 100 milhões |
| `entre_100_mi_e_500_mi` | De R$ 100 milhões a R$ 500 milhões |
| `acima_500_mi` | Acima de R$ 500 milhões |

---

## 3. Convenção de limites no MVP (fronteiras entre faixas)

No **MVP** o produto **não** impõe regra matemática explícita do tipo “inclusive no limite inferior / exclusivo no superior” para cada slug.

- O titular escolhe a faixa que **melhor descreve** a realidade da empresa para fins de **autoclassificação** no diagnóstico.
- Evita litígio de UX em valores exatamente iguais a **R$ 360.000,00** ou **R$ 4.800.000,00**, etc. — cenários em que, na prática, contabilidade e regime tributário já orientam o utilizador.
- Se no futuro for exigido **contrato numérico fechado** (intervalos semiabertos, alinhamento a porte legal, etc.), deve ser tratado como **evolução de produto** + eventual ADR e revisão de labels.

**Referência econômica (não vinculante ao slug):** os marcos **360 mil** e **4,8 milhões** são amplamente associados a limites do **Simples Nacional** e correlatos (**LC 123/2006** e alterações). O QDI **não** calcula enquadramento legal a partir só deste campo.

---

## 4. Relação com **Porte da empresa** (`PorteEmpresa`)

- **Porte** e **faixa de faturamento** são **independentes** no modelo de dados: ambos podem ser preenchidos.
- Podem existir **combinações aparentemente incoerentes** (ex.: porte “micro” com faixa alta) por erro, por ano-calendário diferente, por grupo econômico, ou por interpretação do respondente.
- O MVP **não** bloqueia submissão por inconsistência porte × faixa; **roadmap** pode introduzir aviso suave (“confirme se a faixa reflete o último ano”) ou uso interno em scoring, sem misturar com obrigação legal automática.

---

## 5. Imutabilidade após diagnóstico finalizado (WORM)

Após `status = finalizado`, a coluna `empresa_faixa_faturamento` entra no conjunto de campos protegidos pelo trigger **`qdi_tr_block_mutacao_pos_finalizacao`** (evidência imutável), em linha com os demais snapshots de empresa no mesmo registo.

---

## 6. Referências cruzadas

| Artefacto | Conteúdo |
|-----------|-----------|
| `docs/operacao/DECISOES_PRODUTO_MVP_D1_D5.md` | D3 — contexto “faturamento / setor fino”; esta faixa é **fatia implementada** sem reabrir todo o escopo D3. |
| `docs/operacao/SQL_VERIFICACAO_SCHEMA_MVP.sql` | Check `empresa_faixa_faturamento_0017`. |
| `scripts/verify_mvp_schema.py` | Verificação da coluna pós-migração. |

---

*Última atualização documental: alinhada à entrega da migração **0017** e enum no domínio.*
