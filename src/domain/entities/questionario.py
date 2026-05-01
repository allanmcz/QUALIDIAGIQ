"""
Entidades e regras de negócio para o motor do questionário.

Camada: Domain
Isola toda a complexidade de exibição condicional e pontuação.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, cast
from uuid import UUID, uuid4

if TYPE_CHECKING:
    from src.domain.entities.diagnostico import (
        EmpresaInfo,
        PorteEmpresa,
        RegimeTributario,
        SetorMacro,
    )
    from src.domain.value_objects.score import Dimensao


class TipoPergunta(Enum):
    """Tipos alinhados ao doc `docs/refs/05_QUESTIONARIO_v1.md` + extensões MVP."""

    TERNARIA = "ternaria"
    BINARIA = "binaria"
    ESCALA_1_5 = "escala_1_5"
    MULTIPLA_ESCOLHA = "multipla_escolha"
    CHECKLIST = "checklist"
    NUMERICA = "numerica"


class AlternativaTernaria(Enum):
    SIM = "sim"
    PARCIALMENTE = "parcialmente"
    NAO = "nao"


@dataclass(frozen=True, slots=True)
class CondicaoExibicao:
    """Regras para o motor adaptativo decidir se a pergunta aparece."""

    regimes_permitidos: tuple[RegimeTributario, ...] | None = None
    setores_permitidos: tuple[SetorMacro, ...] | None = None
    setores_excluidos: tuple[SetorMacro, ...] | None = None
    portes_permitidos: tuple[PorteEmpresa, ...] | None = None


@dataclass(frozen=True, slots=True)
class Pergunta:
    """Uma questão dentro do diagnóstico."""

    codigo: str
    dimensao: Dimensao
    texto: str
    peso: float
    tipo: TipoPergunta
    base_legal: str | None = None
    condicao: CondicaoExibicao | None = None
    # Para MULTIPLA_ESCOLHA / CHECKLIST: quantidade máxima de itens selecionáveis (denominador do score)
    multipla_total: int | None = None
    id: UUID = field(default_factory=uuid4)

    def __post_init__(self) -> None:
        if self.peso < 0:
            raise ValueError(f"Peso não pode ser negativo. Recebido: {self.peso}")

    def aplicavel_para(self, empresa: EmpresaInfo) -> bool:
        """
        Avalia se a pergunta é aplicável para a empresa (Motor Adaptativo).
        Se a pergunta não tem condição, ela é "core" e se aplica a todos.
        """
        if self.condicao is None:
            return True

        c = self.condicao
        if c.setores_excluidos and empresa.setor_macro in c.setores_excluidos:
            return False
        regimes_ok = c.regimes_permitidos is None or empresa.regime in c.regimes_permitidos
        setores_ok = c.setores_permitidos is None or empresa.setor_macro in c.setores_permitidos
        portes_ok = c.portes_permitidos is None or empresa.porte in c.portes_permitidos
        return regimes_ok and setores_ok and portes_ok


@dataclass(frozen=True, slots=True)
class Resposta:
    """Resposta dada pelo usuário a uma pergunta."""

    diagnostico_id: UUID
    pergunta_id: UUID
    pergunta_tipo: TipoPergunta
    valor_bruto: str | int | list[str]  # 'sim', json list, 1-5, etc.
    id: UUID = field(default_factory=uuid4)

    def calcular_pontuacao(self, pergunta: Pergunta) -> float | None:
        """
        Converte a resposta bruta em pontuação 0-100, ou None se deve ser excluída da média
        (ex.: 'nao_se_aplica' em ternárias estendidas - doc seção 11.1).
        """
        if self.pergunta_tipo == TipoPergunta.TERNARIA:
            raw = str(self.valor_bruto).lower().strip()
            if raw in ("nao_se_aplica", "nao_comercializo", "nao_se_aplica_ao_meu_negocio"):
                return None
            try:
                alternativa = AlternativaTernaria(raw)
            except ValueError as e:
                raise ValueError(
                    f"Valor inválido para pergunta ternária: {self.valor_bruto}. "
                    f"Use 'sim', 'parcialmente', 'nao' ou 'nao_se_aplica'."
                ) from e
            if alternativa == AlternativaTernaria.SIM:
                return 100.0
            if alternativa == AlternativaTernaria.PARCIALMENTE:
                return 50.0
            return 0.0

        if self.pergunta_tipo == TipoPergunta.BINARIA:
            v = str(self.valor_bruto).lower().strip()
            if v in ("sim", "s", "1", "true"):
                return 100.0
            if v in ("nao", "n", "0", "false"):
                return 0.0
            raise ValueError(f"Valor inválido para binária: {self.valor_bruto}")

        if self.pergunta_tipo == TipoPergunta.ESCALA_1_5:
            try:
                escala = int(cast("str | int", self.valor_bruto))
            except (ValueError, TypeError) as e:
                raise ValueError(
                    f"Valor inválido para escala. Deve ser um número de 1 a 5. Recebido: {self.valor_bruto}"
                ) from e
            if not 1 <= escala <= 5:
                raise ValueError(f"Valor fora do limite da escala (1-5): {escala}")
            return (escala - 1) * 25.0

        if self.pergunta_tipo in (TipoPergunta.MULTIPLA_ESCOLHA, TipoPergunta.CHECKLIST):
            total = pergunta.multipla_total
            if total is None or total < 1:
                raise ValueError(
                    "Pergunta multipla/checklist exige multipla_total > 0 no catálogo."
                )
            sel = self._extrair_lista_selecionados()
            if len(sel) > total:
                raise ValueError("Mais itens selecionados que o permitido pelo catálogo.")
            return min(100.0, (len(sel) / total) * 100.0)

        if self.pergunta_tipo == TipoPergunta.NUMERICA:
            try:
                n = float(cast("str | int | float", self.valor_bruto))
            except (ValueError, TypeError) as e:
                raise ValueError(f"Valor numérico inválido: {self.valor_bruto}") from e
            if not 0.0 <= n <= 100.0:
                raise ValueError("NUMERICA deve estar entre 0 e 100.")
            return float(n)

        raise NotImplementedError(f"Cálculo não implementado para o tipo {self.pergunta_tipo}")

    def _extrair_lista_selecionados(self) -> list[str]:
        vb = self.valor_bruto
        if isinstance(vb, list):
            return [str(x).strip() for x in vb if str(x).strip()]
        if isinstance(vb, str):
            try:
                parsed = json.loads(vb)
            except json.JSONDecodeError:
                return [p.strip() for p in vb.split(",") if p.strip()]
            else:
                if isinstance(parsed, list):
                    return [str(x).strip() for x in parsed if str(x).strip()]
                raise ValueError("JSON de múltipla escolha deve ser lista.")
        raise ValueError(f"Formato inválido para múltipla escolha: {type(vb)}")
