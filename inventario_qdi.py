#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import os
import json
from pathlib import Path
from collections import defaultdict

projeto_root = Path("/Users/allan/000-PROJETOS/018-QUALIDIAGIQ")
analise_dir = projeto_root / "ANALISE_04052026_MANUS"

inventario = {
    "backend": {"arquivos": [], "total_linhas": 0, "modulos": {}},
    "frontend": {"arquivos": [], "total_linhas": 0},
    "testes": {"arquivos": [], "total_linhas": 0},
    "docs": {"arquivos": [], "total_linhas": 0},
}

def contar_linhas(arquivo):
    try:
        with open(arquivo, 'r', encoding='utf-8', errors='ignore') as f:
            return len(f.readlines())
    except:
        return 0

modulos_backend = defaultdict(list)
for py_file in (projeto_root / "src").rglob("*.py"):
    rel_path = str(py_file.relative_to(projeto_root))
    linhas = contar_linhas(py_file)
    modulo = rel_path.split('/')[1] if len(rel_path.split('/')) > 1 else "root"
    inventario["backend"]["arquivos"].append({"path": rel_path, "linhas": linhas})
    inventario["backend"]["total_linhas"] += linhas
    modulos_backend[modulo].append(rel_path)

inventario["backend"]["modulos"] = dict(modulos_backend)

for ts_file in (projeto_root / "frontend" / "app").rglob("*.ts*"):
    if "node_modules" not in str(ts_file):
        rel_pat        rel_pat        rel_pat        rel_pat        rel_pat   tar_linhas(ts_file)
        inventario["frontend"]["arquivos"].append({"path": rel_path, "linhas": linhas})
        inventario["frontend"]["total_linhas"] += li        inventario["fr (projeto_root / "tests").rglob("*.py"):
    rel_path = str(test_file.relative_to(projeto_root))
    linhas = contar_linhas(test_file)
    inventario["testes"]["arquivos"].append({"path": rel_path, "linhas": linhas})
    inventario["testes"]["total_linhas"] += linhas

for doc_file in (projeto_root for doc_file in (projeto_r   rel_path = str(doc_file.relative_to(projeto_root))
    linhas = contar_linhas(doc_file)
    inventario["docs"]["arquivos"].append({"path": rel_path, "linhas": linhas})
    inventario["docs"]["total_linhas"] += linhas

 InventPrintrio gerado!")("
print(f"  Backend: {len(inventario['backend']['arquivos'])} arquivos, {inventario['backend']['total_linhas']} linhas")
print(f"  Frontend: {len(inventario['frontend']['arquivos'])} arquivos, {inventario['frontend']['total_linhas']} linhas")
print(f"  Testes: {len(inventario['testes']['arquivos'])} arquivos, {inventario['testes']['total_linhas']} linhas")
print(f"  Docs: {len(inventario['docs']['arquivos'])} arquivos, {inventario['docs']['total_linhas']} linhas")
