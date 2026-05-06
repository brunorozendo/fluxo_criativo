#!/usr/bin/env python3
"""
Monta meus-produtos/{slug}/painel-entregas.html a partir dos JSONs em
meus-produtos/{slug}/dados/*.json. Leve, sem dependências externas.

Uso:
  py -3 scripts/painel-entregas-montar.py                 # usa o produto ativo
  py -3 scripts/painel-entregas-montar.py --slug curso-x  # força um slug específico

Fluxo:
  1. Lê `meus-produtos/.ativo` (ou --slug).
  2. Lê JSONs esperados em `meus-produtos/{slug}/dados/`. Faltantes viram {}.
  3. Carrega `assets/templates/painel-entregas/painel-base.html`.
  4. Substitui placeholders ({{PRODUTO_NOME}}, {{COMUNICADOR_NOME}},
     {{CSS_PATH}}, {{JS_PATH}}, {{DADOS_JSON}}) e salva o HTML final.

Objetivo: o Claude gera só os JSONs (rápido, estruturado, validável).
O HTML final é montado em <1 segundo por este script, sem regenerar markup.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))

import importlib.util

SECOES = [
    "visao-geral", "quadro", "furadeira", "decorados", "urgencias",
    "id-produto", "id-consumidor", "id-comunicador", "pesquisa",
]


def _carregar_validador():
    """Importa scripts/painel-validar.py (nome com hífen) dinamicamente."""
    caminho = SCRIPT_DIR / "painel-validar.py"
    if not caminho.exists():
        return None
    spec = importlib.util.spec_from_file_location("painel_validar", caminho)
    if not spec or not spec.loader:
        return None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def validar_dados_pesquisa(produto_dir: Path, root: Path) -> list[str]:
    pesquisa = produto_dir / "dados" / "pesquisa.json"
    if not pesquisa.exists():
        return []
    mod = _carregar_validador()
    if not mod:
        return []
    return mod.validar_arquivo(pesquisa, root)


def projeto_root() -> Path:
    return Path(__file__).resolve().parent.parent


def slug_ativo(root: Path) -> str:
    ativo = root / "meus-produtos" / ".ativo"
    if not ativo.exists():
        raise SystemExit("meus-produtos/.ativo não encontrado. Use /produto-novo ou passe --slug.")
    s = ativo.read_text(encoding="utf-8").strip()
    if not s:
        raise SystemExit("meus-produtos/.ativo está vazio.")
    return s


def carregar_json(path: Path) -> dict:
    if not path.exists():
        return {}
    try:
        txt = path.read_text(encoding="utf-8")
        data = json.loads(txt)
    except json.JSONDecodeError as e:
        raise SystemExit(f"JSON inválido em {path}: {e}")
    # Remove chaves de comentário (_comentario) para não poluir window.PAINEL_DADOS
    if isinstance(data, dict):
        data.pop("_comentario", None)
    return data


def montar(slug: str, root: Path) -> Path:
    produto_dir = root / "meus-produtos" / slug
    dados_dir = produto_dir / "dados"
    if not produto_dir.exists():
        raise SystemExit(f"Produto não encontrado: {produto_dir}")

    # Caminhos relativos para o HTML (subindo dois níveis até a raiz)
    css_rel = "../../assets/templates/painel-entregas/painel.css"
    js_rel = "../../assets/templates/painel-entregas/painel-render.js"

    # Carrega dados por seção
    dados: dict = {}
    for secao in SECOES:
        dados[secao] = carregar_json(dados_dir / f"{secao}.json")

    # Nome do produto e comunicador para cabeçalho da sidebar
    produto_nome = (
        dados.get("visao-geral", {}).get("nome")
        or ler_nome_do_perfil(produto_dir)
        or slug
    )
    comunicador_nome = dados.get("id-comunicador", {}).get("nome") or ""

    # Template shell
    tpl_path = root / "assets" / "templates" / "painel-entregas" / "painel-base.html"
    if not tpl_path.exists():
        raise SystemExit(f"Template não encontrado: {tpl_path}")
    shell = tpl_path.read_text(encoding="utf-8")

    # JSON compacto (sem indent) para manter o HTML final enxuto.
    # Os dados editáveis vivem nos JSONs individuais em dados/.
    dados_json = json.dumps(dados, ensure_ascii=False, separators=(",", ":"))
    html = (
        shell
        .replace("{{PRODUTO_NOME}}", escape_html(produto_nome))
        .replace("{{COMUNICADOR_NOME}}", escape_html(comunicador_nome))
        .replace("{{CSS_PATH}}", css_rel)
        .replace("{{JS_PATH}}", js_rel)
        .replace("{{DADOS_JSON}}", dados_json)
    )

    saida = produto_dir / "painel-entregas.html"
    saida.write_text(html, encoding="utf-8")
    return saida


def ler_nome_do_perfil(produto_dir: Path) -> str | None:
    perfil = produto_dir / "perfil.md"
    nome_txt = produto_dir / "nome.txt"
    if nome_txt.exists():
        t = nome_txt.read_text(encoding="utf-8").strip()
        if t:
            return t
    if perfil.exists():
        for linha in perfil.read_text(encoding="utf-8").splitlines():
            linha = linha.strip()
            if linha.lower().startswith("# "):
                return linha[2:].strip()
    return None


def escape_html(s: str) -> str:
    return (
        s.replace("&", "&amp;")
         .replace("<", "&lt;")
         .replace(">", "&gt;")
    )


def main() -> int:
    ap = argparse.ArgumentParser(description="Monta painel-entregas.html a partir dos JSONs de dados/.")
    ap.add_argument("--slug", help="Slug do produto. Se omitido, usa meus-produtos/.ativo.")
    args = ap.parse_args()

    root = projeto_root()
    slug = args.slug or slug_ativo(root)

    produto_dir = root / "meus-produtos" / slug
    erros = validar_dados_pesquisa(produto_dir, root)
    if erros:
        print(
            f"[painel-validar] pesquisa.json de {slug} reprovado. "
            f"Corrija antes de montar:",
            file=sys.stderr,
        )
        for e in erros:
            print(f"  . {e}", file=sys.stderr)
        return 1

    saida = montar(slug, root)
    print(f"Painel gerado: {saida}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
