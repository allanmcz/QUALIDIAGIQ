"""
Erros de orquestração da camada Application (casos de uso).

Não confundir com exceções de domínio (`DiagnosticoNaoFinalizavelError`, etc.).
"""


class DiagnosticoNaoEncontradoError(Exception):
    """Nenhuma linha no tenant informado para o ID do diagnóstico."""


class ConflitoVersaoOtimistaError(Exception):
    """Header If-Match (versão otimista) não coincide com o estado persistido."""
