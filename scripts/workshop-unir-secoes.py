# -*- coding: utf-8 -*-
"""
Une secoes HTML independentes em uma unica pagina de vendas.

Cada secao vira um <section> escopado com uma classe unica
para evitar colisao entre seletores CSS (ex.: .hero-headline
definido diferente em 3 secoes).

Uso:
  py -3 scripts/workshop-unir-secoes.py \
    --slug mentoria-contador-aprovado \
    --output pagina-vendas-mentoria.html \
    --secoes hero-contador-aprovado-topit.html hero-paliativo-mentoria.html secao-depoimentos-video.html

  O output vai para meus-produtos/{slug}/entregas/paginas/{output}.
  As secoes sao lidas dessa mesma pasta.
"""
from __future__ import annotations

import argparse
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


# ============================================================
# Extracao de partes do HTML
# ============================================================

def extract_styles(html: str) -> str:
    matches = re.findall(r"<style[^>]*>(.*?)</style>", html, re.DOTALL)
    return "\n".join(matches)


def extract_body_inner(html: str) -> str:
    m = re.search(r"<body[^>]*>(.*?)</body>", html, re.DOTALL)
    return m.group(1).strip() if m else html


def extract_head_external(html: str) -> list[str]:
    """Extrai <link rel=...> e <script src=...> do head para dedup."""
    m = re.search(r"<head[^>]*>(.*?)</head>", html, re.DOTALL)
    if not m:
        return []
    head = m.group(1)
    tags = []
    for match in re.finditer(r"<link\b[^>]*>", head):
        tags.append(match.group(0))
    for match in re.finditer(r"<script\b[^>]*>.*?</script>", head, re.DOTALL):
        tags.append(match.group(0))
    return tags


# ============================================================
# Escopamento de CSS
# ============================================================

def find_matching_brace(s: str, start: int) -> int:
    """Acha o } que fecha o { em start."""
    depth = 1
    i = start + 1
    n = len(s)
    while i < n and depth > 0:
        c = s[i]
        if c == '{':
            depth += 1
        elif c == '}':
            depth -= 1
            if depth == 0:
                return i
        i += 1
    return n - 1


def scope_selector_list(selector_list: str, scope: str) -> str:
    parts = [p.strip() for p in selector_list.split(',')]
    scoped = []
    for p in parts:
        if not p:
            continue
        if p == ':root' or p == 'html' or p == 'body':
            scoped.append(scope)
        elif p.startswith(':root'):
            scoped.append(scope + p[len(':root'):])
        elif p.startswith('html,') or p.startswith('html '):
            scoped.append(scope + p[len('html'):])
        elif p.startswith('body,') or p.startswith('body '):
            scoped.append(scope + p[len('body'):])
        elif p.startswith('*'):
            scoped.append(f"{scope} {p}")
        else:
            scoped.append(f"{scope} {p}")
    return ', '.join(scoped)


def scope_css(css: str, scope: str) -> str:
    out = []
    pos = 0
    n = len(css)

    while pos < n:
        # Espacos em branco
        while pos < n and css[pos] in ' \t\n\r':
            out.append(css[pos])
            pos += 1
        if pos >= n:
            break

        # Comentario
        if css.startswith('/*', pos):
            end = css.find('*/', pos + 2)
            if end == -1:
                out.append(css[pos:])
                break
            out.append(css[pos:end + 2])
            pos = end + 2
            continue

        # @-rule
        if css[pos] == '@':
            at_end = pos
            while at_end < n and css[at_end] not in '{;':
                at_end += 1
            at_prelude = css[pos:at_end].strip()

            if at_end < n and css[at_end] == ';':
                out.append(css[pos:at_end + 1])
                pos = at_end + 1
                continue

            at_name = at_prelude.split()[0] if at_prelude.split() else at_prelude
            brace_end = find_matching_brace(css, at_end)

            if at_name in ('@keyframes', '@-webkit-keyframes', '@font-face', '@supports', '@page', '@property'):
                out.append(css[pos:brace_end + 1])
                pos = brace_end + 1
                continue

            if at_name == '@media':
                inner = css[at_end + 1:brace_end]
                inner_scoped = scope_css(inner, scope)
                out.append(f"{at_prelude} {{\n{inner_scoped}\n}}")
                pos = brace_end + 1
                continue

            # Qualquer outro at-rule: nao prefixa
            out.append(css[pos:brace_end + 1])
            pos = brace_end + 1
            continue

        # Seletor normal
        sel_end = pos
        while sel_end < n and css[sel_end] != '{':
            sel_end += 1
        if sel_end >= n:
            break

        selector = css[pos:sel_end].strip()
        brace_end = find_matching_brace(css, sel_end)
        body = css[sel_end + 1:brace_end]

        if selector:
            scoped = scope_selector_list(selector, scope)
            out.append(f"{scoped} {{{body}}}")
        pos = brace_end + 1

    return ''.join(out)


# ============================================================
# Merge
# ============================================================

SHELL = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{title}</title>
{head_external}
  <style>
    /* ===== RESET GLOBAL ===== */
    html, body {{
      margin: 0;
      padding: 0;
      background: #000000;
      color: #FFFFFF;
      font-family: 'Inter', 'DM Sans', system-ui, -apple-system, sans-serif;
    }}
    *, *::before, *::after {{ box-sizing: border-box; }}
    a {{ color: inherit; text-decoration: none; }}

{scoped_styles}
  </style>
</head>
<body>
{body_content}
</body>
</html>
"""


def main() -> int:
    ap = argparse.ArgumentParser(description="Une seções HTML customizadas.")
    ap.add_argument("--slug", required=True, help="Slug do produto em meus-produtos/")
    ap.add_argument("--output", required=True, help="Nome do arquivo de saida (ex.: pagina-vendas.html)")
    ap.add_argument("--secoes", nargs="+", required=True, help="Nomes dos arquivos HTML das secoes, em ordem")
    ap.add_argument("--titulo", default="Pagina de Vendas", help="Title tag")
    args = ap.parse_args()

    pasta = ROOT / "meus-produtos" / args.slug / "entregas" / "paginas"
    if not pasta.is_dir():
        print(f"Pasta nao encontrada: {pasta}")
        return 1

    head_tags_seen: set[str] = set()
    head_tags_ordered: list[str] = []
    scoped_styles_blocks: list[str] = []
    body_parts: list[str] = []

    for i, nome in enumerate(args.secoes, start=1):
        arquivo = pasta / nome
        if not arquivo.is_file():
            print(f"Arquivo nao encontrado: {arquivo}")
            return 1

        html = arquivo.read_text(encoding="utf-8")

        # Dedup head externals
        for tag in extract_head_external(html):
            key = re.sub(r"\s+", " ", tag.strip())
            if key not in head_tags_seen:
                head_tags_seen.add(key)
                head_tags_ordered.append(tag)

        # CSS escopado
        scope = f".sect-{i}"
        styles = extract_styles(html)
        scoped = scope_css(styles, scope)
        scoped_styles_blocks.append(f"    /* ===== SECAO {i}. {nome} ===== */\n{scoped}")

        # Body escopado
        body_inner = extract_body_inner(html)
        body_parts.append(f'<div class="sect-{i}">\n{body_inner}\n</div>')

    out_html = SHELL.format(
        title=args.titulo,
        head_external="\n".join(f"  {t}" for t in head_tags_ordered),
        scoped_styles="\n\n".join(scoped_styles_blocks),
        body_content="\n\n".join(body_parts),
    )

    destino = pasta / args.output
    destino.write_text(out_html, encoding="utf-8")
    print(f"Paginas unidas. Caminho: {destino.relative_to(ROOT)}")
    print(f"Secoes: {len(args.secoes)}")
    print(f"Tags head dedup: {len(head_tags_ordered)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
