"""Merge catálogo JSON + overlay de pesos (banco_cache)."""

from __future__ import annotations

from datetime import date
from unittest.mock import MagicMock, patch

from src.domain.value_objects.normativa_pergunta_peso import PesoPerguntaNormativoVigente
from src.infrastructure.config.settings import get_settings
from src.infrastructure.questionario import banco_cache as bc


class TestBancoCacheNormativaOverlay:
    """Garante substituição de peso, rasto ``overlay_por_codigo`` e cache de merge."""

    def teardown_method(self) -> None:
        bc.reset_catalogo_perguntas_em_memoria()
        get_settings.cache_clear()

    @patch.object(bc, "_normativa_pergunta_repo")
    def test_overlay_substitui_peso_e_registra_catalogo(self, mock_repo_fn: MagicMock) -> None:
        mock_repo = MagicMock()
        mock_repo.obter_metadados_por_codigo_validos_na_data.return_value = {
            "Q-EST-001": PesoPerguntaNormativoVigente(
                peso=99.0,
                vigencia_inicio=date(2026, 1, 1),
                vigencia_fim=None,
                rotulo_versao="test-overlay",
            ),
        }
        mock_repo_fn.return_value = mock_repo

        ce = bc.get_catalogo_perguntas_efetivo(data_referencia_normativa=date(2026, 5, 1))
        por_codigo = {p.codigo: p for p in ce.perguntas}
        assert por_codigo["Q-EST-001"].peso == 99.0
        assert "Q-EST-001" in ce.overlay_por_codigo
        cat_json, meta = ce.overlay_por_codigo["Q-EST-001"]
        assert cat_json != 99.0
        assert meta.peso == 99.0

    @patch.object(bc, "_normativa_pergunta_repo")
    def test_sem_overlay_mantem_json(self, mock_repo_fn: MagicMock) -> None:
        mock_repo = MagicMock()
        mock_repo.obter_metadados_por_codigo_validos_na_data.return_value = {}
        mock_repo_fn.return_value = mock_repo

        ce = bc.get_catalogo_perguntas_efetivo(data_referencia_normativa=date(2026, 5, 1))
        assert ce.overlay_por_codigo == {}
        assert len(ce.perguntas) > 0

    @patch.object(bc, "_normativa_pergunta_repo")
    def test_get_banco_perguntas_cached_delega_catalogo(self, mock_repo_fn: MagicMock) -> None:
        mock_repo = MagicMock()
        mock_repo.obter_metadados_por_codigo_validos_na_data.return_value = {}
        mock_repo_fn.return_value = mock_repo

        lst = bc.get_banco_perguntas_cached()
        assert isinstance(lst, list)
        assert len(lst) == len(bc.get_catalogo_perguntas_efetivo().perguntas)

    @patch.object(bc, "_ttl_segundos_overlay_cache", return_value=300.0)
    @patch.object(bc, "_normativa_pergunta_repo")
    def test_cache_mesma_data_chama_repo_uma_vez(
        self, mock_repo_fn: MagicMock, _mock_ttl: MagicMock
    ) -> None:
        """Rajada de pedidos na mesma data — um SELECT de overlay por janela TTL."""
        mock_repo = MagicMock()
        mock_repo.obter_metadados_por_codigo_validos_na_data.return_value = {}
        mock_repo_fn.return_value = mock_repo

        bc.reset_catalogo_perguntas_em_memoria()
        ref = date(2031, 6, 1)
        bc.get_catalogo_perguntas_efetivo(data_referencia_normativa=ref)
        bc.get_catalogo_perguntas_efetivo(data_referencia_normativa=ref)
        assert mock_repo.obter_metadados_por_codigo_validos_na_data.call_count == 1

    @patch.object(bc, "_ttl_segundos_overlay_cache", return_value=0.0)
    @patch.object(bc, "_normativa_pergunta_repo")
    def test_ttl_zero_desliga_cache(self, mock_repo_fn: MagicMock, _mock_ttl: MagicMock) -> None:
        mock_repo = MagicMock()
        mock_repo.obter_metadados_por_codigo_validos_na_data.return_value = {}
        mock_repo_fn.return_value = mock_repo

        bc.reset_catalogo_perguntas_em_memoria()
        ref = date(2031, 6, 2)
        bc.get_catalogo_perguntas_efetivo(data_referencia_normativa=ref)
        bc.get_catalogo_perguntas_efetivo(data_referencia_normativa=ref)
        assert mock_repo.obter_metadados_por_codigo_validos_na_data.call_count == 2

    @patch(
        "src.infrastructure.questionario.banco_cache.time.monotonic",
        side_effect=[0.0, 0.0, 20.0, 20.0],
    )
    @patch.object(bc, "_ttl_segundos_overlay_cache", return_value=10.0)
    @patch.object(bc, "_normativa_pergunta_repo")
    def test_cache_expira_apos_ttl_monotonic(
        self, mock_repo_fn: MagicMock, _mock_ttl: MagicMock, _mock_mono: MagicMock
    ) -> None:
        mock_repo = MagicMock()
        mock_repo.obter_metadados_por_codigo_validos_na_data.return_value = {}
        mock_repo_fn.return_value = mock_repo

        bc.reset_catalogo_perguntas_em_memoria()
        ref = date(2031, 6, 3)
        bc.get_catalogo_perguntas_efetivo(data_referencia_normativa=ref)
        bc.get_catalogo_perguntas_efetivo(data_referencia_normativa=ref)
        assert mock_repo.obter_metadados_por_codigo_validos_na_data.call_count == 2

    @patch.object(bc, "_ttl_segundos_overlay_cache", return_value=3600.0)
    @patch.object(bc, "_normativa_pergunta_repo")
    def test_cache_lru_evicta_data_mais_antiga(
        self, mock_repo_fn: MagicMock, _mock_ttl: MagicMock
    ) -> None:
        """Mais datas distintas que o limite — a mais antiga sai; volta a consultar."""
        mock_repo = MagicMock()
        mock_repo.obter_metadados_por_codigo_validos_na_data.return_value = {}
        mock_repo_fn.return_value = mock_repo

        bc.reset_catalogo_perguntas_em_memoria()
        with patch.object(bc, "_MERGED_MAX_DATES", 2):
            bc.get_catalogo_perguntas_efetivo(data_referencia_normativa=date(2040, 1, 1))
            bc.get_catalogo_perguntas_efetivo(data_referencia_normativa=date(2040, 1, 2))
            bc.get_catalogo_perguntas_efetivo(data_referencia_normativa=date(2040, 1, 3))
            bc.get_catalogo_perguntas_efetivo(data_referencia_normativa=date(2040, 1, 1))
        assert mock_repo.obter_metadados_por_codigo_validos_na_data.call_count == 4


class TestBancoCacheTtlSettings:
    """Fallback de TTL quando settings falham."""

    def teardown_method(self) -> None:
        bc.reset_catalogo_perguntas_em_memoria()
        get_settings.cache_clear()

    @patch("src.infrastructure.config.settings.get_settings", side_effect=RuntimeError("offline"))
    def test_ttl_segundos_overlay_cache_excecao_fallback_60(self, _mock_gs: MagicMock) -> None:
        assert bc._ttl_segundos_overlay_cache() == 60.0

    @patch("src.infrastructure.config.settings.get_settings")
    def test_ttl_segundos_overlay_cache_zero_via_settings(self, mock_gs: MagicMock) -> None:
        mock_s = MagicMock()
        mock_s.qdi_normativa_pergunta_peso_cache_ttl_seconds = 0
        mock_gs.return_value = mock_s
        assert bc._ttl_segundos_overlay_cache() == 0.0


def test_versao_catalogo_lida_retorna_string() -> None:
    """Smoke — integração com ``versao_catalogo_banco_mvp``."""
    v = bc.versao_catalogo_lida()
    assert isinstance(v, str)
    assert len(v) > 0
