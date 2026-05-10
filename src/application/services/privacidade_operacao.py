"""
Parâmetros operacionais do fluxo LGPD em painel (SLA e metadados).

Camada: Application

Workshop J3 (DEV_09052026_V2): prazo de resposta a pedidos do titular (art. 18),
referência LGPD art. 19, II — **15 dias úteis**.
"""

from __future__ import annotations

# Prazo acordado com controlador/DPO para resposta a pedidos simples (runbook + página pública).
LGPD_PRAZO_RESPOSTA_ART18_DIAS_UTEIS: int = 15
