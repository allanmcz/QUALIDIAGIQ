"""
Validação de CNPJ brasileiro (14 dígitos + dígitos verificadores).

Camada: Domain (regra cadastral pura — sem IO).

Base: Cadastro Nacional da Pessoa Jurídica (Receita Federal do Brasil).

Analogia Delphi/Oracle: equivale a uma função PL/SQL `FN_VALIDA_CNPJ` antes do INSERT na tabela de empresas.
"""

from __future__ import annotations


def normalizar_cnpj_apenas_digitos(valor: str) -> str:
    """Extrai somente dígitos da string informada."""
    return "".join(c for c in (valor or "").strip() if c.isdigit())


def cnpj_com_digitos_verificadores_validos(digitos14: str) -> bool:
    """
    Verifica os dois dígitos verificadores do CNPJ (algoritmo oficial).

    Args:
        digitos14: exatamente 14 caracteres numéricos.

    Returns:
        True se o DV confere; False caso contrário (ou entrada inválida).
    """
    if len(digitos14) != 14 or not digitos14.isdigit():
        return False
    if len(set(digitos14)) == 1:
        return False

    def _dv(base: str, pesos: list[int]) -> int:
        soma = sum(int(d) * p for d, p in zip(base, pesos, strict=True))
        resto = soma % 11
        return 0 if resto < 2 else 11 - resto

    w1 = [5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    w2 = [6, 5, 4, 3, 2, 9, 8, 7, 6, 5, 4, 3, 2]
    d1 = _dv(digitos14[:12], w1)
    d2 = _dv(digitos14[:13], w2)
    return d1 == int(digitos14[12]) and d2 == int(digitos14[13])


def exigir_cnpj_vazio_ou_com_dv_ok(valor_normalizado_14_ou_vazio: str) -> None:
    """
    Garante invariante de domínio para `EmpresaInfo.cnpj`.

    Raises:
        ValueError: se preenchido e DV inválido.
    """
    if valor_normalizado_14_ou_vazio == "":
        return
    if not cnpj_com_digitos_verificadores_validos(valor_normalizado_14_ou_vazio):
        raise ValueError("CNPJ inválido: dígitos verificadores não conferem")
