"""
Erros de orquestração da camada Application (casos de uso).

Não confundir com exceções de domínio (`DiagnosticoNaoFinalizavelError`, etc.).
"""


class DiagnosticoNaoEncontradoError(Exception):
    """Nenhuma linha no tenant informado para o ID do diagnóstico."""


class ConflitoVersaoOtimistaError(Exception):
    """Header If-Match (versão otimista) não coincide com o estado persistido."""


class ErroPersistenciaLgpdError(Exception):
    """Falha ao aceder à tabela LGPD (infraestrutura Postgres, migração ou ligação)."""


class EliminacaoDiagnosticoFinalizadoWormError(Exception):
    """
    Pedido de eliminação física sobre diagnóstico já finalizado (evidência WORM).

    Operação correta: anonimização controlada (LGPD art. 18, IV) via fluxo dedicado.
    Alinhado a ADR-012 e workshop J4 (DEV_09052026_V2).
    """
