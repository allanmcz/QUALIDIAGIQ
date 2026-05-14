# ADR-020 — Go-live: risco residual JWT em `localStorage` (complemento ADR-004)

Data: 2026-05-11  
**Atualização PO (recomendação objetiva):** 2026-05-13 — ver secção *Condições de aceite PO* abaixo.  
Estado: **aceite para MVP** (QDI-H-034 — fase curta)

## Contexto

O MVP do painel armazena JWT em **`localStorage`**, o que expõe o token a scripts maliciosos (classe XSS). A mitigação completa é cookie **HttpOnly** + BFF (**ADR-004**).

## Decisão de go-live (Beta)

1. Aceitar risco **residual documentado** até Onda **1.1**, desde que:
   - `npm audit` / gitleaks no CI (**ADR-016**);
   - erros do proxy Next não vazem stack (**QDI-H-036**);
   - Sentry com scrub (**QDI-H-016**);
   - pentest (**QDI-H-028**) sem P1 aberto sem compensação.
2. Copy de produto **não** prometer «sessão inviolável» enquanto ADR-004 não estiver implementado.

## Mitigações compensatórias obrigatórias MVP (refino 2026-05-13)

Além dos itens da decisão acima, em **APP_ENV=production** aplicam-se:

1. **(a) TTL reduzido do JWT do painel:** `JWT_EXPIRE_MINUTES ≤ 30` — validado em `Settings._producao_segredos_obrigatorios` (falha de arranque se > 30). Desenvolvimento mantém default longo para UX local.
2. **(b) Cabeçalhos HTTP no Next.js:** `frontend/next.config.mjs` — `X-Frame-Options: DENY`, `Referrer-Policy: no-referrer`, `X-Content-Type-Options: nosniff`, `Permissions-Policy` restritiva (geolocation/microphone/camera vazios), alinhado ao hardening do handoff de refinamento.
3. **(c) Rate-limit agressivo (API):** middleware `SensitiveRouteRateLimitMiddleware` — por defeito **5 POST/min/IP** por grupo de rota em:
   - `POST /auth/login`, `POST /auth/cadastro`;
   - `POST /auth/verificar-email/solicitar`, `POST /auth/verificar-email/confirmar`;
   - `POST` com path prefixo `/diagnosticos/rascunho-self-service` (abrangência controlada: não aplica a todo `POST /diagnosticos/` para não quebrar o wizard autenticado).
4. **(d) Expiração defensiva no cliente:** o frontend grava `admin_token_expires_at` derivado do claim `exp` do JWT e limpa o `localStorage` antes de reutilizar token vencido. Isso não substitui validação server-side, mas reduz permanência prática de token expirado no navegador.

Env: `QDI_SENSITIVE_RATE_LIMIT_ENABLED`, `QDI_SENSITIVE_RATE_LIMIT_PER_MINUTE`.

## Condições de aceite PO (2026-05-13)

**Recomendação objetiva do PO:** aceitar **H-034** com mitigação **sem** exigir migração para cookie **HttpOnly** neste momento, **desde que** se cumpra **todo** o pacote abaixo:

1. **Produção — TTL JWT:** evidência (print, log de arranque ou config redigida) de que `JWT_EXPIRE_MINUTES ≤ 30` no ambiente onde `APP_ENV=production`.
2. **Produção — headers do front:** saída de `curl -I` (ou equivalente) contra o **front público** publicado, anexada ao dossiê de go-live, mostrando os headers acordados em **(b)** desta ADR (ou equivalente documentado).
3. **Produção — rate-limit sensível:** burst de **6** `POST` em `/auth/login` (ou rota coberta pelo mesmo middleware), com anexo do **6.º** pedido **429** incluindo `Retry-After` quando devolvido pela API.
4. **Frontend — limpeza defensiva:** evidência de build/teste mostrando `admin_token_expires_at` criado no login/cadastro e sessão local descartada ao expirar.
5. **Ata de go-live:** constar expressamente a formulação: *«risco residual aceite até Onda 1.1, conforme ADR-020»*.
6. **QA ofensivo:** **pentest** (H-028) e **ZAP baseline** (H-029) **sem** XSS explorável nem **P1** aberto **relacionado a token** / superfície de sessão que invalide esta ADR.

**Quando cookie HttpOnly (ADR-004) passa a ser exigido *antes* de produção**

Somente se ocorrer **qualquer** destes casos:

- falha de **qualquer** evidência do pacote (itens 1–4) ou incumprimento do registo na ata (item 5);
- existir **P1** de **XSS** aberto (ou equivalente tratado como bloqueante no `CRITERIO_ACEITE_PENTEST.md`) ligado ao modelo de token;
- o **posicionamento comercial** passar a prometer **segurança de sessão forte** (ou linguagem equivalente a «sessão inviolável») incompatível com JWT em `localStorage` — manter copy alinhada à **ADR-020** até Onda 1.1.

## Consequências

- Ata de go-live deve listar explicitamente «JWT em localStorage — ADR-020 **e mitigações compensatórias desta ADR implementadas**» como risco aceite e, quando aplicável, a frase de aceite PO da secção *Condições de aceite PO*.
- Onda 1.1 remove o token sensível do `localStorage` ou documenta exceção aprovada pelo PO.

## Referências

- **ADR-004** — roadmap técnico HttpOnly.
- `.cursor/rules/qdi-lexico-plataforma.mdc`
