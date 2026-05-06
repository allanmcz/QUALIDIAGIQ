"""Testes de hash Argon2id e compatibilidade bcrypt legado (ADR-010)."""

from __future__ import annotations

import bcrypt

from src.infrastructure.auth.password_hashing import (
    gerar_hash_senha,
    precisa_rehash,
    resolver_algoritmo_armazenado,
    verificar_senha,
)


class TestArgon2idHash:
    def test_gerar_hash_retorna_argon2id(self) -> None:
        h, algo = gerar_hash_senha("senha_teste_complexa_123!")
        assert algo == "argon2id"
        assert h.startswith("$argon2id$")

    def test_verificar_senha_argon2id_valida(self) -> None:
        senha = "minhasenha_segura"
        h, algo = gerar_hash_senha(senha)
        assert verificar_senha(senha, h, algo) is True

    def test_verificar_senha_argon2id_invalida(self) -> None:
        h, algo = gerar_hash_senha("senha_correta")
        assert verificar_senha("senha_errada", h, algo) is False

    def test_verificar_senha_bcrypt_legado(self) -> None:
        senha = "legado123"
        hash_bcrypt = bcrypt.hashpw(senha.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        assert verificar_senha(senha, hash_bcrypt, "bcrypt") is True
        assert verificar_senha("errada", hash_bcrypt, "bcrypt") is False

    def test_precisa_rehash_em_bcrypt(self) -> None:
        legado = bcrypt.hashpw(b"x", bcrypt.gensalt()).decode("utf-8")
        assert precisa_rehash(legado, "bcrypt") is True

    def test_nao_precisa_rehash_argon2id_fresco(self) -> None:
        h, algo = gerar_hash_senha("teste")
        assert precisa_rehash(h, algo) is False

    def test_algoritmo_desconhecido_retorna_false(self) -> None:
        assert verificar_senha("senha", "$x$", "scrypt") is False

    def test_resolver_infere_argon2_pelo_prefixo(self) -> None:
        h, _ = gerar_hash_senha("a")
        assert resolver_algoritmo_armazenado(h, None) == "argon2id"

    def test_resolver_infere_bcrypt_pelo_prefixo(self) -> None:
        b = bcrypt.hashpw(b"x", bcrypt.gensalt()).decode("utf-8")
        assert resolver_algoritmo_armazenado(b, None) == "bcrypt"
