#!/usr/bin/env python3
"""
Cria um registro na tabela `admins` (substitui a rota HTTP removida por segurança).

Uso (na raiz do repo, com `.env` carregado):
    python -m src.scripts.criar_admin --email admin@empresa.com --password '***' --nome 'Nome'

Requer `SUPABASE_URL` e `SUPABASE_ANON_KEY` (ou `SUPABASE_KEY`) no ambiente.
"""

from __future__ import annotations

import argparse
import os
import sys
from uuid import UUID

from supabase import create_client

from src.infrastructure.auth.password_hashing import gerar_hash_senha


def main() -> int:
    parser = argparse.ArgumentParser(description="Cria usuário admin no PostgreSQL/Supabase.")
    parser.add_argument("--email", required=True)
    parser.add_argument("--password", required=True)
    parser.add_argument("--nome", required=True)
    parser.add_argument(
        "--tenant-id",
        type=UUID,
        default=UUID("33333333-3333-4333-8333-333333333333"),
        help="UUID do tenant vinculado ao admin (claim JWT).",
    )
    args = parser.parse_args()

    url = os.environ.get("SUPABASE_URL", "").strip()
    key = os.environ.get("SUPABASE_ANON_KEY", os.environ.get("SUPABASE_KEY", "")).strip()
    if not url or not key:
        print("Erro: defina SUPABASE_URL e SUPABASE_ANON_KEY (ou SUPABASE_KEY).", file=sys.stderr)
        return 1

    hashed, hash_algo = gerar_hash_senha(args.password)

    client = create_client(url, key)
    try:
        client.table("admins").insert(
            {
                "email": args.email,
                "hashed_password": hashed,
                "hash_algoritmo": hash_algo,
                "nome": args.nome,
                "tenant_id": str(args.tenant_id),
            }
        ).execute()
    except Exception as e:
        print(f"Erro ao inserir admin: {e}", file=sys.stderr)
        return 1

    print(f"Admin criado: {args.email} (tenant_id={args.tenant_id})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
