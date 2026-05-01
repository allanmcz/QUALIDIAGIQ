"""
Exemplos consolidados para OpenAPI (P1 - documentacao exportavel).

Camada: Presentation — usados em Body(openapi_examples=...) e respostas descritivas.
"""

from __future__ import annotations

from typing import Any

# UUID de pergunta real do catálogo (Q-EST-001 derivado do namespace MVP) — usado só em exemplo.
_EXEMPLO_PERGUNTA_UUID = "df52b20e-dab8-5ce5-a89d-4fb235016cbe"

# Corpo mínimo válido para POST /diagnosticos/ (Idempotency-Key e Bearer vão nos headers).
OPENAPI_EXAMPLES_POST_DIAGNOSTICO: dict[str, dict[str, Any]] = {
    "micro_comercio_um_item": {
        "summary": "Micro comércio — uma resposta escala",
        "description": (
            "Headers obrigatorios: Authorization Bearer (JWT valido do login) e "
            "Idempotency-Key (UUID v4). Resposta HTTP 201 com score e consultoria derivada."
        ),
        "value": {
            "empresa": {
                "cnpj": "12345678000195",
                "razao_social": "Empresa Exemplo LTDA",
                "porte": "micro",
                "regime": "simples_nacional",
                "cnae_principal": "1234567",
                "uf": "SP",
                "setor_macro": "comercio",
            },
            "respondente": {
                "email": "fiscal@empresa.com.br",
                "nome": "Fulano da Silva",
                "telefone": "5511999998888",
            },
            "respostas": [{"pergunta_id": _EXEMPLO_PERGUNTA_UUID, "valor": 4}],
            "plano": "gratuito",
            "aceite_termos_privacidade": True,
        },
    },
}


# Referência cruzada — resposta tipada em ValidarAncoraNormativaResponse (schemas.py).
OPENAPI_NORMATIVA_TAGS_DOC = (
    "Sem autenticação. Resposta sempre 200 com campo `valido` booleano e opcional "
    "`motivo_rejeicao` quando inválido."
)

OPENAPI_EXAMPLES_NORMATIVA: dict[str, dict[str, Any]] = {
    "com_lc214": {
        "summary": "Texto com LC 214/2025",
        "value": {
            "texto": "Conforme LC 214/2025 art. 5º e EC 132/2023, o plano deve ser documentado."
        },
    },
    "sem_ancora": {
        "summary": "Texto sem âncora reconhecida",
        "value": {"texto": "Melhore a governanca tributaria da empresa sem citar norma."},
    },
}
