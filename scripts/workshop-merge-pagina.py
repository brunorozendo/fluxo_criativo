# -*- coding: utf-8 -*-
"""
DEPRECATED. Script descontinuado junto com os 5 temas VTSD.

Fluxo atual: scripts/montar-pagina-copias.py monta a pagina a partir de
copias HTML isoladas em paginas/copias/ (geradas pela /pagina-visual).

Mantido so por compatibilidade. Nao use em novos produtos.

---

Regenera a página completa VTSD via build_merge.py do tema escolhido e,
opcionalmente, copia para meus-produtos/{slug}/entregas/paginas/vendas-{slug}.html.

Uso (na raiz do repositório):
  python scripts/workshop-merge-pagina.py --tema flat_claro
  python scripts/workshop-merge-pagina.py --tema glass_escuro --copiar-entregas
  python scripts/workshop-merge-pagina.py --tema teal_claro --copiar-entregas --slug meu-produto

  Após copiar templates com workshop-copy-template-tema.py:
  python scripts/workshop-merge-pagina.py --tema flat_claro --templates-root meus-produtos/meu-produto/entregas/paginas/templates-flat_claro --copiar-entregas
"""
from __future__ import annotations

import argparse
import shutil
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEMPLATES = (
    ROOT
    / ".claude"
    / "plugins"
    / "workshop-marketing"
    / "skills"
    / "paginas"
    / "references"
    / "templates"
)

THEMES = {
    "flat_claro": "pagina_completa_flat_claro",
    "minimal_claro": "pagina_completa_minimal_claro",
    "glass_escuro": "pagina_completa_glass_escuro",
    "teal_claro": "pagina_completa_teal_claro",
    "purple_escuro": "pagina_completa_purple_escuro",
}


def main() -> None:
    p = argparse.ArgumentParser(
        description="Merge de página completa (melhor custo-benefício).",
    )
    p.add_argument(
        "--tema",
        required=True,
        choices=sorted(THEMES.keys()),
        help="Sufixo do tema (ex.: flat_claro)",
    )
    p.add_argument(
        "--copiar-entregas",
        action="store_true",
        help="Copia code.html para meus-produtos/{slug}/entregas/paginas/vendas-{slug}.html",
    )
    p.add_argument(
        "--slug",
        default=None,
        help="Slug do produto para pasta e nome do arquivo (padrão: conteúdo de meus-produtos/.ativo)",
    )
    p.add_argument(
        "--templates-root",
        default=None,
        help=(
            "Pasta que contém pagina_completa_{tema} e os blocos *_{tema} "
            "(cópia feita por workshop-copy-template-tema.py). "
            "Se omitido, usa o plugin em .claude/plugins/.../references/templates/"
        ),
    )
    args = p.parse_args()

    if args.templates_root:
        root = Path(args.templates_root).expanduser().resolve()
        folder = root / THEMES[args.tema]
    else:
        folder = TEMPLATES / THEMES[args.tema]
    script = folder / "build_merge.py"
    if not script.is_file():
        print("Arquivo não encontrado:", script, file=sys.stderr)
        sys.exit(1)

    subprocess.run([sys.executable, str(script)], cwd=str(folder), check=True)
    out_html = folder / "code.html"
    print("Gerado:", out_html, "bytes:", out_html.stat().st_size)

    if not args.copiar_entregas:
        return

    slug = args.slug
    if not slug:
        ativo = ROOT / "meus-produtos" / ".ativo"
        if ativo.is_file():
            slug = ativo.read_text(encoding="utf-8").strip()
    if not slug:
        print(
            "Defina --slug ou crie meus-produtos/.ativo com o identificador do produto.",
            file=sys.stderr,
        )
        sys.exit(2)

    dest_dir = ROOT / "meus-produtos" / slug / "entregas" / "paginas"
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / f"vendas-{slug}.html"
    shutil.copy2(out_html, dest)
    print("Copiado para:", dest)


if __name__ == "__main__":
    main()
