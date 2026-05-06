# -*- coding: utf-8 -*-
"""
DEPRECATED. Script descontinuado em favor de scripts/montar-pagina-copias.py.

Fluxo atual usa copias HTML isoladas em paginas/copias/ (geradas pela skill
ui-reverse-engineer com design preservado de cada print, sem harmonizacao
global). Este script dependia dos 5 temas VTSD com 16 blocos atomicos +
CSS variables globais, arquitetura abandonada.

Novo fluxo:
  /pagina-visual  -> gera paginas/copias/*.html + manifest.json
  py -3 scripts/montar-pagina-copias.py --slug X  -> monta vendas-X.html

Este arquivo e mantido so por compatibilidade com paginas ja geradas.

---

Build unificado da pagina de vendas VTSD.
Parseia a copy aprovada em meus-produtos/{slug}/entregas/copy-pagina/copy-{slug}.md,
preenche os 16 blocos atomicos do tema escolhido, roda o merge e entrega
meus-produtos/{slug}/entregas/paginas/vendas-{slug}.html.

Uso:
  py -3 scripts/build-pagina-vendas.py --slug meu-produto --tema flat_claro --dry-run
  py -3 scripts/build-pagina-vendas.py --slug meu-produto --tema flat_claro

Ordem do pipeline:
  1. Ler copy.md e parsear em 16 blocos estruturados
  2. --dry-run: validar estrutura e sair
  3. Copiar pasta do tema para meus-produtos/{slug}/entregas/paginas/templates-{tema}/
     (se nao existir ou --force)
  4. Substituir placeholders em cada code.html atomico usando a copy parseada
  5. Rodar build_merge.py do tema para gerar code.html final
  6. Copiar para meus-produtos/{slug}/entregas/paginas/vendas-{slug}.html
"""
from __future__ import annotations

import argparse
import html
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
TEMPLATES_CANDIDATES = (
    ROOT / ".claude" / "skills" / "paginas" / "references" / "templates",
    ROOT / ".claude" / "plugins" / "workshop-marketing" / "skills" / "paginas" / "references" / "templates",
)
TEMPLATES = next((p for p in TEMPLATES_CANDIDATES if p.is_dir()), TEMPLATES_CANDIDATES[0])

THEMES = ("flat_claro", "minimal_claro", "glass_escuro", "teal_claro", "purple_escuro")


# ============================================================
# PARSE DA COPY
# ============================================================


def _split_blocos(md_text: str) -> dict[int, str]:
    """Quebra o texto da copy em dicionario {numero_bloco: texto_do_bloco}."""
    pattern = re.compile(r"^##\s+Bloco\s+(\d+)\s*.\s*[^\n]+$", re.MULTILINE)
    matches = list(pattern.finditer(md_text))
    blocos: dict[int, str] = {}
    for i, m in enumerate(matches):
        num = int(m.group(1))
        start = m.end()
        end = matches[i + 1].start() if i + 1 < len(matches) else len(md_text)
        corpo = md_text[start:end].strip()
        corpo = re.sub(r"\n---\s*$", "", corpo).strip()
        blocos[num] = corpo
    return blocos


def _extract_field(body: str, label: str) -> str:
    """Extrai um campo no formato **Label**\\ntexto da linha seguinte ou ate a proxima label/section."""
    pat = re.compile(
        rf"\*\*{re.escape(label)}\*\*\s*\n(.*?)(?=\n\s*\*\*[^*]+\*\*|\n##|\Z)",
        re.DOTALL,
    )
    m = pat.search(body)
    return m.group(1).strip() if m else ""


def _extract_bullets_block(body: str) -> list[str]:
    """Extrai bullets apos marcador '**3 Bullets**' ou apos '**Bullets**'."""
    section = re.search(
        r"\*\*(?:3\s+Bullets|Bullets)\*\*\s*\n(.*?)(?=\n\s*\*\*[^*]+\*\*|\n##|\Z)",
        body,
        re.DOTALL,
    )
    if not section:
        return []
    txt = section.group(1)
    items = re.findall(r"^\s*-\s+(.+?)(?=\n\s*-\s+|\n\s*$|\Z)", txt, re.MULTILINE | re.DOTALL)
    return [re.sub(r"\s+", " ", it).strip() for it in items]


def _paragraphs(body: str) -> list[str]:
    """Quebra em paragrafos por linhas em branco, ignora citacoes > e headings ###."""
    # Remove secoes como **Label**\ntexto e citacoes
    txt = body
    # Quebra por duplo newline
    parts = re.split(r"\n\s*\n", txt)
    out = []
    for p in parts:
        p = p.strip()
        if not p:
            continue
        if p.startswith("#"):
            continue
        if p.startswith(">"):
            continue
        if p.startswith("**") and p.count("**") == 2 and "\n" not in p:
            continue
        out.append(p)
    return out


def _md_to_plain(t: str) -> str:
    """Remove marcas markdown basicas, preservando texto."""
    t = re.sub(r"\*\*(.+?)\*\*", r"\1", t)
    t = re.sub(r"\*(.+?)\*", r"\1", t)
    t = re.sub(r"`([^`]+)`", r"\1", t)
    t = re.sub(r"\[([^\]]+)\]\([^)]+\)", r"\1", t)
    return t.strip()


def parse_bloco_01_hero(body: str) -> dict[str, Any]:
    return {
        "headline": _md_to_plain(_extract_field(body, "Headline")),
        "subheadline": _md_to_plain(_extract_field(body, "Subheadline")),
        "bullets": [_md_to_plain(b) for b in _extract_bullets_block(body)],
        "video": _md_to_plain(_extract_field(body, "Indicação de vídeo") or _extract_field(body, "Indicacao de video")),
        "button": _md_to_plain(_extract_field(body, "Texto do botão") or _extract_field(body, "Texto do botao")),
    }


def parse_bloco_02_dor(body: str) -> dict[str, Any]:
    paras = _paragraphs(body)
    # Primeiro paragrafo costuma ser a cena de entrada (curta). H2 ideal: primeira frase marcante.
    headline = paras[0] if paras else ""
    # H2 do bloco: usa primeiro paragrafo como cena (limitamos a 140 chars)
    return {
        "headline": _md_to_plain(headline),
        "subheadline": _md_to_plain(paras[1]) if len(paras) > 1 else "",
        "paragrafos": [_md_to_plain(p) for p in paras],
    }


def parse_bloco_03_paliativo(body: str) -> dict[str, Any]:
    # Formato: intro, depois 4 paliativos cada com **Nome (preco/detalhe)** seguido de descricao.
    paras = _paragraphs(body)
    intro = _md_to_plain(paras[0]) if paras else ""
    bridge = _md_to_plain(paras[-1]) if len(paras) > 1 else ""
    # Itens: **Titulo**\n descricao. Capturamos por blocos que comecam com **.
    itens: list[dict[str, str]] = []
    item_pat = re.compile(
        r"\*\*([^*\n]+?)\*\*\n(.+?)(?=\n\*\*[^*\n]+?\*\*\n|\Z)",
        re.DOTALL,
    )
    for m in item_pat.finditer(body):
        titulo = m.group(1).strip()
        desc = _md_to_plain(re.sub(r"\s+", " ", m.group(2)).strip())
        # Pula se for label conhecida (Headline, Subheadline, etc.)
        if titulo.lower() in {"headline", "subheadline", "3 bullets", "bullets", "texto do botão", "texto do botao"}:
            continue
        itens.append({"titulo": titulo, "descricao": desc})
    return {
        "intro": intro,
        "bridge": bridge,
        "itens": itens[:4],
    }


def parse_bloco_04_provas(body: str) -> dict[str, Any]:
    # Formato: intro, depois 3 blocos ">" com **[modelo] nome, meta** e quote
    intro_match = re.match(r"^(.*?)(?=\n>)", body, re.DOTALL)
    intro = _md_to_plain(intro_match.group(1).strip()) if intro_match else ""
    # Blocos de citacao separados por linha em branco
    depos_raw = re.findall(
        r"(>.*?)(?=\n\s*\n|\Z)",
        body,
        re.DOTALL,
    )
    depos: list[dict[str, str]] = []
    for raw in depos_raw:
        linhas = [l.lstrip("> ").strip() for l in raw.splitlines()]
        linhas = [l for l in linhas if l]
        if not linhas:
            continue
        # Primeira linha: nome + meta. Ultima linha tende a ter aspas.
        header = _md_to_plain(linhas[0])
        quote = _md_to_plain(linhas[-1])
        # Tira [modelo]
        header = re.sub(r"^\[modelo\]\s*", "", header).strip()
        quote = quote.strip('"')
        # Extrai nome + detalhes
        nome = header.split(",", 1)[0].strip() if "," in header else header
        detalhe = header.split(",", 1)[1].strip() if "," in header else ""
        depos.append({"nome": nome, "detalhe": detalhe, "header": header, "quote": quote})
    return {"intro": intro, "depoimentos": depos[:3]}


def parse_bloco_05_cta(body: str) -> dict[str, Any]:
    button = _md_to_plain(_extract_field(body, "Texto do botão") or _extract_field(body, "Texto do botao"))
    # Tira bloco do botao do corpo antes de extrair paragrafos
    body_sem_botao = re.sub(r"\*\*Texto do bot[aã]o\*\*\s*\n.*$", "", body, flags=re.DOTALL).strip()
    paras = _paragraphs(body_sem_botao)
    return {
        "headline": _md_to_plain(paras[0]) if paras else "",
        "subheadline": _md_to_plain(paras[1]) if len(paras) > 1 else "",
        "button": button,
    }


def parse_bloco_06_metodo(body: str) -> dict[str, Any]:
    # Extrai nome do metodo em **Metodo XXX. Nome completo**
    nome_metodo = ""
    nome_match = re.search(r"Chamo de\s*\*\*([^*]+)\*\*", body)
    if nome_match:
        nome_metodo = nome_match.group(1).strip()
    # Extrai etapas
    etapa_pat = re.compile(
        r"###\s+Etapa\s+(\d+)[.\s]+([^\n]+)\n+(.+?)(?=\n###\s+Etapa|\Z)",
        re.DOTALL,
    )
    etapas = []
    for m in etapa_pat.finditer(body):
        numero = m.group(1)
        titulo = _md_to_plain(m.group(2).strip())
        corpo_etapa = _md_to_plain(re.sub(r"\s+", " ", m.group(3)).strip())
        etapas.append({"numero": numero, "titulo": titulo, "corpo": corpo_etapa})
    # Filosofia: paragrafo em italico *(...)
    fil_match = re.search(r"\*\(([^)]+)\)\*|\*([^*\n]{50,})\*", body)
    filosofia = ""
    if fil_match:
        filosofia = _md_to_plain(fil_match.group(1) or fil_match.group(2) or "")
    # Intro (antes de qualquer ###)
    intro_match = re.match(r"^(.*?)(?=###\s+Etapa|Chamo de)", body, re.DOTALL)
    intro = _md_to_plain(intro_match.group(1).strip()) if intro_match else ""
    # Fechamento (apos ultima etapa)
    fecho_paras = _paragraphs(body)
    fecho = _md_to_plain(fecho_paras[-1]) if fecho_paras else ""
    return {
        "intro": intro,
        "nome_metodo": nome_metodo,
        "filosofia": filosofia,
        "etapas": etapas,
        "fecho": fecho,
    }


def parse_bloco_07_para_quem(body: str) -> dict[str, Any]:
    # Perfis em ### headers
    perfil_pat = re.compile(
        r"###\s+Para\s+([^\n]+)\n+((?:-\s+[^\n]+\n?)+)",
        re.MULTILINE,
    )
    perfis = []
    for m in perfil_pat.finditer(body):
        titulo = _md_to_plain(m.group(1).strip())
        bullets_raw = m.group(2)
        bullets = re.findall(r"^-\s+(.+)$", bullets_raw, re.MULTILINE)
        perfis.append({"titulo": titulo, "bullets": [_md_to_plain(b) for b in bullets]})
    # Nao para quem
    nao_match = re.search(r"###\s+N[aã]o\s+[eé]\s+para\s+quem\n+((?:-\s+[^\n]+\n?)+)", body)
    nao_bullets = []
    if nao_match:
        nao_bullets = [_md_to_plain(b) for b in re.findall(r"^-\s+(.+)$", nao_match.group(1), re.MULTILINE)]
    intro_match = re.match(r"^(.*?)(?=###)", body, re.DOTALL)
    intro = _md_to_plain(intro_match.group(1).strip()) if intro_match else ""
    return {"intro": intro, "perfis": perfis, "nao_para_quem": nao_bullets}


def parse_bloco_08_entregaveis(body: str) -> dict[str, Any]:
    # Lista com **Titulo** descricao. Valor estimado RS XXX
    intro_match = re.match(r"^(.*?)(?=\n-)", body, re.DOTALL)
    intro = _md_to_plain(intro_match.group(1).strip()) if intro_match else ""
    item_pat = re.compile(
        r"^-\s+\*\*([^*]+)\*\*\s*(.*?)(?=\n-\s+\*\*|\n\nValor\s+somado|\Z)",
        re.DOTALL | re.MULTILINE,
    )
    itens: list[dict[str, str]] = []
    for m in item_pat.finditer(body):
        titulo = _md_to_plain(m.group(1).strip())
        resto = _md_to_plain(re.sub(r"\s+", " ", m.group(2).strip()))
        # Separa descricao do valor
        valor_match = re.search(r"(Valor\s+estimado\s+R\$?[\s]*[\d.,]+)", resto)
        valor = valor_match.group(1) if valor_match else ""
        desc = re.sub(r"\.\s*Valor\s+estimado.*$", "", resto).strip(" .")
        itens.append({"titulo": titulo, "descricao": desc, "valor": valor})
    total_match = re.search(r"Valor\s+somado[^\n]*?(R\$?[\s]*[\d.,]+)", body)
    total = total_match.group(1) if total_match else ""
    return {"intro": intro, "itens": itens, "total": total}


def parse_bloco_09_bonus(body: str) -> dict[str, Any]:
    intro_match = re.match(r"^(.*?)(?=###)", body, re.DOTALL)
    intro = _md_to_plain(intro_match.group(1).strip()) if intro_match else ""
    bonus_pat = re.compile(
        r"###\s+B[oô]nus\s+(\d+)[.\s]+([^\n]+)\n+(.*?)(?=\n###\s+B[oô]nus|\nValor\s+somado|\Z)",
        re.DOTALL,
    )
    bonus: list[dict[str, str]] = []
    for m in bonus_pat.finditer(body):
        numero = m.group(1)
        titulo = _md_to_plain(m.group(2).strip())
        corpo = _md_to_plain(re.sub(r"\s+", " ", m.group(3)).strip())
        valor_match = re.search(r"\*\*Valor:\s*(R\$?[\s]*[\d.,]+)\*\*", m.group(3))
        valor = valor_match.group(1) if valor_match else ""
        desc = re.sub(r"\s*\*\*Valor:.*?\*\*\s*$", "", corpo).strip()
        bonus.append({"numero": numero, "titulo": titulo, "descricao": desc, "valor": valor})
    total_match = re.search(r"Valor\s+somado[^\n]*?(R\$?[\s]*[\d.,]+)", body)
    total = total_match.group(1) if total_match else ""
    return {"intro": intro, "bonus": bonus, "total": total}


def parse_bloco_10_stack(body: str) -> dict[str, Any]:
    # Extrai linhas da tabela markdown
    linhas: list[dict[str, str]] = []
    for m in re.finditer(r"^\|\s*([^|\n]+?)\s*\|\s*([^|\n]+?)\s*\|$", body, re.MULTILINE):
        item = _md_to_plain(m.group(1).strip())
        valor = _md_to_plain(m.group(2).strip())
        if item.lower().startswith("---") or valor.lower().startswith("---"):
            continue
        if item.lower() == "item" and valor.lower().startswith("valor"):
            continue
        if "total" in item.lower():
            continue
        linhas.append({"item": item, "valor": valor})
    total_match = re.search(r"Valor\s+total\s+somado[^\n]*?(R\$?[\s]*[\d.,]+)", body)
    total = total_match.group(1) if total_match else ""
    preco_vista_match = re.search(r"paga\s+(R\$?[\s]*[\d.,]+)\s+[aà]\s+vista", body, re.IGNORECASE)
    preco_parc_match = re.search(r"(\d+x\s+de\s+R\$?[\s]*[\d.,]+)", body)
    preco_vista = preco_vista_match.group(1) if preco_vista_match else ""
    preco_parc = preco_parc_match.group(1) if preco_parc_match else ""
    button = _md_to_plain(_extract_field(body, "Texto do botão") or _extract_field(body, "Texto do botao"))
    # Valor real destacado
    valor_real_match = re.search(r"\*\*Valor\s+real\s+[^:]+:\s*(R\$?[\s]*[\d.,]+)\*\*", body)
    valor_real = valor_real_match.group(1) if valor_real_match else preco_vista
    return {
        "linhas": linhas,
        "total": total,
        "valor_real": valor_real,
        "preco_vista": preco_vista,
        "preco_parc": preco_parc,
        "button": button,
    }


def parse_bloco_11_provas2(body: str) -> dict[str, Any]:
    intro_match = re.match(r"^(.*?)(?=\n>)", body, re.DOTALL)
    intro = _md_to_plain(intro_match.group(1).strip()) if intro_match else ""
    # Cada depoimento e um bloco de > linhas, separado por linha em branco
    depos_raw = re.findall(r"((?:^>\s.*\n?)+)", body, re.MULTILINE)
    depos: list[dict[str, str]] = []
    for raw in depos_raw:
        texto = "\n".join(l.lstrip("> ").rstrip() for l in raw.splitlines() if l.strip())
        if not texto.strip():
            continue
        linhas = [l for l in texto.split("\n") if l.strip()]
        if not linhas:
            continue
        header = _md_to_plain(linhas[0])
        header = re.sub(r"^\[modelo\]\s*", "", header).strip()
        antes = ""
        depois = ""
        quote = ""
        for linha in linhas[1:]:
            linha_plain = _md_to_plain(linha)
            if linha.startswith("**Antes:**") or linha_plain.startswith("Antes:"):
                antes = re.sub(r"^Antes:\s*", "", linha_plain).strip()
            elif linha.startswith("**Depois:**") or linha_plain.startswith("Depois:"):
                depois = re.sub(r"^Depois:\s*", "", linha_plain).strip()
            elif linha_plain.startswith('"') or linha_plain.endswith('"'):
                quote = linha_plain.strip('"')
        if not quote and linhas:
            quote = _md_to_plain(linhas[-1]).strip('"')
        nome = header.split(",", 1)[0].strip() if "," in header else header
        detalhe = header.split(",", 1)[1].strip() if "," in header else ""
        depos.append({
            "nome": nome, "detalhe": detalhe, "header": header,
            "antes": antes, "depois": depois, "quote": quote,
        })
    return {"intro": intro, "depoimentos": depos[:3]}


def parse_bloco_12_suporte(body: str) -> dict[str, Any]:
    paras = _paragraphs(body)
    intro = _md_to_plain(paras[0]) if paras else ""
    # Cada paragrafo com **Titulo** no comeco e uma forma de suporte
    itens: list[dict[str, str]] = []
    item_pat = re.compile(r"\*\*([^*]+?)\*\*\s*(.+?)(?=\n\n\*\*|\Z)", re.DOTALL)
    for m in item_pat.finditer(body):
        titulo = _md_to_plain(m.group(1).strip().rstrip("."))
        desc = _md_to_plain(re.sub(r"\s+", " ", m.group(2)).strip())
        itens.append({"titulo": titulo, "descricao": desc})
    fecho = _md_to_plain(paras[-1]) if paras else ""
    return {"intro": intro, "itens": itens, "fecho": fecho}


def parse_bloco_13_garantia(body: str) -> dict[str, Any]:
    dias_match = re.search(r"\*\*(\d+)\s+dias\s+de\s+garantia[^*]*\*\*", body, re.IGNORECASE)
    dias = dias_match.group(1) if dias_match else "7"
    paras = _paragraphs(body)
    return {
        "dias": dias,
        "headline": _md_to_plain(paras[0]) if paras else "",
        "corpo": _md_to_plain(paras[1]) if len(paras) > 1 else "",
        "fecho": _md_to_plain(paras[-1]) if paras else "",
    }


def parse_bloco_14_autoridade(body: str) -> dict[str, Any]:
    paras = _paragraphs(body)
    # Nome do criador: primeira frase "Me chamo XXX"
    nome_match = re.search(r"Me\s+chamo\s+([^.,\n]+)", body)
    nome = _md_to_plain(nome_match.group(1).strip()) if nome_match else ""
    # Cargo: logo apos "Hoje sou"
    cargo_match = re.search(r"Hoje\s+sou\s+([^.]+)", body)
    cargo = _md_to_plain(cargo_match.group(1).strip()) if cargo_match else ""
    # Bio destacada: ultimo paragrafo em italico
    bio_match = re.search(r"\*([^*]{80,})\*\s*$", body)
    bio = _md_to_plain(bio_match.group(1)) if bio_match else ""
    return {
        "nome": nome,
        "cargo": cargo,
        "paragrafos": [_md_to_plain(p) for p in paras if not p.startswith("*")][:6],
        "bio": bio,
    }


def parse_bloco_15_faq(body: str) -> dict[str, Any]:
    faq_pat = re.compile(
        r"\*\*(\d+\.\s*[^*]+?)\*\*\s*\n+(.+?)(?=\n\*\*\d+\.|\Z)",
        re.DOTALL,
    )
    itens: list[dict[str, str]] = []
    for m in faq_pat.finditer(body):
        pergunta = _md_to_plain(m.group(1).strip().rstrip("?")) + "?"
        # Tira numero do inicio
        pergunta = re.sub(r"^\d+\.\s*", "", pergunta).strip()
        resposta = _md_to_plain(re.sub(r"\s+", " ", m.group(2)).strip())
        itens.append({"pergunta": pergunta, "resposta": resposta})
    return {"itens": itens}


def parse_bloco_16_oferta(body: str) -> dict[str, Any]:
    intro_match = re.match(r"^(.*?)(?=\n-)", body, re.DOTALL)
    intro = _md_to_plain(intro_match.group(1).strip()) if intro_match else ""
    # Itens
    itens: list[dict[str, str]] = []
    for m in re.finditer(r"^-\s+(.+)$", body, re.MULTILINE):
        linha = m.group(1)
        linha_plain = _md_to_plain(linha)
        # Separa valor no final
        v_match = re.search(r"(R\$?[\s]*[\d.,]+)\s*$", linha_plain)
        if v_match:
            titulo = linha_plain[: v_match.start()].strip(" .")
            valor = v_match.group(1)
        else:
            titulo = linha_plain.strip(" .")
            valor = ""
        itens.append({"titulo": titulo, "valor": valor})
    total_match = re.search(r"Valor\s+total\s+somado[:\s]*\*?\*?\s*(R\$?[\s]*[\d.,]+)", body)
    total = total_match.group(1) if total_match else ""
    preco_vista_match = re.search(r"\*\*(R\$?[\s]*[\d.,]+)\s+[aà]\s+vista\*\*", body)
    preco_vista = preco_vista_match.group(1) if preco_vista_match else ""
    preco_parc_match = re.search(r"\*\*(\d+x\s+de\s+R\$?[\s]*[\d.,]+[^*]*)\*\*", body)
    preco_parc = preco_parc_match.group(1).strip() if preco_parc_match else ""
    button = _md_to_plain(_extract_field(body, "Texto do botão") or _extract_field(body, "Texto do botao"))
    # Fecho: ultimo paragrafo antes do botao/disclaimer
    paras = _paragraphs(body)
    fecho_candidatos = [p for p in paras if not p.startswith("-") and "botão" not in p.lower() and "botao" not in p.lower()]
    fecho = _md_to_plain(fecho_candidatos[-1]) if fecho_candidatos else ""
    disclaimer_match = re.search(r"\*\(([^)]+)\)\*|\*([^*\n]{30,})\*\s*$", body)
    disclaimer = ""
    if disclaimer_match:
        disclaimer = _md_to_plain(disclaimer_match.group(1) or disclaimer_match.group(2) or "")
    return {
        "intro": intro,
        "itens": itens,
        "total": total,
        "preco_vista": preco_vista,
        "preco_parc": preco_parc,
        "button": button,
        "fecho": fecho,
        "disclaimer": disclaimer,
    }


PARSERS = {
    1: parse_bloco_01_hero,
    2: parse_bloco_02_dor,
    3: parse_bloco_03_paliativo,
    4: parse_bloco_04_provas,
    5: parse_bloco_05_cta,
    6: parse_bloco_06_metodo,
    7: parse_bloco_07_para_quem,
    8: parse_bloco_08_entregaveis,
    9: parse_bloco_09_bonus,
    10: parse_bloco_10_stack,
    11: parse_bloco_11_provas2,
    12: parse_bloco_12_suporte,
    13: parse_bloco_13_garantia,
    14: parse_bloco_14_autoridade,
    15: parse_bloco_15_faq,
    16: parse_bloco_16_oferta,
}


def parse_copy(md_path: Path) -> dict[int, dict[str, Any]]:
    txt = md_path.read_text(encoding="utf-8")
    blocos_raw = _split_blocos(txt)
    parsed: dict[int, dict[str, Any]] = {}
    for num, parser in PARSERS.items():
        body = blocos_raw.get(num, "")
        if not body:
            parsed[num] = {}
            continue
        parsed[num] = parser(body)
    return parsed


def validate(data: dict[int, dict[str, Any]]) -> list[str]:
    erros: list[str] = []
    if not data.get(1, {}).get("headline"):
        erros.append("Bloco 01: headline vazia")
    if not data.get(1, {}).get("subheadline"):
        erros.append("Bloco 01: subheadline vazia")
    if len(data.get(1, {}).get("bullets") or []) < 3:
        erros.append("Bloco 01: esperado 3 bullets, encontrados " + str(len(data.get(1, {}).get("bullets") or [])))
    if len(data.get(3, {}).get("itens") or []) < 3:
        erros.append("Bloco 03: esperados 4 paliativos")
    if len(data.get(4, {}).get("depoimentos") or []) < 3:
        erros.append("Bloco 04: esperados 3 depoimentos")
    if len(data.get(6, {}).get("etapas") or []) < 3:
        erros.append("Bloco 06: esperado ao menos 3 etapas do metodo")
    if len(data.get(7, {}).get("perfis") or []) < 3:
        erros.append("Bloco 07: esperados ao menos 3 perfis")
    if len(data.get(8, {}).get("itens") or []) < 3:
        erros.append("Bloco 08: esperados entregaveis")
    if len(data.get(9, {}).get("bonus") or []) < 3:
        erros.append("Bloco 09: esperados 3 bonus")
    if len(data.get(10, {}).get("linhas") or []) < 3:
        erros.append("Bloco 10: esperada tabela de stack")
    if not data.get(10, {}).get("preco_vista") and not data.get(10, {}).get("valor_real"):
        erros.append("Bloco 10: preco nao encontrado")
    if len(data.get(15, {}).get("itens") or []) < 3:
        erros.append("Bloco 15: esperadas perguntas de FAQ")
    if not data.get(16, {}).get("preco_vista"):
        erros.append("Bloco 16: preco final nao encontrado")
    return erros


# ============================================================
# COPIA DOS TEMPLATES PARA A PASTA DO PRODUTO
# ============================================================


def copy_tema(tema: str, slug: str, force: bool) -> Path:
    """Replica workshop-copy-template-tema.py."""
    suf = f"_{tema}"
    mid = f"_{tema}_"
    to_copy: list[Path] = []
    for p in sorted(TEMPLATES.iterdir()):
        if not p.is_dir():
            continue
        n = p.name
        if n == f"pagina_completa_{tema}" or n.endswith(suf) or mid in n:
            to_copy.append(p)
    if not to_copy:
        raise SystemExit(f"Nenhuma pasta encontrada para o tema '{tema}' em {TEMPLATES}")
    dest_root = ROOT / "meus-produtos" / slug / "entregas" / "paginas" / f"templates-{tema}"
    if dest_root.exists():
        if force:
            shutil.rmtree(dest_root)
        else:
            return dest_root
    dest_root.mkdir(parents=True, exist_ok=True)
    for src in to_copy:
        shutil.copytree(src, dest_root / src.name)
    return dest_root


# ============================================================
# HELPERS DE SUBSTITUICAO HTML
# ============================================================


def _esc(t: str) -> str:
    return html.escape(t or "", quote=False)


def _replace_tag_content(source: str, pattern: str, replacement: str, count: int = 1) -> str:
    """Substitui apenas o conteudo de tag casado por pattern. Pattern precisa ter 1 grupo com o conteudo."""
    def _sub(m: re.Match) -> str:
        full = m.group(0)
        inner = m.group(1)
        return full.replace(inner, replacement, 1)
    return re.sub(pattern, _sub, source, count=count, flags=re.DOTALL)


def _replace_sequence(source: str, pattern: str, values: list[str]) -> str:
    """Substitui as N primeiras ocorrencias do pattern (com 3 grupos: abertura, conteudo, fechamento)
    pelos N valores na lista values. Ocorrencias apos N ficam inalteradas.
    Tolerante a replacements que ainda casam o pattern (nao causa loop).
    """
    idx = [0]
    def repl(m: re.Match) -> str:
        i = idx[0]
        idx[0] += 1
        if i < len(values):
            return m.group(1) + values[i] + m.group(3)
        return m.group(0)
    return re.sub(pattern, repl, source, flags=re.DOTALL)


def _replace_first(source: str, pattern: str, value: str) -> str:
    """Substitui apenas a primeira ocorrencia (3 grupos). Equivalente a _replace_sequence com [value]."""
    return _replace_sequence(source, pattern, [value])


def _read(p: Path) -> str:
    return p.read_text(encoding="utf-8")


def _write(p: Path, t: str) -> None:
    p.write_text(t, encoding="utf-8")


# ============================================================
# SUBSTITUICOES POR BLOCO (tema-agnostico quando possivel)
# ============================================================


def fill_hero(tema_root: Path, tema: str, d: dict[str, Any]) -> None:
    path = tema_root / f"hero_{tema}" / "code.html"
    if not path.is_file():
        return
    t = _read(path)
    if tema == "teal_claro":
        t = _fill_hero_teal_claro(t, d)
        _write(path, t)
        return
    headline = _esc(d.get("headline", ""))
    subheadline = _esc(d.get("subheadline", ""))
    bullets = [_esc(b) for b in (d.get("bullets") or [])][:3]
    button = _esc(d.get("button", "") or "Quero conhecer")

    if headline:
        t = _replace_first(t, r"(<h1[^>]*>)(.*?)(</h1>)", headline)
    if subheadline:
        t = _replace_first(t, r'(<p class="text-lg text-gray-500[^"]*"[^>]*>)(.*?)(</p>)', subheadline)
    if bullets:
        t = _replace_sequence(t, r'(<span class="text-ink font-medium text-\[15px\]">)(.*?)(</span>)', bullets)
    # Botao do hero
    novo_botao = (
        "\n                        " + button +
        '\n                        <span class="material-symbols-outlined text-lg">arrow_forward</span>\n                    '
    )
    t = _replace_first(t, r'(<button[^>]*class="[^"]*cta-button[^"]*"[^>]*>)(.*?)(</button>)', novo_botao)
    # Titulo do iframe
    t = re.sub(
        r'title="[^"]*"',
        'title="Apresentacao do produto"',
        t,
        count=1,
    )
    _write(path, t)


def fill_dor(tema_root: Path, tema: str, d: dict[str, Any]) -> None:
    path = tema_root / f"dor_{tema}" / "code.html"
    if not path.is_file():
        return
    t = _read(path)
    if tema == "teal_claro":
        t = _fill_dor_teal_claro(t, d)
        _write(path, t)
        return
    headline = _esc(d.get("headline", ""))
    sub = _esc(d.get("subheadline", ""))
    if headline:
        t = _replace_first(t, r'(<h2 class="text-3xl[^"]*"[^>]*>)(.*?)(</h2>)', headline)
    if sub:
        t = _replace_first(t, r'(<p class="text-lg text-gray-500[^"]*"[^>]*>)(.*?)(</p>)', sub)
    # Os 4 cards de dor derivam de 4 frases curtas dos paragrafos
    paras = d.get("paragrafos") or []
    cards_fonte: list[tuple[str, str]] = []
    for p in paras:
        if len(cards_fonte) >= 4:
            break
        for frase in re.split(r"(?<=[.!?])\s+", p):
            frase = frase.strip()
            if 30 <= len(frase) <= 180:
                palavras = frase.split()
                titulo = " ".join(palavras[:6]).strip(" .,")
                cards_fonte.append((titulo, frase))
                if len(cards_fonte) >= 4:
                    break
    titulos = [_esc(tit) for tit, _ in cards_fonte[:4]]
    descs = [_esc(desc) for _, desc in cards_fonte[:4]]
    if titulos:
        t = _replace_sequence(t, r'(<h3 class="text-lg font-bold[^"]*"[^>]*>)(.*?)(</h3>)', titulos)
    if descs:
        t = _replace_sequence(t, r'(<p class="text-\[15px\] text-gray-500[^"]*"[^>]*>)(.*?)(</p>)', descs)
    _write(path, t)


def fill_paliativo(tema_root: Path, tema: str, d: dict[str, Any]) -> None:
    path = tema_root / f"paliativo_{tema}" / "code.html"
    if not path.is_file():
        return
    t = _read(path)
    if tema == "teal_claro":
        t = _fill_paliativo_teal_claro(t, d)
        _write(path, t)
        return
    intro = d.get("intro", "")
    # Headline curta (1a frase do intro) e subheadline (bridge curto)
    primeira_frase = re.split(r"(?<=[.!?])\s+", intro, maxsplit=1)[0] if intro else ""
    headline_txt = _esc(primeira_frase[:140] or "Paliativos que nao resolvem")
    t = _replace_first(t, r'(<h2[^>]*class="[^"]*"[^>]*>)(.*?)(</h2>)', headline_txt)
    # Subheadline (segunda frase do intro)
    demais = re.split(r"(?<=[.!?])\s+", intro, maxsplit=1)
    sub_txt = _esc((demais[1] if len(demais) > 1 else intro)[:240])
    t = _replace_first(t, r'(<p class="mt-6 text-base[^"]*"[^>]*>)(.*?)(</p>)', sub_txt)
    # 4 cards
    itens = d.get("itens") or []
    titulos = [_esc(it.get("titulo", "")) for it in itens[:4]]
    descs = [_esc(it.get("descricao", "")) for it in itens[:4]]
    if titulos:
        t = _replace_sequence(t, r'(<h3 class="text-base md:text-lg font-semibold"[^>]*>)(.*?)(</h3>)', titulos)
    if descs:
        t = _replace_sequence(t, r'(<p class="text-sm md:text-\[15px\][^"]*"[^>]*>)(.*?)(</p>)', descs)
    bridge = d.get("bridge", "")
    if bridge:
        t = _replace_first(t, r'(<p class="text-base md:text-lg font-light[^"]*"[^>]*>)(.*?)(</p>)', _esc(bridge))
    _write(path, t)


def fill_provas(tema_root: Path, tema: str, d: dict[str, Any]) -> None:
    path = tema_root / f"provas_sociais_{tema}" / "code.html"
    if not path.is_file():
        return
    t = _read(path)
    if tema == "teal_claro":
        t = _fill_provas_teal_claro(t, d)
        _write(path, t)
        return
    depos = d.get("depoimentos") or []
    nomes = [_esc(dep.get("nome", "")) for dep in depos[:3]]
    detalhes = [_esc(dep.get("detalhe", "")[:60]) for dep in depos[:3]]
    quotes = [_esc(dep.get("quote", "")) for dep in depos[:3]]
    if nomes:
        t = _replace_sequence(t, r'(<p class="font-semibold text-base"[^>]*>)(.*?)(</p>)', nomes)
    if detalhes:
        t = _replace_sequence(t, r'(<p class="text-xs text-gray-500"[^>]*>)(.*?)(</p>)', detalhes)
    if quotes:
        t = _replace_sequence(t, r'(<p class="text-sm font-light text-ink leading-relaxed"[^>]*>)(.*?)(</p>)', quotes)
    _write(path, t)


def fill_cta(tema_root: Path, tema: str, d: dict[str, Any]) -> None:
    path = tema_root / f"cta_{tema}" / "code.html"
    if not path.is_file():
        return
    t = _read(path)
    if tema == "teal_claro":
        t = _fill_cta_teal_claro(t, d)
        _write(path, t)
        return
    headline = _esc(d.get("headline", ""))
    sub = _esc(d.get("subheadline", ""))
    button = _esc(d.get("button", "") or "Quero ver a oferta")
    if headline:
        t = _replace_first(t, r'(<h2 class="fadeUp[^"]*"[^>]*>)(.*?)(</h2>)', headline)
    if sub:
        t = _replace_first(t, r'(<p class="fadeUp fadeUp-delay-1[^"]*"[^>]*>)(.*?)(</p>)', sub)
    # Esconde preco intermediario (usamos so na oferta final)
    t = re.sub(
        r'<div class="fadeUp fadeUp-delay-2 mt-10">.*?</div>',
        '<div class="fadeUp fadeUp-delay-2 mt-10" style="display:none"></div>',
        t,
        count=1,
        flags=re.DOTALL,
    )
    novo_botao = (
        "\n          " + button +
        '\n          <span class="material-symbols-outlined">arrow_forward</span>\n        '
    )
    t = _replace_first(t, r'(<button class="cta-btn"[^>]*>)(.*?)(</button>)', novo_botao)
    _write(path, t)


def _scope_css(css: str, scope: str) -> str:
    """Escopa regras CSS para `scope` (ex.: ".furadeira-embed").
    - html, body, * viram o proprio scope (substitui, nao prefixa) pra nao vazar
      nos elementos globais da pagina onde a furadeira e injetada.
    - :root e @-rules permanecem inalterados.
    - Demais seletores recebem prefixo `scope `.
    """
    out: list[str] = []
    for bloco in re.split(r"(\})", css):
        if not bloco.strip():
            out.append(bloco)
            continue
        if bloco == "}":
            out.append(bloco)
            continue
        if "{" in bloco:
            sel_part, _, decl = bloco.partition("{")
            seletores = [s.strip() for s in sel_part.split(",") if s.strip()]
            novos = []
            for s in seletores:
                if s.startswith("@") or s == ":root":
                    novos.append(s)
                elif s in ("html", "body"):
                    # body/html da furadeira: vira o proprio scope pra nao vazar
                    novos.append(scope)
                elif s == "*":
                    # reset universal: escopa dentro do container
                    novos.append(f"{scope} *")
                elif s.startswith(":"):
                    novos.append(s)
                else:
                    novos.append(f"{scope} {s}")
            out.append(", ".join(novos) + "{" + decl)
        else:
            out.append(bloco)
    return "".join(out)


def _try_inject_furadeira(tema_root: Path, tema: str, slug: str, nome: str, filosofia: str) -> bool:
    """Se existir entregas/furadeira-visual.html, substitui o body do metodo_{tema}/code.html
    pela furadeira embarcada em wrapper .furadeira-embed com CSS scoped.
    Retorna True se injetou, False se nao.
    """
    fur_path = ROOT / "meus-produtos" / slug / "entregas" / "furadeira-visual.html"
    if not fur_path.is_file():
        return False
    metodo_path = tema_root / f"metodo_{tema}" / "code.html"
    if not metodo_path.is_file():
        return False

    fur_html = fur_path.read_text(encoding="utf-8")
    css_match = re.search(r"<style>(.*?)</style>", fur_html, re.DOTALL | re.IGNORECASE)
    body_match = re.search(r"<body[^>]*>(.*?)</body>", fur_html, re.DOTALL | re.IGNORECASE)
    if not body_match:
        return False
    css_fur = css_match.group(1) if css_match else ""
    body_fur = body_match.group(1).strip()
    # Remove as fonts google se ja tiver, vamos reimportar no head do metodo
    fonts_match = re.search(
        r'<link\s+href="https://fonts\.googleapis\.com/css2[^"]*"[^>]*>',
        fur_html,
    )
    fonts_link = fonts_match.group(0) if fonts_match else ""

    css_scoped = _scope_css(css_fur, ".furadeira-embed")

    # Novo code.html do metodo: mantem a section-metodo do tema (pra o merge continuar funcionando)
    # e injeta a furadeira como conteudo principal da section.
    header_line = f"{nome}" if nome else "Metodo"
    sub_line = filosofia if filosofia else ""
    novo_html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
<meta charset="UTF-8">
{fonts_link}
<style>
/* Furadeira embedded */
{css_scoped}

/* Wrapper neutro pra section-metodo */
.section-metodo {{ padding: 48px 0; }}
</style>
</head>
<body>
<section class="section-metodo py-16 sm:py-20 px-6">
  <div class="max-w-5xl mx-auto text-center mb-10">
    <h2 class="fadeUp font-inter font-700 text-ink text-2xl sm:text-3xl leading-snug tracking-tight">{_esc(header_line)}</h2>
  </div>
  <div class="furadeira-embed">
    {body_fur}
  </div>
</section>
</body>
</html>
"""
    metodo_path.write_text(novo_html, encoding="utf-8")
    return True


def fill_metodo(tema_root: Path, tema: str, d: dict[str, Any]) -> None:
    path = tema_root / f"metodo_{tema}" / "code.html"
    if not path.is_file():
        return
    nome = d.get("nome_metodo", "") or "Metodo do produto"
    filosofia = d.get("filosofia", "") or d.get("intro", "")[:280]
    # Se existir furadeira-visual.html, usa ela como bloco do metodo
    slug = d.get("__slug__", "")
    if slug and _try_inject_furadeira(tema_root, tema, slug, nome, filosofia):
        return
    if tema == "teal_claro":
        t = _read(path)
        t = _fill_metodo_teal_claro(t, d)
        _write(path, t)
        return
    # Fallback: preenche os 3 cards do template com etapas da copy
    t = _read(path)
    nome_esc = _esc(nome)
    filosofia_esc = _esc(filosofia)
    t = _replace_first(t, r'(<h2 class="fadeUp[^"]*"[^>]*>)(.*?)(</h2>)', nome_esc)
    t = _replace_first(t, r'(<p class="fadeUp fadeUp-delay-1[^"]*"[^>]*>)(.*?)(</p>)', filosofia_esc)
    etapas = d.get("etapas") or []
    if len(etapas) > 3:
        selecionadas = [etapas[0], etapas[len(etapas) // 2], etapas[-1]]
    else:
        selecionadas = etapas[:3]
    titulos: list[str] = []
    todos_bullets: list[str] = []
    for etapa in selecionadas:
        titulo = f'Etapa {etapa.get("numero", "")}. {etapa.get("titulo", "")}'
        titulos.append(_esc(titulo))
        corpo = etapa.get("corpo", "")
        frases = re.split(r"(?<=[.!?])\s+", corpo)
        bullets_etapa = [f.strip() for f in frases if 20 <= len(f.strip()) <= 180][:3]
        while len(bullets_etapa) < 3:
            bullets_etapa.append("")
        todos_bullets.extend([_esc(b) for b in bullets_etapa])
    if titulos:
        t = _replace_sequence(
            t,
            r'(<h3 class="font-inter font-bold text-ink text-lg mb-3"[^>]*>)(.*?)(</h3>)',
            titulos,
        )
    if todos_bullets:
        t = _replace_sequence(t, r'(<li>)(.*?)(</li>)', todos_bullets)
    _write(path, t)


def fill_para_quem(tema_root: Path, tema: str, d: dict[str, Any]) -> None:
    path = tema_root / f"para_quem_{tema}" / "code.html"
    if not path.is_file():
        return
    t = _read(path)
    if tema == "teal_claro":
        t = _fill_para_quem_teal_claro(t, d)
        _write(path, t)
        return
    perfis = d.get("perfis") or []
    nao_para = d.get("nao_para_quem") or []
    intro = _esc(d.get("intro", "")[:280])
    if intro:
        t = _replace_first(t, r'(<p class="[^"]*text-gray-500[^"]*"[^>]*>)(.*?)(</p>)', intro)
    # "Para quem e" card: pega o titulo do perfil como criterio (ate 5)
    positivos: list[str] = []
    for perfil in perfis[:5]:
        titulo = perfil.get("titulo", "").strip()
        if titulo:
            # Prefixa so se ja nao tiver algo coerente
            if not titulo.lower().startswith(("para ", "e ", "contador", "para o", "para a")):
                titulo = f"Para o perfil: {titulo}"
            positivos.append(_esc(titulo))
    # Completa com bullets do primeiro perfil se faltar
    if perfis and len(positivos) < 4:
        for b in perfis[0].get("bullets", []):
            if len(positivos) >= 4:
                break
            positivos.append(_esc(b))
    # Substitui nas 4 primeiras ocorrencias de <span> dentro de check-row (sem class)
    if positivos:
        t = _replace_sequence(
            t,
            r'(<span class="icon-yes"><span class="material-symbols-outlined"[^>]*>check</span></span>\s*<span>)([^<]+)(</span>)',
            positivos[:4],
        )
    # "Para quem nao e" card: usa bullets de nao_para_quem
    negativos = [_esc(b) for b in nao_para[:4]]
    if negativos:
        t = _replace_sequence(
            t,
            r'(<span class="icon-no"><span class="material-symbols-outlined"[^>]*>close</span></span>\s*<span class="text-gray-400">)([^<]+)(</span>)',
            negativos,
        )
    _write(path, t)


def fill_entregaveis(tema_root: Path, tema: str, d: dict[str, Any]) -> None:
    path = tema_root / f"entregaveis_{tema}" / "code.html"
    if not path.is_file():
        return
    t = _read(path)
    if tema == "teal_claro":
        t = _fill_entregaveis_teal_claro(t, d)
        _write(path, t)
        return
    itens = d.get("itens") or []
    titulos = [_esc(it.get("titulo", "")) for it in itens[:8]]
    descs = [_esc(it.get("descricao", "")) for it in itens[:8]]
    if titulos:
        t = _replace_sequence(t, r'(<h3 class="[^"]*"[^>]*>)(.*?)(</h3>)', titulos)
    if descs:
        t = _replace_sequence(t, r'(<p class="[^"]*text-gray-500[^"]*"[^>]*>)(.*?)(</p>)', descs)
    _write(path, t)


def fill_bonus(tema_root: Path, tema: str, d: dict[str, Any]) -> None:
    path = tema_root / f"bonus_{tema}" / "code.html"
    if not path.is_file():
        return
    t = _read(path)
    if tema == "teal_claro":
        t = _fill_bonus_teal_claro(t, d)
        _write(path, t)
        return
    bonus = d.get("bonus") or []
    titulos = [_esc(f'Bonus {b.get("numero", "")}. {b.get("titulo", "")}') for b in bonus[:3]]
    descs = [_esc(b.get("descricao", "")) for b in bonus[:3]]
    valores = [b.get("valor", "") for b in bonus[:3] if b.get("valor")]
    if titulos:
        t = _replace_sequence(t, r'(<h3 class="[^"]*"[^>]*>)(.*?)(</h3>)', titulos)
    if descs:
        t = _replace_sequence(t, r'(<p class="[^"]*text-gray-500[^"]*"[^>]*>)(.*?)(</p>)', descs)
    if valores:
        idx = [0]
        def repl(m: re.Match) -> str:
            i = idx[0]
            idx[0] += 1
            if i < len(valores):
                return valores[i]
            return m.group(0)
        t = re.sub(r'R\$[\s]*[\d.,]+', repl, t)
    _write(path, t)


def fill_stack(tema_root: Path, tema: str, d: dict[str, Any]) -> None:
    path = tema_root / f"stack_valor_{tema}" / "code.html"
    if not path.is_file():
        return
    t = _read(path)
    if tema == "teal_claro":
        t = _fill_stack_teal_claro(t, d)
        _write(path, t)
        return
    linhas = d.get("linhas") or []
    nomes = [_esc(l.get("item", "")) for l in linhas[:12]]
    valores = [_esc(l.get("valor", "")) for l in linhas[:12]]
    if nomes:
        t = _replace_sequence(
            t,
            r'(<span class="flex items-center"><span class="material-symbols-outlined">check</span>)([^<]+)(</span>)',
            nomes,
        )
    if valores:
        t = _replace_sequence(t, r'(<span class="font-semibold"[^>]*>)(.*?)(</span>)', valores)
    total = d.get("total", "")
    if total:
        t = _replace_first(t, r'(<span class="valor-total[^"]*"[^>]*>)(.*?)(</span>)', _esc(total))
    # Texto "Investimento hoje: R$ X a vista ou 12x de R$ Y" no rodape do card
    vista = d.get("preco_vista", "")
    parc = d.get("preco_parc", "")
    if vista or parc:
        partes = []
        if vista:
            partes.append(f"{vista} a vista")
        if parc:
            partes.append(parc)
        texto_invest = "Investimento hoje: " + " ou ".join(partes) + "."
        t = _replace_first(
            t,
            r'(<p class="text-sm font-light text-gray-500"[^>]*>)(.*?)(</p>)',
            _esc(texto_invest),
        )
    _write(path, t)


def fill_suporte(tema_root: Path, tema: str, d: dict[str, Any]) -> None:
    path = tema_root / f"suporte_{tema}" / "code.html"
    if not path.is_file():
        return
    t = _read(path)
    if tema == "teal_claro":
        t = _fill_suporte_teal_claro(t, d)
        _write(path, t)
        return
    intro = _esc(d.get("intro", "")[:280])
    if intro:
        t = _replace_first(t, r'(<p class="[^"]*text-gray-500[^"]*"[^>]*>)(.*?)(</p>)', intro)
    itens = d.get("itens") or []
    titulos = [_esc(it.get("titulo", "")) for it in itens[:6]]
    if titulos:
        t = _replace_sequence(t, r'(<h3 class="[^"]*"[^>]*>)(.*?)(</h3>)', titulos)
    _write(path, t)


def fill_garantia(tema_root: Path, tema: str, d: dict[str, Any]) -> None:
    path = tema_root / f"garantia_{tema}" / "code.html"
    if not path.is_file():
        return
    t = _read(path)
    if tema == "teal_claro":
        t = _fill_garantia_teal_claro(t, d)
        _write(path, t)
        return
    dias = d.get("dias", "7")
    headline = _esc(d.get("headline", ""))
    corpo = _esc(d.get("corpo", ""))
    # Substitui ocorrencias de "30 dias" ou "7 dias" no seletor do selo
    t = re.sub(r"\b(\d+)\s+dias\b", f"{dias} dias", t, count=2)
    if headline:
        t = re.sub(
            r'(<h2[^>]*>)(.*?)(</h2>)',
            lambda m: m.group(1) + headline + m.group(3),
            t,
            count=1,
            flags=re.DOTALL,
        )
    if corpo:
        t = re.sub(
            r'(<p class="[^"]*text-gray-500[^"]*"[^>]*>)(.*?)(</p>)',
            lambda m: m.group(1) + corpo + m.group(3),
            t,
            count=1,
            flags=re.DOTALL,
        )
    _write(path, t)


def fill_autoridade(tema_root: Path, tema: str, d: dict[str, Any]) -> None:
    path = tema_root / f"autoridade_{tema}" / "code.html"
    if not path.is_file():
        return
    t = _read(path)
    if tema == "teal_claro":
        t = _fill_autoridade_teal_claro(t, d)
        _write(path, t)
        return
    nome = _esc(d.get("nome", ""))
    cargo = _esc(d.get("cargo", ""))
    paragrafos = [_esc(p) for p in (d.get("paragrafos") or [])][:4]
    if nome:
        t = _replace_first(t, r'(<h2[^>]*>)(.*?)(</h2>)', nome)
    if paragrafos:
        t = _replace_sequence(t, r'(<p class="[^"]*text-gray-500[^"]*"[^>]*>)(.*?)(</p>)', paragrafos)
    if cargo:
        t = _replace_first(t, r'(<p class="[^"]*text-warm[^"]*"[^>]*>)(.*?)(</p>)', cargo)
    _write(path, t)


def fill_faq(tema_root: Path, tema: str, d: dict[str, Any]) -> None:
    path = tema_root / f"faq_{tema}" / "code.html"
    if not path.is_file():
        return
    t = _read(path)
    if tema == "teal_claro":
        t = _fill_faq_teal_claro(t, d)
        _write(path, t)
        return
    itens = d.get("itens") or []
    perguntas = [_esc(it.get("pergunta", "")) for it in itens[:10]]
    respostas = [_esc(it.get("resposta", "")) for it in itens[:10]]
    if perguntas:
        t = _replace_sequence(
            t,
            r'(<span class="faq-question[^"]*"[^>]*>|<span class="text-left[^"]*"[^>]*>)(.*?)(</span>)',
            perguntas,
        )
    if respostas:
        t = _replace_sequence(
            t,
            r'(<div class="faq-answer"[^>]*>\s*<p[^>]*>)(.*?)(</p>)',
            respostas,
        )
    _write(path, t)


def fill_oferta(tema_root: Path, tema: str, d: dict[str, Any]) -> None:
    path = tema_root / f"oferta_final_{tema}" / "code.html"
    if not path.is_file():
        return
    t = _read(path)
    if tema == "teal_claro":
        t = _fill_oferta_teal_claro(t, d)
        _write(path, t)
        return
    itens = d.get("itens") or []
    nomes = [_esc(it.get("titulo", "")) for it in itens[:12]]
    valores = [_esc(it.get("valor", "")) for it in itens[:12] if it.get("valor")]
    # Parag. descritiva do header da oferta (mt-6 text-base md:text-lg font-light text-gray-500)
    intro = d.get("intro", "") or d.get("fecho", "")
    if intro:
        t = _replace_first(
            t,
            r'(<p class="mt-6 text-base md:text-lg font-light text-gray-500[^"]*"[^>]*>)(.*?)(</p>)',
            _esc(intro[:320]),
        )
    if nomes:
        t = _replace_sequence(
            t,
            r'(<span class="flex items-center"><span class="material-symbols-outlined">check</span>)([^<]+)(</span>)',
            nomes,
        )
    if valores:
        t = _replace_sequence(t, r'(<span class="font-semibold"[^>]*>)(.*?)(</span>)', valores)
    vista = d.get("preco_vista", "")
    parc = d.get("preco_parc", "")
    # Preco principal (maior destaque): <p class="text-5xl md:text-6xl font-extrabold mt-2 leading-none">
    # Colocamos o preco parcelado (mais aspiracional) no destaque e o a vista embaixo.
    if parc:
        t = _replace_first(
            t,
            r'(<p class="text-5xl[^"]*font-extrabold[^"]*"[^>]*>)(.*?)(</p>)',
            _esc(parc),
        )
    if vista:
        # Texto "ou R$ X a vista..."
        t = _replace_first(
            t,
            r'(<p class="text-sm text-gray-500 mt-2"[^>]*>)(.*?)(</p>)',
            _esc(f"ou {vista} a vista"),
        )
    # Total ancorado (preco cheio dos bonus + entregaveis somados)
    total = d.get("total", "")
    if total:
        t = _replace_first(
            t,
            r'(<span class="valor-total[^"]*"[^>]*>)(.*?)(</span>)',
            _esc(total),
        )
    button = _esc(d.get("button", "") or "Quero minha vaga")
    # O botao no template eh um <a>, nao <button>
    t = re.sub(
        r'(<a class="cta-btn"[^>]*>)(.*?)(</a>)',
        lambda m: m.group(1) + "\n              " + button +
                  '\n              <span class="material-symbols-outlined">arrow_forward</span>\n            ' + m.group(3),
        t,
        count=1,
        flags=re.DOTALL,
    )
    _write(path, t)


# ============================================================
# HELPERS ESPECIFICOS DO TEMA teal_claro (classes BEM, nao tailwind)
# ============================================================


def _fill_hero_teal_claro(t: str, d: dict[str, Any]) -> str:
    headline = _esc(d.get("headline", ""))
    subheadline = _esc(d.get("subheadline", ""))
    bullets = [_esc(b) for b in (d.get("bullets") or [])][:3]
    button = _esc(d.get("button", "") or "Quero conhecer")
    if headline:
        t = _replace_first(t, r'(<h1 class="anim delay-2"[^>]*>)(.*?)(</h1>)', headline)
    if subheadline:
        t = _replace_first(t, r'(<p class="subtitle anim delay-3"[^>]*>)(.*?)(</p>)', subheadline)
    if bullets:
        t = _replace_sequence(
            t,
            r'(<li class="check-item">[\s\S]*?<span>)([^<]+)(</span>\s*</li>)',
            bullets,
        )
    t = re.sub(
        r'(<button class="cta-button"[^>]*>)(.*?)(<div class="arrow-circle")',
        lambda m: m.group(1) + f"\n          {button}\n          " + m.group(3),
        t,
        count=1,
        flags=re.DOTALL,
    )
    t = re.sub(r'(<span class="cta-sub"[^>]*>)(.*?)(</span>)', r'\1Acesso imediato ao metodo completo\3', t, count=1, flags=re.DOTALL)
    t = re.sub(r'title="[^"]*"', 'title="Apresentacao do produto"', t, count=1)
    return t


def _fill_dor_teal_claro(t: str, d: dict[str, Any]) -> str:
    headline = _esc(d.get("headline", ""))
    sub = _esc(d.get("subheadline", ""))
    if headline:
        t = _replace_first(t, r'(<h2 class="pain-headline"[^>]*>)(.*?)(</h2>)', headline)
    if sub:
        t = _replace_first(t, r'(<p class="pain-subheadline"[^>]*>)(.*?)(</p>)', sub)
    paras = d.get("paragrafos") or []
    cards_fonte: list[tuple[str, str]] = []
    for p in paras:
        if len(cards_fonte) >= 4:
            break
        for frase in re.split(r"(?<=[.!?])\s+", p):
            frase = frase.strip()
            if 30 <= len(frase) <= 200:
                palavras = frase.split()
                titulo = " ".join(palavras[:7]).strip(" .,")
                cards_fonte.append((titulo, frase))
                if len(cards_fonte) >= 4:
                    break
    while len(cards_fonte) < 4:
        cards_fonte.append(("", ""))
    titulos = [_esc(tit) for tit, _ in cards_fonte[:4]]
    descs = [_esc(desc) for _, desc in cards_fonte[:4]]
    t = _replace_sequence(t, r'(<h3 class="pain-card-title"[^>]*>)(.*?)(</h3>)', titulos)
    t = _replace_sequence(t, r'(<p class="pain-card-text"[^>]*>)(.*?)(</p>)', descs)
    # Texto ponte no rodape da secao
    bottom_candidatos = [p for p in paras if len(p) >= 60]
    bottom_txt = _esc(bottom_candidatos[-1][:320]) if bottom_candidatos else _esc(paras[-1][:320] if paras else "")
    if bottom_txt:
        t = _replace_first(t, r'(<p class="pain-bottom-text"[^>]*>)(.*?)(</p>)', bottom_txt)
    # CTA pill
    button_txt = "Quero conhecer o metodo"
    t = re.sub(
        r'(<a href="#" class="cta-pill"[^>]*>)(.*?)(<span class="material-symbols-outlined")',
        lambda m: m.group(1) + f"\n                {button_txt}\n                " + m.group(3),
        t,
        count=1,
        flags=re.DOTALL,
    )
    return t


def _fill_paliativo_teal_claro(t: str, d: dict[str, Any]) -> str:
    intro = d.get("intro", "")
    primeira = re.split(r"(?<=[.!?])\s+", intro, maxsplit=1)[0] if intro else ""
    headline_txt = _esc(primeira[:180] or "Paliativos que nao resolvem")
    t = _replace_first(t, r'(<h2 class="section-paliativo__headline"[^>]*>)(.*?)(</h2>)', headline_txt)
    demais = re.split(r"(?<=[.!?])\s+", intro, maxsplit=1)
    sub_txt = _esc((demais[1] if len(demais) > 1 else intro)[:280])
    if sub_txt:
        t = _replace_first(t, r'(<p class="section-paliativo__subtitle"[^>]*>)(.*?)(</p>)', sub_txt)
    itens = d.get("itens") or []
    titulos = [_esc(it.get("titulo", "")) for it in itens[:4]]
    descs = [_esc(it.get("descricao", "")) for it in itens[:4]]
    while len(titulos) < 4:
        titulos.append("")
        descs.append("")
    t = _replace_sequence(t, r'(<h3 class="paliativo-card__title"[^>]*>)(.*?)(</h3>)', titulos)
    t = _replace_sequence(t, r'(<p class="paliativo-card__text"[^>]*>)(.*?)(</p>)', descs)
    bridge = d.get("bridge", "")
    if bridge:
        t = _replace_first(
            t,
            r'(<div class="section-paliativo__bridge"[^>]*>\s*<p[^>]*>)(.*?)(</p>)',
            _esc(bridge[:320]),
        )
    return t


def _fill_provas_teal_claro(t: str, d: dict[str, Any]) -> str:
    depos = d.get("depoimentos") or []
    intro = d.get("intro", "")
    primeira = re.split(r"(?<=[.!?])\s+", intro, maxsplit=1)[0] if intro else ""
    headline_txt = _esc(primeira[:160] or "Quem aplicou ja esta vendo resultado")
    t = _replace_first(t, r'(<h2 class="section-provas__headline"[^>]*>)(.*?)(</h2>)', headline_txt)
    demais = re.split(r"(?<=[.!?])\s+", intro, maxsplit=1)
    sub_txt = _esc((demais[1] if len(demais) > 1 else intro)[:240])
    if sub_txt:
        t = _replace_first(t, r'(<p class="section-provas__subtitle"[^>]*>)(.*?)(</p>)', sub_txt)
    nomes = [_esc(dep.get("nome", "")) for dep in depos[:3]]
    detalhes = [_esc(dep.get("detalhe", "")[:80]) for dep in depos[:3]]
    while len(nomes) < 3:
        nomes.append("")
        detalhes.append("")
    t = _replace_sequence(t, r'(<span class="prova-card__name"[^>]*>)(.*?)(</span>)', nomes)
    t = _replace_sequence(t, r'(<span class="prova-card__location"[^>]*>)(.*?)(</span>)', detalhes)
    # 6 blocos prova-block__text: antes/depois para cada um dos 3 cards (sequencia A1, D1, A2, D2, A3, D3)
    textos: list[str] = []
    for dep in depos[:3]:
        antes = dep.get("antes") or dep.get("header") or dep.get("detalhe") or ""
        depois = dep.get("depois") or dep.get("quote") or ""
        textos.append(_esc(antes[:400]))
        textos.append(_esc(depois[:400]))
    while len(textos) < 6:
        textos.append("")
    t = _replace_sequence(t, r'(<p class="prova-block__text"[^>]*>)(.*?)(</p>)', textos)
    return t


def _fill_cta_teal_claro(t: str, d: dict[str, Any]) -> str:
    headline = _esc(d.get("headline", ""))
    sub = _esc(d.get("subheadline", ""))
    button = _esc(d.get("button", "") or "Quero ver a oferta")
    if headline:
        t = _replace_first(t, r'(<h2 class="cta-headline"[^>]*>)(.*?)(</h2>)', headline)
    if sub:
        t = _replace_first(t, r'(<p class="cta-text"[^>]*>)(.*?)(</p>)', sub)
    # Esconder container de preco intermediario (so usamos preco na oferta final)
    t = re.sub(
        r'<div style="margin-bottom: 2rem;">(.*?)</div>',
        '<div style="margin-bottom: 2rem; display:none">\\1</div>',
        t,
        count=1,
        flags=re.DOTALL,
    )
    t = re.sub(
        r'(<a href="#oferta" class="cta-btn"[^>]*>)(.*?)(<span class="arrow-circle")',
        lambda m: m.group(1) + f"\n          {button}\n          " + m.group(3),
        t,
        count=1,
        flags=re.DOTALL,
    )
    return t


def _fill_metodo_teal_claro(t: str, d: dict[str, Any]) -> str:
    nome = _esc(d.get("nome_metodo", "") or "Metodo do produto")
    filosofia = _esc((d.get("filosofia", "") or d.get("intro", ""))[:320])
    headline_html = f'O <span class="accent">{nome}</span> em 3 passos'
    t = _replace_first(t, r'(<h2 class="metodo-headline"[^>]*>)(.*?)(</h2>)', headline_html)
    if filosofia:
        t = _replace_first(t, r'(<p class="metodo-text"[^>]*>)(.*?)(</p>)', filosofia)
    etapas = d.get("etapas") or []
    if len(etapas) > 3:
        selecionadas = [etapas[0], etapas[len(etapas) // 2], etapas[-1]]
    else:
        selecionadas = etapas[:3]
    while len(selecionadas) < 3:
        selecionadas.append({"numero": "", "titulo": "", "corpo": ""})
    titulos = [_esc(e.get("titulo", "")) for e in selecionadas[:3]]
    t = _replace_sequence(t, r'(<h3 class="step-title"[^>]*>)(.*?)(</h3>)', titulos)
    # Cada passo tem 4 micro-steps. Distribui 4 frases do corpo em cada etapa.
    todos_bullets: list[str] = []
    for etapa in selecionadas[:3]:
        corpo = etapa.get("corpo", "")
        frases = [f.strip() for f in re.split(r"(?<=[.!?])\s+", corpo) if 15 <= len(f.strip()) <= 160]
        while len(frases) < 4:
            frases.append("")
        todos_bullets.extend([_esc(f) for f in frases[:4]])
    # Substitui o ultimo <span> de cada micro-step <li> (o texto vem apos o icone)
    t = _replace_sequence(
        t,
        r'(<ul class="micro-steps">[\s\S]*?)?(<li>\s*<span class="material-symbols-outlined"[^>]*>[^<]*</span>\s*)([^<]+)(</li>)',
        todos_bullets,
    )
    return t


def _fill_para_quem_teal_claro(t: str, d: dict[str, Any]) -> str:
    intro = d.get("intro", "")
    primeira = re.split(r"(?<=[.!?])\s+", intro, maxsplit=1)[0] if intro else ""
    headline_txt = _esc(primeira[:180] or "Este metodo foi pensado para um perfil especifico")
    t = _replace_first(t, r'(<h2 class="section-paraquem__headline"[^>]*>)(.*?)(</h2>)', headline_txt)
    demais = re.split(r"(?<=[.!?])\s+", intro, maxsplit=1)
    sub_txt = _esc((demais[1] if len(demais) > 1 else intro)[:240])
    if sub_txt:
        t = _replace_first(t, r'(<p class="section-paraquem__subtitle"[^>]*>)(.*?)(</p>)', sub_txt)
    perfis = d.get("perfis") or []
    nao_para = d.get("nao_para_quem") or []
    positivos: list[str] = []
    for perfil in perfis[:3]:
        titulo = perfil.get("titulo", "").strip()
        if titulo:
            positivos.append(_esc(titulo))
        for b in perfil.get("bullets", []):
            if len(positivos) >= 5:
                break
            positivos.append(_esc(b))
        if len(positivos) >= 5:
            break
    while len(positivos) < 5:
        positivos.append("")
    negativos = [_esc(b) for b in nao_para[:5]]
    while len(negativos) < 5:
        negativos.append("")
    # Itens positivos: <span class="icon-yes">...</span><span>TEXT</span> dentro de .check-row
    t = _replace_sequence(
        t,
        r'(<span class="icon-yes"[^>]*>[\s\S]*?</span>\s*<span>)([^<]+)(</span>)',
        positivos,
    )
    # Itens negativos: <span class="icon-no">...</span><span style="color: var(--text-mid);">TEXT</span>
    t = _replace_sequence(
        t,
        r'(<span class="icon-no"[^>]*>[\s\S]*?</span>\s*<span style="[^"]*">)([^<]+)(</span>)',
        negativos,
    )
    return t


def _fill_entregaveis_teal_claro(t: str, d: dict[str, Any]) -> str:
    intro = d.get("intro", "")
    primeira = re.split(r"(?<=[.!?])\s+", intro, maxsplit=1)[0] if intro else ""
    headline_txt = _esc(primeira[:180] or "Tudo que voce recebe quando entrar")
    t = _replace_first(t, r'(<h2 class="section-entregaveis__headline"[^>]*>)(.*?)(</h2>)', headline_txt)
    demais = re.split(r"(?<=[.!?])\s+", intro, maxsplit=1)
    sub_txt = _esc((demais[1] if len(demais) > 1 else intro)[:240])
    if sub_txt:
        t = _replace_first(t, r'(<p class="section-entregaveis__subtitle"[^>]*>)(.*?)(</p>)', sub_txt)
    itens = d.get("itens") or []
    titulos = [_esc(it.get("titulo", "")) for it in itens[:6]]
    descs = [_esc(it.get("descricao", "")) for it in itens[:6]]
    while len(titulos) < 6:
        titulos.append("")
        descs.append("")
    t = _replace_sequence(t, r'(<h3 class="entregavel-card__title"[^>]*>)(.*?)(</h3>)', titulos)
    t = _replace_sequence(t, r'(<p class="entregavel-card__text"[^>]*>)(.*?)(</p>)', descs)
    return t


def _fill_bonus_teal_claro(t: str, d: dict[str, Any]) -> str:
    intro = d.get("intro", "")
    primeira = re.split(r"(?<=[.!?])\s+", intro, maxsplit=1)[0] if intro else ""
    headline_txt = _esc(primeira[:180] or "Bonus exclusivos para quem entrar agora")
    t = _replace_first(t, r'(<h2 class="section-bonus__headline"[^>]*>)(.*?)(</h2>)', headline_txt)
    demais = re.split(r"(?<=[.!?])\s+", intro, maxsplit=1)
    sub_txt = _esc((demais[1] if len(demais) > 1 else intro)[:240])
    if sub_txt:
        t = _replace_first(t, r'(<p class="section-bonus__subtitle"[^>]*>)(.*?)(</p>)', sub_txt)
    bonus = d.get("bonus") or []
    titulos = [_esc(b.get("titulo", "")) for b in bonus[:3]]
    descs = [_esc(b.get("descricao", "")) for b in bonus[:3]]
    valores = [_esc(b.get("valor", "")) for b in bonus[:3]]
    while len(titulos) < 3:
        titulos.append("")
        descs.append("")
        valores.append("")
    t = _replace_sequence(t, r'(<h3 class="bonus-card__title"[^>]*>)(.*?)(</h3>)', titulos)
    t = _replace_sequence(t, r'(<p class="bonus-card__text"[^>]*>)(.*?)(</p>)', descs)
    t = _replace_sequence(t, r'(<span class="bonus-card__value-amount"[^>]*>)(.*?)(</span>)', valores)
    return t


def _fill_stack_teal_claro(t: str, d: dict[str, Any]) -> str:
    linhas = d.get("linhas") or []
    nomes = [_esc(l.get("item", "")) for l in linhas[:6]]
    valores = [_esc(l.get("valor", "")) for l in linhas[:6]]
    while len(nomes) < 6:
        nomes.append("")
        valores.append("")
    t = _replace_sequence(t, r'(<span class="stack-item__name"[^>]*>)(.*?)(</span>)', nomes)
    t = _replace_sequence(t, r'(<span class="stack-item__value"[^>]*>)(.*?)(</span>)', valores)
    total = _esc(d.get("total", "") or "")
    if total:
        t = _replace_first(t, r'(<span class="stack-total__value"[^>]*>)(.*?)(</span>)', total)
    # Rodape do stack card: menciona investimento
    vista = d.get("preco_vista", "")
    parc = d.get("preco_parc", "")
    partes: list[str] = []
    if vista:
        partes.append(f"{vista} a vista")
    if parc:
        partes.append(parc)
    if partes:
        texto = "Mas voce nao vai pagar isso. Investimento hoje: " + " ou ".join(partes) + "."
        t = _replace_first(t, r'(<p class="stack-footer"[^>]*>)(.*?)(</p>)', _esc(texto))
    return t


def _fill_suporte_teal_claro(t: str, d: dict[str, Any]) -> str:
    intro = d.get("intro", "")
    primeira = re.split(r"(?<=[.!?])\s+", intro, maxsplit=1)[0] if intro else ""
    headline_txt = _esc(primeira[:180] or "Voce nao vai estar sozinho nessa")
    t = _replace_first(t, r'(<h2 class="section-suporte__headline"[^>]*>)(.*?)(</h2>)', headline_txt)
    demais = re.split(r"(?<=[.!?])\s+", intro, maxsplit=1)
    sub_txt = _esc((demais[1] if len(demais) > 1 else intro)[:240])
    if sub_txt:
        t = _replace_first(t, r'(<p class="section-suporte__subtitle"[^>]*>)(.*?)(</p>)', sub_txt)
    itens = d.get("itens") or []
    titulos = [_esc(it.get("titulo", "")) for it in itens[:4]]
    descs = [_esc(it.get("descricao", "")) for it in itens[:4]]
    while len(titulos) < 4:
        titulos.append("")
        descs.append("")
    t = _replace_sequence(t, r'(<h3 class="suporte-card__title"[^>]*>)(.*?)(</h3>)', titulos)
    t = _replace_sequence(t, r'(<p class="suporte-card__text"[^>]*>)(.*?)(</p>)', descs)
    return t


def _fill_garantia_teal_claro(t: str, d: dict[str, Any]) -> str:
    dias = str(d.get("dias", "") or "7")
    headline = _esc(d.get("headline", ""))
    corpo = _esc(d.get("corpo", ""))
    t = _replace_first(t, r'(<span class="garantia-selo__days"[^>]*>)(.*?)(</span>)', _esc(f"{dias} dias"))
    if headline:
        t = _replace_first(t, r'(<h2 class="garantia-card__headline"[^>]*>)(.*?)(</h2>)', headline)
    if corpo:
        t = _replace_first(t, r'(<p class="garantia-card__text"[^>]*>)(.*?)(</p>)', corpo)
    return t


def _fill_autoridade_teal_claro(t: str, d: dict[str, Any]) -> str:
    nome = _esc(d.get("nome", ""))
    cargo = _esc(d.get("cargo", ""))
    paragrafos = [_esc(p) for p in (d.get("paragrafos") or [])][:3]
    while len(paragrafos) < 3:
        paragrafos.append("")
    # Headline da secao autoridade
    t = _replace_first(t, r'(<h2 class="section-autoridade__headline"[^>]*>)(.*?)(</h2>)', "Quem esta por tras do metodo")
    # Subtitle: usa cargo se tiver, senao texto neutro
    subtitle_txt = _esc(f"Conheca o criador que desenhou pessoalmente cada etapa deste metodo.") if not cargo else _esc("Conheca o profissional que desenhou este caminho.")
    t = _replace_first(t, r'(<p class="section-autoridade__subtitle"[^>]*>)(.*?)(</p>)', subtitle_txt)
    if nome:
        t = _replace_first(t, r'(<h3 class="autoridade-nome"[^>]*>)(.*?)(</h3>)', nome)
    if cargo:
        t = _replace_first(t, r'(<p class="autoridade-cargo"[^>]*>)(.*?)(</p>)', cargo)
    # Credenciais (4 items): extrai frases com numeros dos paragrafos, senao placeholder
    paragrafos_brutos = d.get("paragrafos") or []
    credenciais: list[str] = []
    for p in paragrafos_brutos:
        for frase in re.split(r"(?<=[.!?])\s+", p):
            if re.search(r"\d", frase) and 15 <= len(frase) <= 120:
                credenciais.append(_esc(frase.strip(" .")))
                if len(credenciais) >= 4:
                    break
        if len(credenciais) >= 4:
            break
    while len(credenciais) < 4:
        credenciais.append("[Credencial: substitua por marco real]")
    t = _replace_sequence(t, r'(<span class="credencial-card__text"[^>]*>)(.*?)(</span>)', credenciais)
    # 3 paragrafos de bio dentro de <div class="autoridade-bio">
    def _replace_bio(match: re.Match) -> str:
        inner_open = match.group(1)
        inner_close = match.group(3)
        paragrafos_html = "\n".join(f"<p>{p}</p>" for p in paragrafos if p)
        return inner_open + "\n" + paragrafos_html + "\n" + inner_close
    t = re.sub(
        r'(<div class="autoridade-bio"[^>]*>)(.*?)(</div>)',
        _replace_bio,
        t,
        count=1,
        flags=re.DOTALL,
    )
    return t


def _fill_faq_teal_claro(t: str, d: dict[str, Any]) -> str:
    itens = d.get("itens") or []
    perguntas = [_esc(it.get("pergunta", "")) for it in itens[:6]]
    respostas = [_esc(it.get("resposta", "")) for it in itens[:6]]
    while len(perguntas) < 6:
        perguntas.append("")
        respostas.append("")
    # Perguntas: primeiro <span> dentro do <button class="faq-trigger">
    t = _replace_sequence(
        t,
        r'(<button class="faq-trigger"[^>]*>\s*<span>)([^<]+)(</span>)',
        perguntas,
    )
    # Respostas: <div class="faq-answer-inner"><p>TEXT</p></div>
    t = _replace_sequence(
        t,
        r'(<div class="faq-answer-inner"[^>]*>\s*<p[^>]*>)(.*?)(</p>)',
        respostas,
    )
    return t


def _fill_oferta_teal_claro(t: str, d: dict[str, Any]) -> str:
    intro = d.get("intro", "")
    primeira = re.split(r"(?<=[.!?])\s+", intro, maxsplit=1)[0] if intro else ""
    headline_txt = _esc(primeira[:180] or "Sua entrada para o metodo completo")
    t = _replace_first(t, r'(<h2 class="section-oferta__headline"[^>]*>)(.*?)(</h2>)', headline_txt)
    demais = re.split(r"(?<=[.!?])\s+", intro, maxsplit=1)
    sub_txt = _esc((demais[1] if len(demais) > 1 else intro)[:240])
    if sub_txt:
        t = _replace_first(t, r'(<p class="section-oferta__subtitle"[^>]*>)(.*?)(</p>)', sub_txt)
    itens = d.get("itens") or []
    nomes = [_esc(it.get("titulo", "")) for it in itens[:5]]
    valores = [_esc(it.get("valor", "")) for it in itens[:5]]
    while len(nomes) < 5:
        nomes.append("")
        valores.append("")
    t = _replace_sequence(t, r'(<span class="oferta-item__name"[^>]*>)(.*?)(</span>)', nomes)
    t = _replace_sequence(t, r'(<span class="oferta-item__value"[^>]*>)(.*?)(</span>)', valores)
    total = _esc(d.get("total", "") or "")
    if total:
        t = _replace_first(t, r'(<span class="oferta-total__value"[^>]*>)(.*?)(</span>)', total)
    parc = d.get("preco_parc", "") or ""
    vista = d.get("preco_vista", "") or ""
    # parc formato "12x de R$ 297"
    parc_match = re.match(r"\s*(\d+x\s+de)\s*(R\$?[\s\xa0]*[\d.,]+)", parc)
    if parc_match:
        parcelas_txt = _esc(parc_match.group(1).strip())
        valor_txt = _esc(parc_match.group(2).strip())
        t = _replace_first(t, r'(<p class="oferta-preco__parcelas"[^>]*>)(.*?)(</p>)', parcelas_txt)
        t = _replace_first(t, r'(<p class="oferta-preco__valor"[^>]*>)(.*?)(</p>)', valor_txt)
    elif parc:
        t = _replace_first(t, r'(<p class="oferta-preco__valor"[^>]*>)(.*?)(</p>)', _esc(parc))
    if vista:
        t = _replace_first(t, r'(<p class="oferta-preco__avista"[^>]*>)(.*?)(</p>)', _esc(f"ou {vista} a vista"))
    button = _esc(d.get("button", "") or "Quero minha vaga")
    t = re.sub(
        r'(<a href="#" class="oferta-cta"[^>]*>)(.*?)(<span class="material-symbols-outlined")',
        lambda m: m.group(1) + f"\n              {button}\n              " + m.group(3),
        t,
        count=1,
        flags=re.DOTALL,
    )
    return t


def _fill_hero_depoimentos_teal_claro(tema_root: Path, data: dict[int, dict[str, Any]]) -> None:
    """Preenche o segundo bloco de provas (hero_teal_claro_depoimentos) que é
    um arquivo separado, não mergeado a partir do primeiro bloco.
    Usa Bloco 04 (3 depoimentos) + Bloco 11 (3 depoimentos) = 6 cards (2 slides × 3).
    """
    path = tema_root / "hero_teal_claro_depoimentos" / "code.html"
    if not path.is_file():
        return
    t = _read(path)
    dep04 = (data.get(4) or {}).get("depoimentos") or []
    dep11 = (data.get(11) or {}).get("depoimentos") or []
    depos_6 = (dep04[:3] + dep11[:3])[:6]
    while len(depos_6) < 6:
        depos_6.append({})
    # Headline da secao: aproveita intro do Bloco 11 (primeira frase)
    intro11 = (data.get(11) or {}).get("intro", "") or (data.get(4) or {}).get("intro", "")
    primeira = re.split(r"(?<=[.!?])\s+", intro11, maxsplit=1)[0] if intro11 else ""
    if primeira:
        t = re.sub(
            r'(<div class="section-header[^"]*"[^>]*>\s*<h2[^>]*>)(.*?)(</h2>)',
            lambda m: m.group(1) + _esc(primeira[:160]) + m.group(3),
            t,
            count=1,
            flags=re.DOTALL,
        )
    demais = re.split(r"(?<=[.!?])\s+", intro11, maxsplit=1)
    sub_txt = (demais[1] if len(demais) > 1 else intro11)[:240]
    if sub_txt:
        t = re.sub(
            r'(<div class="section-header[^"]*"[^>]*>[\s\S]*?<p[^>]*>)(.*?)(</p>)',
            lambda m: m.group(1) + _esc(sub_txt) + m.group(3),
            t,
            count=1,
            flags=re.DOTALL,
        )
    # Monta dados dos 6 cards
    frases_titulo: list[str] = []  # 1º <p class="quote"> com style (negrito)
    corpos: list[str] = []          # 2º <p class="quote"> (corpo longo)
    iniciais: list[str] = []
    nomes_autor: list[str] = []
    cargos: list[str] = []
    for dep in depos_6:
        quote_curto = (dep.get("quote") or "").strip('"').strip()
        # Frase-titulo curta (primeiro trecho do quote, ate 80 chars)
        frase_titulo = quote_curto.split(".")[0][:80] if quote_curto else ""
        frases_titulo.append(_esc(f'"{frase_titulo}"' if frase_titulo else ""))
        # Corpo: antes + depois ou quote inteiro
        partes: list[str] = []
        if dep.get("antes"):
            partes.append(dep["antes"])
        if dep.get("depois"):
            partes.append(dep["depois"])
        corpo = " ".join(partes).strip() if partes else quote_curto
        corpos.append(_esc(corpo[:400]))
        nome = dep.get("nome", "") or ""
        nomes_autor.append(_esc(nome))
        # Iniciais: primeiras letras de ate 2 palavras
        palavras_nome = [w for w in nome.split() if w]
        ini = "".join(w[0] for w in palavras_nome[:2]).upper() if palavras_nome else ""
        iniciais.append(_esc(ini))
        cargos.append(_esc((dep.get("detalhe") or "")[:80]))
    # Substituicoes sequenciais
    # 1º <p class="quote"> com style inline → frase titulo
    t = _replace_sequence(
        t,
        r'(<p class="quote"\s+style="[^"]*">)(.*?)(</p>)',
        frases_titulo,
    )
    # 2º <p class="quote"> sem style → corpo longo
    t = _replace_sequence(
        t,
        r'(<p class="quote">)(.*?)(</p>)',
        corpos,
    )
    t = _replace_sequence(t, r'(<div class="avatar"[^>]*>)(.*?)(</div>)', iniciais)
    t = _replace_sequence(t, r'(<div class="author-name"[^>]*>)(.*?)(</div>)', nomes_autor)
    t = _replace_sequence(t, r'(<div class="author-role"[^>]*>)(.*?)(</div>)', cargos)
    _write(path, t)


# ============================================================
# POS-PROCESSAMENTO DO HTML MERGEADO
# ============================================================


def postprocess_merged(final_html_path: Path, data: dict[int, dict[str, Any]], slug: str, tema: str = "flat_claro") -> None:
    """Aplicacoes que precisam do HTML ja mergeado:
    - Preencher o segundo bloco de prova social (provas2) com dados do Bloco 11
    - Limpar residuos de sample text do template (nomes especificos do template base)
    - Atualizar title e meta description da pagina
    """
    t = _read(final_html_path)

    # 1) Prova social: a pagina final tem 6 depo-cards (bloco 04 duplicado pelo merge).
    # Aplica _replace_sequence com 6 valores (3 do Bloco 04 + 3 do Bloco 11) em toda pagina.
    # (Para teal_claro o segundo bloco ja foi preenchido antes do merge, entao pulamos)
    dep04 = (data.get(4) or {}).get("depoimentos") or []
    dep11 = (data.get(11) or {}).get("depoimentos") or []
    todos_depos = (dep04[:3] + dep11[:3])
    if todos_depos and tema != "teal_claro":
        nomes = [_esc(dep.get("nome", "")) for dep in todos_depos]
        detalhes = [_esc(dep.get("detalhe", "")[:60]) for dep in todos_depos]
        quotes: list[str] = []
        for dep in todos_depos:
            partes: list[str] = []
            if dep.get("antes"):
                partes.append("Antes: " + dep["antes"])
            if dep.get("depois"):
                partes.append("Depois: " + dep["depois"])
            if dep.get("quote"):
                partes.append('"' + dep["quote"] + '"')
            texto = " ".join(partes).strip() or dep.get("quote", "")
            quotes.append(_esc(texto))
        t = _replace_sequence(t, r'(<p class="font-semibold text-base"[^>]*>)(.*?)(</p>)', nomes)
        t = _replace_sequence(t, r'(<p class="text-xs text-gray-500"[^>]*>)(.*?)(</p>)', detalhes)
        t = _replace_sequence(
            t,
            r'(<p class="text-sm font-light text-ink leading-relaxed"[^>]*>)(.*?)(</p>)',
            quotes,
        )

    # 2) Limpa residuos de sample text conhecidos do template flat_claro
    nome_criador = (data.get(14) or {}).get("nome", "") or "o criador"
    residuos = {
        "Apresentação Planilhas Pro": "Apresentação do produto",
        "Biblioteca Planilhas Pro": "Solução completa do produto",
        "Planilhas Pro": "o programa",
        "Quero entrar na Planilhas Pro agora": (data.get(16) or {}).get("button", "") or "Quero minha vaga",
    }
    for src_t, dst_t in residuos.items():
        t = t.replace(src_t, dst_t)

    # 2b) Limpa residuos conhecidos do tema teal_claro
    if tema == "teal_claro":
        marca = " ".join(w.capitalize() for w in slug.split("-"))
        residuos_teal = {
            '<div class="logo">Atelier<span>.</span></div>': f'<div class="logo">{_esc(marca)}<span>.</span></div>',
            "SuaMarca": marca,
            # Marca placeholders claros em links ainda nao configurados
        }
        for src_t, dst_t in residuos_teal.items():
            t = t.replace(src_t, dst_t)
        # CTAs ainda com href="#" (sem destino): marca como placeholder explicito
        t = re.sub(
            r'<a href="#"(\s+class="(cta-pill|oferta-cta|faq-footer-cta)")',
            r'<a href="#COLOCAR_LINK_CHECKOUT"\1',
            t,
        )
        # Video placeholder (rickroll): substitui por aviso claro sem quebrar iframe
        t = t.replace(
            "https://www.youtube.com/embed/dQw4w9WgXcQ?rel=0",
            "about:blank",
        )

    # 3) Atualiza title e meta description
    hero = data.get(1) or {}
    page_title = hero.get("headline", "")[:120] or "Pagina de vendas"
    page_desc = hero.get("subheadline", "")[:160]
    t = re.sub(r'<title>.*?</title>', f'<title>{_esc(page_title)}</title>', t, count=1, flags=re.DOTALL)
    if page_desc:
        t = re.sub(
            r'<meta\s+name="description"\s+content="[^"]*"',
            f'<meta name="description" content="{_esc(page_desc)}"',
            t,
            count=1,
        )

    # 4) Iframe title (pode ter ficado do template original)
    t = re.sub(
        r'<iframe([^>]*)\stitle="[^"]*"',
        r'<iframe\1 title="Apresentacao do produto"',
        t,
    )

    _write(final_html_path, t)


FILLERS = [
    (1, fill_hero),
    (2, fill_dor),
    (3, fill_paliativo),
    (4, fill_provas),
    (5, fill_cta),
    (6, fill_metodo),
    (7, fill_para_quem),
    (8, fill_entregaveis),
    (9, fill_bonus),
    (10, fill_stack),
    (12, fill_suporte),
    (13, fill_garantia),
    (14, fill_autoridade),
    (15, fill_faq),
    (16, fill_oferta),
]


# ============================================================
# MAIN
# ============================================================


def main() -> None:
    p = argparse.ArgumentParser(description="Build unificado de pagina de vendas VTSD")
    p.add_argument("--slug", required=True, help="Slug do produto")
    p.add_argument("--tema", required=True, choices=THEMES, help="Tema visual")
    p.add_argument("--dry-run", action="store_true", help="So valida parse da copy")
    p.add_argument("--force", action="store_true", help="Recopia templates mesmo se ja existirem")
    args = p.parse_args()

    slug = args.slug
    tema = args.tema

    copy_path = ROOT / "meus-produtos" / slug / "entregas" / "copy-pagina" / f"copy-{slug}.md"
    if not copy_path.is_file():
        print(f"Copy nao encontrada em: {copy_path}", file=sys.stderr)
        print("Gere com /copy-pagina primeiro ou confira o slug.", file=sys.stderr)
        sys.exit(2)

    print(f"Lendo copy: {copy_path.relative_to(ROOT)}")
    data = parse_copy(copy_path)
    encontrados = [n for n, d in data.items() if d]
    print(f"Blocos parseados: {len(encontrados)}/16 ({encontrados})")

    erros = validate(data)
    if erros:
        print("\nAvisos de parse:")
        for e in erros:
            print("  -", e)
    else:
        print("Parse OK sem avisos.")

    if args.dry_run:
        print("\n[dry-run] Saindo sem gravar.")
        return

    print(f"\nCopiando templates do tema {tema}...")
    tema_root = copy_tema(tema, slug, args.force)
    print(f"Templates em: {tema_root.relative_to(ROOT)}")

    print("\nSubstituindo placeholders nos 16 blocos...")
    for num, fn in FILLERS:
        bloco_data = data.get(num) or {}
        if not bloco_data:
            print(f"  bloco {num:02d}: copy vazia, pulando")
            continue
        # Injeta slug no dict do bloco 6 (metodo) para permitir uso da furadeira
        if num == 6:
            bloco_data = dict(bloco_data)
            bloco_data["__slug__"] = slug
        try:
            fn(tema_root, tema, bloco_data)
            print(f"  bloco {num:02d}: ok")
        except Exception as exc:  # noqa: BLE001
            print(f"  bloco {num:02d}: falhou ({exc})")

    # Bloco extra do teal_claro: hero_teal_claro_depoimentos (segundo bloco de provas)
    if tema == "teal_claro":
        try:
            _fill_hero_depoimentos_teal_claro(tema_root, data)
            print("  hero_depoimentos: ok")
        except Exception as exc:  # noqa: BLE001
            print(f"  hero_depoimentos: falhou ({exc})")

    print("\nRodando merge do tema...")
    merge_script = tema_root / f"pagina_completa_{tema}" / "build_merge.py"
    if not merge_script.is_file():
        print(f"build_merge.py nao encontrado em {merge_script}", file=sys.stderr)
        sys.exit(3)
    subprocess.run([sys.executable, str(merge_script)], cwd=str(merge_script.parent), check=True)

    src = merge_script.parent / "code.html"
    dest = ROOT / "meus-produtos" / slug / "entregas" / "paginas" / f"vendas-{slug}.html"
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(src, dest)

    print("\nPos-processando HTML final (provas2, title, residuos)...")
    try:
        postprocess_merged(dest, data, slug, tema)
    except Exception as exc:  # noqa: BLE001
        print(f"Aviso: pos-processamento falhou ({exc})")

    print(f"\nGerado: {dest.relative_to(ROOT)} ({dest.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
