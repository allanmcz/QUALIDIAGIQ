# Instructions

- Following Playwright test failed.
- Explain why, be concise, respect Playwright best practices.
- Provide a snippet of code with the fix, if possible.

# Test info

- Name: tests/wizard.spec.ts >> Wizard E2E Flow
- Location: tests/wizard.spec.ts:3:5

# Error details

```
Test timeout of 30000ms exceeded.
```

```
Error: locator.selectOption: Test timeout of 30000ms exceeded.
Call log:
  - waiting for locator('select[id="porte"]')

```

# Page snapshot

```yaml
- generic [ref=e1]:
  - banner [ref=e2]:
    - generic [ref=e3]:
      - generic [ref=e4]:
        - generic [ref=e5]: Q
        - generic [ref=e6]: QualiDiagIQ
        - generic [ref=e7]: by Tributiq
      - generic [ref=e8]:
        - img [ref=e9]
        - generic [ref=e12]: Conformidade ABNT NBR 17301
  - main [ref=e13]:
    - generic [ref=e15]:
      - generic [ref=e16]:
        - img [ref=e18]
        - heading "Análise de Maturidade Tributária" [level=1] [ref=e21]
        - paragraph [ref=e22]: Descubra em 3 passos simples o nível de aderência da sua empresa às novas normas e identifique pontos críticos de melhoria.
      - generic [ref=e23]:
        - generic [ref=e24]:
          - generic [ref=e25]:
            - generic [ref=e26]: Passo 1 de 3
            - generic [ref=e27]: 33% Concluído
          - progressbar [ref=e28]: x
        - generic [ref=e31]:
          - generic [ref=e32]:
            - generic [ref=e33]: Identificação Inicial
            - generic [ref=e34]: Preencha com os dados básicos para contato e registro.
          - generic [ref=e37]:
            - generic [ref=e38]:
              - generic [ref=e39]:
                - generic [ref=e40]: CNPJ *
                - textbox "CNPJ *" [ref=e41]:
                  - /placeholder: 00.000.000/0000-00
                  - text: "12345678000195"
                - paragraph [ref=e42]: "Invalid input: expected string, received undefined"
              - generic [ref=e43]:
                - generic [ref=e44]: Razão Social *
                - textbox "Razão Social *" [ref=e45]:
                  - /placeholder: Empresa Fictícia LTDA
                  - text: Empresa E2E Test SA
                - paragraph [ref=e46]: "Invalid input: expected string, received undefined"
            - generic [ref=e47]:
              - generic [ref=e48]:
                - generic [ref=e49]: Seu Nome *
                - textbox "Seu Nome *" [ref=e50]:
                  - /placeholder: João da Silva
                  - text: Test Lead
                - paragraph [ref=e51]: "Invalid input: expected string, received undefined"
              - generic [ref=e52]:
                - generic [ref=e53]: E-mail Profissional *
                - textbox "E-mail Profissional *" [ref=e54]:
                  - /placeholder: joao@empresa.com.br
                  - text: test@e2e.com
                - paragraph [ref=e55]: "Invalid input: expected string, received undefined"
          - generic [ref=e56]:
            - button "Voltar" [disabled]
            - button "Próxima Etapa" [active] [ref=e57] [cursor=pointer]
  - contentinfo [ref=e58]:
    - generic [ref=e59]:
      - paragraph [ref=e60]: © 2026 Tributiq. Todos os direitos reservados.
      - generic [ref=e61]:
        - link "Termos de Uso" [ref=e62] [cursor=pointer]:
          - /url: "#"
        - link "Política de Privacidade" [ref=e63] [cursor=pointer]:
          - /url: "#"
  - alert [ref=e64]
```

# Test source

```ts
  1  | import { test, expect } from '@playwright/test';
  2  | 
  3  | test('Wizard E2E Flow', async ({ page }) => {
  4  |   console.log("Navigating to Wizard...");
  5  |   await page.goto('http://localhost:3000/wizard');
  6  | 
  7  |   // Step 1
  8  |   console.log("Filling Step 1...");
  9  |   await page.fill('input[id="cnpj"]', '12345678000195');
  10 |   await page.fill('input[id="razao_social"]', 'Empresa E2E Test SA');
  11 |   await page.fill('input[id="nome"]', 'Test Lead');
  12 |   await page.fill('input[id="email"]', 'test@e2e.com');
  13 |   
  14 |   await page.getByRole('button', { name: 'Próxima Etapa' }).click();
  15 | 
  16 |   // Step 2
  17 |   console.log("Filling Step 2...");
> 18 |   await page.locator('select[id="porte"]').selectOption('medio');
     |                                            ^ Error: locator.selectOption: Test timeout of 30000ms exceeded.
  19 |   await page.locator('select[id="regime"]').selectOption('lucro_real');
  20 |   await page.locator('select[id="setor_macro"]').selectOption('servicos');
  21 |   await page.locator('select[id="uf"]').selectOption('SP');
  22 |   await page.fill('input[id="cnae_principal"]', '1234567');
  23 |   
  24 |   await page.getByRole('button', { name: 'Próxima Etapa' }).click();
  25 | 
  26 |   // Step 3
  27 |   console.log("Filling Step 3...");
  28 |   const radios = await page.locator('input[type="radio"]').all();
  29 |   // Select the highest score for each question
  30 |   await radios[2].check();
  31 |   await radios[5].check();
  32 |   await radios[8].check();
  33 | 
  34 |   console.log("Submitting...");
  35 |   await page.getByRole('button', { name: 'Finalizar Diagnóstico' }).click();
  36 | 
  37 |   console.log("Waiting for success page...");
  38 |   await expect(page.getByText('Diagnóstico Concluído com Sucesso!')).toBeVisible({ timeout: 15000 });
  39 |   console.log("SUCCESS: Reached the success page and API request succeeded!");
  40 | });
  41 | 
```