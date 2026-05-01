# Guia de Integração da Calculadora com Sistemas ERP

**Fonte:** [Guia de Integração - Consumo Tributos](https://consumo.tributos.gov.br/servico/calcular-tributos-consumo/calculadora/documentacao/guia-integracao)

## Objetivo
Este guia demonstra como integrar um sistema ERP com a **Calculadora da Reforma Tributária do Consumo** usando os scripts Python fornecidos no arquivo `integracao-erp.zip`.

## Estrutura de Pastas
Os scripts estão organizados na pasta `integracao-erp/` com a seguinte estrutura:

```text
integracao-erp/
├── README.md                    # Documentação completa
├── requirements.txt             # Dependências Python
├── scripts/                     # Scripts Python de integração
│   ├── 1-regime-geral.py       # Calcula tributos RTC
│   ├── 2-gerar-xml.py          # Gera XML com grupos RTC
│   ├── 3-validar-grupo-xml.py  # Valida XML gerado
│   └── 4-injetar-xml.py        # Injeta RTC na NFe
├── input/                       # Arquivos de entrada
│   ├── entrada-regime-geral.json
│   └── nfe-sem-rtc.xml
├── output/                      # Arquivos gerados
│   ├── saida-regime-geral.json
│   ├── saida-gerar-xml.xml
│   └── nfe-com-rtc.xml
└── run/                         # Scripts de execução
    ├── executar-exemplo.sh     # Linux/Mac
    └── executar-exemplo.bat    # Windows
```

**Descrição dos diretórios:**
*   `scripts/` - Contém os 4 scripts Python.
*   `input/` - Arquivos de entrada (JSON e XML sem RTC).
*   `output/` - Arquivos gerados durante o processo.
*   `run/` - Scripts shell para execução automatizada.

## Fluxo Completo de Integração
O processo de integração segue 4 passos principais:

1.  **Calcular tributos** → `scripts/1-regime-geral.py`
2.  **Gerar XML** → `scripts/2-gerar-xml.py`
3.  **Validar XML** → `scripts/3-validar-grupo-xml.py`
4.  **Injetar na NFe** → `scripts/4-injetar-xml.py`

---

## Passo 1: Calcular Tributos da RTC

### Script: `1-regime-geral.py`
```python
import requests
import json
import os

# Determina caminhos relativos ao script
script_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.dirname(script_dir)
input_dir = os.path.join(base_dir, 'input')
output_dir = os.path.join(base_dir, 'output')

url = "http://localhost:8080/api/calculadora/regime-geral"

# Carrega dados de entrada
input_file = os.path.join(input_dir, 'entrada-regime-geral.json')
with open(input_file, 'r', encoding='utf-8') as file:
    body = json.load(file)

# Chama API da calculadora
response = requests.post(url, json=body, headers={'Content-Type': 'application/json'})

if response.status_code == 200:
    # Salva resultado do cálculo
    output_file = os.path.join(output_dir, 'saida-regime-geral.json')
    with open(output_file, 'w', encoding='utf-8') as file:
        json.dump(response.json(), file, indent=2, ensure_ascii=False)
    
    print("Calculo de tributos realizado com sucesso!")
    print(f"Status: {response.status_code}")
    print(f"Arquivo gerado: {output_file}")
else:
    print(f"Erro na requisicao: {response.status_code}")
    print(f"Resposta: {response.text}")
    exit(1)
```

### Arquivo de Entrada: `entrada-regime-geral.json`
```json
{
    "id": "507f1f77bcf86cd799439011",
    "versao": "1.0.0", 
    "dataHoraEmissao": "2027-01-01T03:00:00-03:00",
    "municipio": 4314902,
    "uf": "RS",
    "itens": [
        {
            "numero": 1,
            "ncm": "24021000",
            "quantidade": 222,
            "unidade": "VN", 
            "cst": "550",
            "baseCalculo": 1111,
            "cClassTrib": "550020",
            "tributacaoRegular": {
                "cst": "200",
                "cClassTrib": "200032"
            },
            "impostoSeletivo": {
                "cst": "000",
                "baseCalculo": 1111,
                "cClassTrib": "000001",
                "unidade": "VN",
                "quantidade": 222,
                "impostoInformado": 0
            }
        }
    ]
}
```

**O que acontece:**
*   Lê o arquivo `input/entrada-regime-geral.json` com os dados da operação.
*   Envia para a API da calculadora em `/api/calculadora/regime-geral`.
*   Calcula **CBS**, **IBS** e **IS**.
*   Salva o resultado em `output/saida-regime-geral.json`.
*   Usa caminhos relativos para funcionar de qualquer lugar.

---

## Passo 2: Gerar XML dos Grupos de Tributação da RTC

### Script: `2-gerar-xml.py`
```python
import requests
import json
import os

# Determina caminhos relativos ao script
script_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.dirname(script_dir)
output_dir = os.path.join(base_dir, 'output')

url = "http://localhost:8080/api/calculadora/xml/generate"

# Carrega resultado do cálculo anterior
input_file = os.path.join(output_dir, 'saida-regime-geral.json')
with open(input_file, 'r', encoding='utf-8') as file:
    json_data = json.load(file)

# Define o tipo de documento (NFe por padrão)
params = {
    'tipo': 'NFe'
}

try:
    # Gera XML a partir do cálculo
    response = requests.post(
        url, 
        json=json_data, 
        params=params,
        headers={
            'Content-Type': 'application/json',
            'Accept': 'application/xml'
        }
    )
    
    if response.status_code == 200:
        # Salva XML gerado
        output_file = os.path.join(output_dir, 'saida-gerar-xml.xml')
        with open(output_file, 'w', encoding='utf-8') as file:
            file.write(response.text)
        print("XML gerado com sucesso!")
        print(f"Arquivo gerado: {output_file}")
    else:
        print(f"Erro na requisicao: {response.status_code}")
        print(f"Resposta: {response.text}")
        exit(1)
        
except requests.exceptions.RequestException as e:
    print(f"Erro de conexao: {e}")
    exit(1)
```

**O que acontece:**
*   Lê o resultado do cálculo de `output/saida-regime-geral.json`.
*   Converte resultado do cálculo em **XML estruturado**.
*   Endpoint: `POST /api/calculadora/xml/generate?tipo=nfe`.
*   XML contém grupos `<IS>`, `<IBSCBS>`, `<ISTot>`, `<IBSCBSTot>`.
*   Salva em `output/saida-gerar-xml.xml`.

---

## Passo 3: Validar XML Gerado

### Script: `3-validar-grupo-xml.py`
```python
import requests
import os

# Determina caminhos relativos ao script
script_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.dirname(script_dir)
output_dir = os.path.join(base_dir, 'output')

url = "http://localhost:8080/api/calculadora/xml/validate"

# Carrega XML gerado anteriormente
input_file = os.path.join(output_dir, 'saida-gerar-xml.xml')
with open(input_file, 'r', encoding='utf-8') as file:
    xml_content = file.read()

# Define tipo e subtipo do documento
params = {
    'tipo': 'nfe',
    'subtipo': 'grupo'
}

try:
    response = requests.post(
        url, 
        data=xml_content, 
        params=params,
        headers={'Content-Type': 'application/xml'}
    )
    
    if response.status_code == 200:
        print("XML valido!")
        print(f"Resposta: {response.text}")
    else:
        print(f"XML invalido: {response.status_code}")
        print(f"Erros: {response.text}")
        exit(1)
        
except requests.exceptions.RequestException as e:
    print(f"Erro de conexao: {e}")
    exit(1)
```

**O que acontece:**
*   Lê o XML gerado de `output/saida-gerar-xml.xml`.
*   Valida se XML está estruturalmente correto.
*   Endpoint: `POST /api/calculadora/xml/validate?tipo=nfe&subtipo=grupo`.
*   Verifica regras de negócio da RTC.
*   Retorna mensagem de sucesso ou lista de erros.

---

## Passo 4: Injetar XML no Documento Fiscal Eletrônico

### Script: `4-injetar-xml.py`
```python
import xml.etree.ElementTree as ET
import re
import os

script_dir = os.path.dirname(os.path.abspath(__file__))
base_dir = os.path.dirname(script_dir)
input_dir = os.path.join(base_dir, 'input')
output_dir = os.path.join(base_dir, 'output')

def inject_xml_content(source_file, target_file, output_file):
    """
    Injeta o conteúdo RTC no XML da NFe em posições específicas usando regex
    """
    
    # Namespace da NFe
    NS = 'http://www.portalfiscal.inf.br/nfe'
    
    # Lê os arquivos
    with open(source_file, 'r', encoding='utf-8') as f:
        source_content = f.read()
    
    with open(target_file, 'r', encoding='utf-8') as f:
        target_content = f.read()
    
    # Detecta indentação do XML de destino
    imposto_match = re.search(r'^(\s*)<imposto>', target_content, re.MULTILINE)
    total_match = re.search(r'^(\s*)<total>', target_content, re.MULTILINE)
    
    if not imposto_match or not total_match:
        print("ERRO: Nao foi possivel detectar indentacao")
        return False
    
    imposto_indent = len(imposto_match.group(1))
    total_indent = len(total_match.group(1))
    
    # Parse do XML fonte para extrair elementos
    source_root = ET.fromstring(source_content)
    
    # Extrai elementos do XML fonte (com namespace)
    source_det_imposto = source_root.find(f'.//{{{NS}}}det[@nItem="1"]/{{{NS}}}imposto')
    source_total = source_root.find(f'.//{{{NS}}}total')
    
    if not source_det_imposto or not source_total:
        print("ERRO: Elementos fonte nao encontrados")
        return False
    
    # Extrai IS e IBSCBS
    is_element = source_det_imposto.find(f'{{{NS}}}IS')
    ibscbs_element = source_det_imposto.find(f'{{{NS}}}IBSCBS')
    
    # Extrai ISTot e IBSCBSTot
    istot_element = source_total.find(f'{{{NS}}}ISTot')
    ibscbstot_element = source_total.find(f'{{{NS}}}IBSCBSTot')
    
    def element_to_xml_string(element, indent_spaces=10):
        """Converte elemento XML para string preservando estrutura"""
        if element is None:
            return ""
        
        xml_str = ET.tostring(element, encoding='unicode')
        
        # Remove declarações de namespace e prefixos
        xml_str = xml_str.replace(f' xmlns="{NS}"', '')
        xml_str = re.sub(r'<ns\d+:', '<', xml_str)
        xml_str = re.sub(r'</ns\d+:', '</', xml_str)
        xml_str = re.sub(r' xmlns:ns\d+="[^"]*"', '', xml_str)
        
        # Formata linha por linha
        from xml.dom import minidom
        
        try:
            dom = minidom.parseString(xml_str)
            pretty = dom.toprettyxml(indent="  ")
            lines = [line for line in pretty.split('\n') if line.strip() and not line.strip().startswith('<?xml')]
            
            # Adiciona indentação base
            base_indent = ' ' * indent_spaces
            indented = [base_indent + line for line in lines]
            
            return '\n'.join(indented)
        except:
            lines = xml_str.split('\n')
            base_indent = ' ' * indent_spaces
            return '\n'.join([base_indent + line for line in lines if line.strip()])
    
    # Converte elementos para strings
    is_xml = element_to_xml_string(is_element, indent_spaces=imposto_indent + 2)
    ibscbs_xml = element_to_xml_string(ibscbs_element, indent_spaces=imposto_indent + 2)
    istot_xml = element_to_xml_string(istot_element, indent_spaces=total_indent + 2)
    ibscbstot_xml = element_to_xml_string(ibscbstot_element, indent_spaces=total_indent + 2)
    
    # 1. Injeta IS e IBSCBS ao final de <imposto>
    imposto_pattern = r'(\s*)(</imposto>)'
    
    if is_xml or ibscbs_xml:
        blocks_to_inject = []
        if is_xml:
            blocks_to_inject.append(is_xml)
        if ibscbs_xml:
            blocks_to_inject.append(ibscbs_xml)
        
        replacement = '\n' + '\n'.join(blocks_to_inject) + r'\1\2'
        target_content = re.sub(imposto_pattern, replacement, target_content, count=1)
    
    # 2. Injeta ISTot e IBSCBSTot ao final de <total>
    total_pattern = r'(\s*)(<vNFTot>)'
    total_match = re.search(total_pattern, target_content)
    
    if not total_match:
        total_pattern = r'(\s*)(</total>)'
    
    if istot_xml or ibscbstot_xml:
        blocks_to_inject = []
        if istot_xml:
            blocks_to_inject.append(istot_xml)
        if ibscbstot_xml:
            blocks_to_inject.append(ibscbstot_xml)
        
        replacement = '\n' + '\n'.join(blocks_to_inject) + r'\1\2'
        target_content = re.sub(total_pattern, replacement, target_content, count=1)
    
    # Salva o arquivo
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(target_content)
    
    return True

# Executa injeção
success = inject_xml_content(
    os.path.join(output_dir, 'saida-gerar-xml.xml'),
    os.path.join(input_dir, 'nfe-sem-rtc.xml'),
    os.path.join(output_dir, 'nfe-com-rtc.xml')
)

if success:
    print("\nXML da RTC injetado na NFe com sucesso!")
else:
    print("\nFalha ao injetar XML da RTC")
    exit(1)
```

**O que acontece:**
*   Lê XML gerado da calculadora de `output/saida-gerar-xml.xml`.
*   Lê NFe sem RTC de `input/nfe-sem-rtc.xml`.
*   Extrai grupos de tributação da RTC do XML da Calculadora.
*   Injeta nos locais corretos do Documento Fiscal Eletrônico:
    *   `<IS>` e `<IBSCBS>` dentro de `<imposto>` do item.
    *   `<ISTot>` e `<IBSCBSTot>` dentro de `<total>`.
*   Detecta automaticamente a indentação do XML de destino.
*   Gera NFe completa em `output/nfe-com-rtc.xml`.

---

## Executando Todo o Fluxo

### Pré-requisitos
*   Python 3.7 ou superior instalado.
*   API da Calculadora RTC rodando em `http://localhost:8080`.
*   Dependências Python instaladas (via `pip install -r requirements.txt`).

### Método 1: Scripts Individuais
```bash
cd integracao-erp/

# 1. Calcular tributos
python3 scripts/1-regime-geral.py

# 2. Gerar XML
python3 scripts/2-gerar-xml.py

# 3. Validar XML (opcional)
python3 scripts/3-validar-grupo-xml.py

# 4. Injetar na NFe
python3 scripts/4-injetar-xml.py
```

### Método 2: Script Automatizado (Recomendado)
```bash
cd integracao-erp/run/

# Linux/Mac
chmod +x executar-exemplo.sh
./executar-exemplo.sh

# Windows
executar-exemplo.bat
```

**O script automatizado:**
*   Verifica se Python está instalado.
*   Instala as dependências se necessário.
*   Executa os 4 passos em sequência.
*   Valida cada etapa antes de prosseguir.
*   Exibe mensagens de progresso e resultado final.

---

## Adaptando para seu ERP

### 1. Preparar Dados de Entrada
Exemplo: converter dados do ERP para formato RTC.
```python
def preparar_entrada_rtc(pedido_erp):
    return {
        "id": pedido_erp.numero,
        "versao": "1.0.0",
        "dataHoraEmissao": pedido_erp.data_emissao.isoformat() + "Z",
        "municipio": pedido_erp.municipio_codigo,
        "uf": pedido_erp.uf,
        "itens": [
            {
                "numero": item.sequencia,
                "ncm": item.ncm,
                "quantidade": item.quantidade,
                "unidade": item.unidade,
                "cst": item.cst,
                "baseCalculo": item.valor_total,
                "cClassTrib": item.classificacao_tributaria,
                # ... outros campos
            } for item in pedido_erp.itens
        ]
    }
```

### 2. Integrar com Gerador de NFe
```python
def gerar_nfe_com_rtc(pedido_erp):
    # 1. Preparar dados
    entrada_rtc = preparar_entrada_rtc(pedido_erp)
    
    # 2. Calcular RTC
    roc = calcular_tributos_rtc(entrada_rtc)
    
    # 3. Gerar XML RTC
    xml_rtc = gerar_xml_rtc(roc)
    
    # 4. Gerar NFe base
    nfe_base = gerar_nfe_base(pedido_erp)
    
    # 5. Injetar RTC na NFe
    nfe_final = injetar_rtc_na_nfe(xml_rtc, nfe_base)
    
    return nfe_final
```

### 3. Tratamento de Erros
```python
def calcular_com_retry(entrada_rtc, max_tentativas=3):
    for tentativa in range(max_tentativas):
        try:
            response = requests.post(
                "http://localhost:8080/api/calculadora/regime-geral",
                json=entrada_rtc,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )
            
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Erro {response.status_code}: {response.text}")
                
        except requests.exceptions.RequestException as e:
            print(f"Tentativa {tentativa + 1} falhou: {e}")
            if tentativa < max_tentativas - 1:
                import time
                time.sleep(2 ** tentativa)  # Backoff exponencial
    
    raise Exception("Falha após todas as tentativas")
```

---

## Endpoints da API Utilizados

### Cálculo de Tributos
*   **Endpoint:** `POST /api/calculadora/regime-geral`
*   **Content-Type:** `application/json`
*   **Entrada:** JSON com dados da operação
*   **Saída:** JSON com tributos calculados

### Geração de XML
*   **Endpoint:** `POST /api/calculadora/xml/generate`
*   **Parâmetros:** `tipo` (ex: "nfe", "cte")
*   **Content-Type:** `application/json`
*   **Accept:** `application/xml`
*   **Entrada:** JSON com resultado do cálculo
*   **Saída:** XML com grupos de tributação da RTC

### Validação de XML
*   **Endpoint:** `POST /api/calculadora/xml/validate`
*   **Parâmetros:** `tipo` e `subtipo` (ex: tipo="nfe", subtipo="grupo")
*   **Content-Type:** `application/xml`
*   **Entrada:** XML para validar
*   **Saída:** Resultado da validação

---

## Vantagens desta Abordagem
*   **Simples:** Apenas 4 scripts Python básicos.
*   **Reutilizável:** Fácil de adaptar para qualquer ERP.
*   **Completa:** Cobre todo ciclo de integração.
*   **Testada:** Scripts funcionais e validados.
*   **Padrão:** Gera NFe compatível com RTC.

## Próximos Passos
1.  Testar os scripts com seus dados.
2.  Adaptar para estrutura do seu ERP.
3.  Integrar no fluxo de emissão de NFe.
4.  Validar NFe completa no ambiente de homologação.
5.  Implementar em produção.

## Conclusão
Com estes scripts você tem uma base sólida para integrar qualquer ERP com a Calculadora da Reforma Tributária do Consumo!
