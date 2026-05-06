"""
Build Painel de Entregas
========================
Le perfil.md, idconsumidor.md, pesquisa-mercado.md e tipo.md do produto ativo
e gera painel-entregas.html usando o template em scripts/templates/.

Uso:
  py -3 scripts/build-painel-entregas.py
  py -3 scripts/build-painel-entregas.py --slug meu-produto
"""

import os, re, sys, argparse, json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = ROOT / "scripts" / "templates" / "painel-entregas.html"
PRODUTOS = ROOT / "meus-produtos"

# reutiliza parser e render da secao copy-pagina (painel_template.py)
SCRIPT_DIR = Path(__file__).resolve().parent
if str(SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPT_DIR))
import painel_template as _tmpl  # noqa: E402

# ── helpers ──────────────────────────────────────────────────────────

def read_file(path):
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8")

def get_slug():
    parser = argparse.ArgumentParser()
    parser.add_argument("--slug", default=None)
    args = parser.parse_args()
    if args.slug:
        return args.slug
    ativo = PRODUTOS / ".ativo"
    if ativo.exists():
        return ativo.read_text(encoding="utf-8").strip()
    print("Erro: nenhum produto ativo. Use --slug ou crie meus-produtos/.ativo")
    sys.exit(1)

def esc(text):
    """Escape HTML entities."""
    return (text
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;"))

# ── parsers ──────────────────────────────────────────────────────────

def parse_section(text, header, level=2):
    """Extrai conteudo entre ## Header e proximo ## (ou fim)."""
    prefix = "#" * level
    pattern = rf'^{prefix}\s+{re.escape(header)}.*?\n(.*?)(?=^{prefix}\s|\Z)'
    m = re.search(pattern, text, re.MULTILINE | re.DOTALL)
    return m.group(1).strip() if m else ""

def parse_section_fuzzy(text, *keywords, level=2):
    """Busca secao que contenha qualquer das keywords no header."""
    prefix = "#" * level
    for kw in keywords:
        pattern = rf'^{prefix}\s+.*?{re.escape(kw)}.*?\n(.*?)(?=^{prefix}\s|\Z)'
        m = re.search(pattern, text, re.MULTILINE | re.DOTALL | re.IGNORECASE)
        if m:
            return m.group(1).strip()
    return ""

def parse_youtube_rich(sec_yt):
    """Parse formato ### Vídeo X em lista de dicts ricos (comentarios, thumbnail, lacuna)."""
    videos = []
    blocks = re.split(r'\n###\s+V[íi]deo\s+\d+', "\n" + sec_yt, flags=re.IGNORECASE)
    for block in blocks:
        if not block.strip():
            continue
        v = {}
        m = re.search(r'\*\*T[ií]tulo:\*\*\s*(.+)', block)
        v["titulo"] = m.group(1).strip() if m else ""
        m = re.search(r'\*\*Canal:\*\*\s*(.+)', block)
        v["canal"] = m.group(1).strip() if m else ""
        m = re.search(r'\*\*Link:\*\*\s*(https?://\S+)', block)
        v["link"] = m.group(1).strip().rstrip(").,") if m else ""
        m = re.search(r'\*\*Visualiza[çc][oõ]es:\*\*\s*(.+)', block, re.IGNORECASE)
        v["views"] = m.group(1).strip() if m else ""
        m = re.search(r'\*\*Data de publica[çc][aã]o:\*\*\s*(.+)', block, re.IGNORECASE)
        v["data"] = m.group(1).strip() if m else ""
        m = re.search(r'\*\*[Âa]ngulo.*?:\*\*\s*(.+)', block)
        v["angulo"] = m.group(1).strip() if m else ""
        m = re.search(r'\*\*Lacuna.*?:\*\*\s*(.+)', block)
        v["lacuna"] = m.group(1).strip() if m else ""
        v["comentarios"] = [c.strip() for c in re.findall(r'"([^"]{10,200})"', block)][:5]
        thumb = {}
        for field, pat in [
            ("cores", r'- \*?Cores[:\*]*\s*(.+)'),
            ("expressao", r'- \*?Express[aã]o[:\*]*\s*(.+)'),
            ("texto", r'- \*?Texto em destaque[:\*]*\s*(.+)'),
            ("elementos", r'- \*?Elementos visuais[:\*]*\s*(.+)'),
            ("composicao", r'- \*?Composi[çc][aã]o[:\*]*\s*(.+)'),
        ]:
            m2 = re.search(pat, block, re.IGNORECASE)
            if m2:
                thumb[field] = m2.group(1).strip()
        v["thumbnail"] = thumb
        if v["titulo"] or v["canal"]:
            videos.append(v)
    return videos

def parse_bullet_items(text):
    """Extrai itens de lista markdown (- ou 1. ou *)."""
    items = []
    for line in text.splitlines():
        line = line.strip()
        m = re.match(r'^[-*]\s+(.+)', line) or re.match(r'^\d+\.\s+(.+)', line)
        if m:
            items.append(m.group(1).strip())
    return items

def parse_field(text, field_name):
    """Extrai valor de campo como **Campo:** valor ou - **Campo:** valor."""
    pattern = rf'\*\*{re.escape(field_name)}:\*\*\s*(.+)'
    m = re.search(pattern, text, re.IGNORECASE)
    return m.group(1).strip() if m else ""

def parse_subsections(text, level=3):
    """Retorna dict {header: content} para subsecoes ### dentro de um bloco."""
    prefix = "#" * level
    parts = re.split(rf'^{prefix}\s+', text, flags=re.MULTILINE)
    result = {}
    for part in parts[1:]:
        lines = part.split("\n", 1)
        header = lines[0].strip()
        body = lines[1].strip() if len(lines) > 1 else ""
        result[header] = body
    return result

# ── perfil.md parser ─────────────────────────────────────────────────

def parse_perfil(text):
    d = {}
    # titulo
    m = re.match(r'^#\s+.*?[—–\-:]\s*(.+)', text)
    d["nome_produto"] = m.group(1).strip() if m else "Produto"

    # quadro
    sec = parse_section_fuzzy(text, "Quadro")
    d["quadro"] = sec.split("\n")[0].strip() if sec else ""

    # furadeira
    sec = parse_section_fuzzy(text, "Furadeira")
    nm = parse_field(sec, "Nome do Método")
    d["nome_metodo"] = nm if nm else sec.split("\n")[0].strip()

    # parse macroetapas from furadeira - look for ### subsections, then numbered bold items
    d["macroetapas"] = []
    subsecs = parse_subsections(sec, level=3)
    if subsecs:
        for i, (title, body) in enumerate(subsecs.items(), 1):
            d["macroetapas"].append({"num": i, "titulo": title, "desc": body.replace("\n", " ").strip()})
    if not d["macroetapas"]:
        # try numbered bold items: "1. **Titulo.** descricao" or "1. **Titulo:** descricao"
        numbered_re = re.compile(r'^\d+\.\s+\*\*(.+?)[.*:]*\*\*\s*(.*)', re.MULTILINE)
        matches = numbered_re.findall(sec)
        for i, (title, desc) in enumerate(matches, 1):
            d["macroetapas"].append({"num": i, "titulo": title.rstrip(".:"), "desc": desc.strip()})
    if not d["macroetapas"]:
        # last fallback: single block with method name
        lines = sec.split("\n")
        desc_lines = [l for l in lines if not l.startswith("**Nome")]
        if desc_lines:
            desc = " ".join(l.strip() for l in desc_lines if l.strip())
            d["macroetapas"].append({"num": 1, "titulo": d["nome_metodo"], "desc": desc})

    # identidade do produto
    sec_prod = parse_section_fuzzy(text, "Identidade do Produto")
    d["formato_produto"] = parse_field(sec_prod, "Formato")
    d["tipo_raw"] = parse_field(sec_prod, "Tipo")
    d["preco"] = parse_field(sec_prod, "Preço") or parse_field(sec_prod, "Preco")
    d["diferencial_raw"] = parse_field(sec_prod, "Diferencial")
    d["nome_produto_field"] = parse_field(sec_prod, "Nome") or d["nome_produto"]

    # identidade do consumidor (resumo no perfil)
    sec_cons = parse_section_fuzzy(text, "Identidade do Consumidor")
    d["nicho"] = parse_field(sec_cons, "Nicho")
    d["nicho_subtitulo"] = parse_field(sec_cons, "Público-alvo") or ""

    # identidade do comunicador
    sec_com = parse_section_fuzzy(text, "Identidade do Comunicador")
    d["comunicador_nome"] = parse_field(sec_com, "Nome")
    d["comunicador_especialidade"] = parse_field(sec_com, "Especialidade")
    d["valores"] = [v.strip() for v in parse_field(sec_com, "Valores").split(",") if v.strip()]
    d["tom_de_voz"] = parse_field(sec_com, "Tom de voz")
    d["posicionamento"] = parse_field(sec_com, "Posicionamento pessoal")
    d["tonalidade_emocional"] = parse_field(sec_com, "Tonalidade emocional predominante")
    mantras_raw = parse_field(sec_com, "Mantras/Jargões próprios")
    d["mantras"] = [m.strip().strip('"').strip("'") for m in mantras_raw.split(",") if m.strip() and m.strip().lower() != "nenhum ainda"] if mantras_raw.lower() != "nenhum ainda" else []
    d["formatos"] = [f.strip() for f in parse_field(sec_com, "Formatos que combinam mais").split(",") if f.strip()]
    d["estilo_visual"] = [e.strip() for e in parse_field(sec_com, "Elementos visuais recomendados").split(",") if e.strip()]
    refs_raw = parse_field(sec_com, "Referências comunicacionais")
    d["referencias"] = []
    if refs_raw:
        for ref in re.split(r'[;,](?=[A-Z])', refs_raw):
            parts = ref.strip().split("(", 1)
            name = parts[0].strip()
            desc = parts[1].rstrip(")").strip() if len(parts) > 1 else ""
            if name:
                d["referencias"].append({"nome": name, "desc": desc})

    # decorados
    sec_dec = parse_section_fuzzy(text, "Decorados")
    dec_subs = parse_subsections(sec_dec, level=3)
    d["decorados"] = {}
    cat_map = {
        "Financeiro": ("badge-green", "10 benefícios financeiros"),
        "Tempo": ("badge-blue", "10 benefícios de tempo"),
        "Autoestima": ("badge-purple", "10 benefícios de autoestima"),
        "Reputação": ("badge-orange", "10 benefícios de reputação"),
        "Crescimento": ("badge-dark", "10 benefícios de crescimento"),
    }
    for cat_name, (badge, label) in cat_map.items():
        items = []
        for header, body in dec_subs.items():
            if cat_name.lower() in header.lower():
                items = parse_bullet_items(body)
                break
        d["decorados"][cat_name] = {"badge": badge, "label": label, "items": items}

    # urgencias ocultas
    sec_urg = parse_section_fuzzy(text, "Urgências Ocultas", "Urgencias Ocultas")
    urg_subs = parse_subsections(sec_urg, level=3)
    urg_map = {
        "Dores": ("badge-pink", "Dores", "O que incomoda"),
        "Dúvidas": ("badge-indigo", "Dúvidas", "O que pergunta"),
        "Desejos": ("badge-violet", "Desejos", "O que sonha"),
        "Assuntos Relacionados": ("badge-green", "Assuntos Relacionados", "Porta de entrada"),
        "Urgências Quentes": ("badge-orange", "Urgências Quentes", "Alta intenção"),
        "Urgências Frias": ("badge-neutral", "Urgências Frias", "Alto volume"),
        "Urgências Inusitadas": ("badge-purple", "Urgências Inusitadas", "Ângulos inesperados"),
    }
    d["urgencias"] = {}
    for key, (badge, nome, desc) in urg_map.items():
        items = []
        for header, body in urg_subs.items():
            if any(w.lower() in header.lower() for w in key.split()):
                items = parse_bullet_items(body)
                break
        d["urgencias"][key] = {"badge": badge, "nome": nome, "desc": desc, "items": items}

    # argumentos incontestaveis
    sec_arg = parse_section_fuzzy(text, "Argumentos Incontestáveis", "Argumentos Incontestaveis")
    d["argumentos"] = parse_bullet_items(sec_arg)

    return d

# ── idconsumidor.md parser ───────────────────────────────────────────

def parse_idconsumidor(text):
    d = {}
    # para quem e
    sec = parse_section_fuzzy(text, "Para Quem")
    d["para_quem_e"] = sec.split("\n\n")[0].strip() if sec else ""

    # identidade do consumidor (demografico)
    sec_id = parse_section_fuzzy(text, "Identidade do Consumidor")
    d["genero"] = parse_field(sec_id, "Gênero") or parse_field(sec_id, "Genero")
    d["idade"] = parse_field(sec_id, "Idade")
    d["profissao"] = parse_field(sec_id, "Profissão") or parse_field(sec_id, "Profissao")
    d["renda"] = parse_field(sec_id, "Renda")
    d["localizacao"] = parse_field(sec_id, "Localização") or parse_field(sec_id, "Localizacao")
    d["nivel_consciencia"] = parse_field(sec_id, "Nível de consciência") or parse_field(sec_id, "Nivel de consciencia")
    d["onde_busca"] = parse_field(sec_id, "Onde busca informação") or parse_field(sec_id, "Onde busca informacao")

    # como se comunicar
    sec_com = parse_section_fuzzy(text, "Como se Comunicar")
    d["palavras_conectam"] = [w.strip() for w in parse_field(sec_com, "Palavras que conectam").split(",") if w.strip()]
    d["palavras_afastam"] = [w.strip() for w in parse_field(sec_com, "Palavras que afastam").split(",") if w.strip()]

    # objecoes
    d["objecoes"] = []
    sec_obj = parse_section_fuzzy(text, "Objeções de Compra", "Objecoes de Compra")
    obj_subs = parse_subsections(sec_obj, level=3)
    for header, body in obj_subs.items():
        m = re.match(r'Objeção\s+\d+:\s*"?(.+?)"?\s*$', header)
        texto_objecao = m.group(1).strip().strip('"') if m else header
        argumentos = []
        arg_blocks = re.split(r'\*\*(\d+\.\s+Argumento[^*]+)\*\*', body)
        for i in range(1, len(arg_blocks), 2):
            titulo = arg_blocks[i].strip()
            conteudo = arg_blocks[i+1].strip() if i+1 < len(arg_blocks) else ""
            paragrafos = [p.strip() for p in conteudo.split("\n\n") if p.strip() and not p.strip().startswith("---")]
            argumentos.append({"titulo": titulo, "paragrafos": paragrafos})
        d["objecoes"].append({"texto": texto_objecao, "argumentos": argumentos})

    # baldes
    d["baldes"] = []
    sec_baldes = parse_section_fuzzy(text, "Baldes de Para Quem")
    if sec_baldes:
        balde_blocks = re.split(r'➤\s*Pra quem é\s*[-:]\s*', sec_baldes)
        for block in balde_blocks[1:]:
            lines = block.strip().split("\n")
            nome = lines[0].strip()
            items = []
            for line in lines[1:]:
                m = re.match(r'^\d+\.\s+(.+)', line.strip())
                if m:
                    items.append(m.group(1).strip())
            d["baldes"].append({"nome": nome, "items": items})

    # paliativos
    sec_pal = parse_section_fuzzy(text, "Paliativos")
    d["paliativos"] = parse_bullet_items(sec_pal) if sec_pal else []

    return d

# ── pesquisa-mercado.md parser (completo) ────────────────────────────

def extract_numbers(text):
    """Extrai numeros de um texto (R$2,1 bi, 18%, 10, etc.)."""
    nums = re.findall(r'R\$\s*[\d.,]+\s*(?:bi|mi|mil)?|[\d.,]+%|\d+', text)
    return nums

def extract_kpis_from_text(text):
    """Nao tenta extrair KPIs de texto livre. Retorna vazio. KPIs devem vir de secao estruturada."""
    return {}

def parse_pesquisa(text):
    d = {}
    d["tem_pesquisa"] = bool(text.strip())
    if not d["tem_pesquisa"]:
        return d

    # KPIs (secao dedicada ou extraidos do texto)
    sec_kpi = parse_section_fuzzy(text, "KPIs", "Indicadores")
    if sec_kpi:
        d["kpis"] = {}
        for line in sec_kpi.splitlines():
            m = re.match(r'[-*]\s*(.+?):\s*(.+)', line.strip())
            if m:
                key = m.group(1).strip().lower().replace(" ", "_")
                val = m.group(2).strip()
                trend_m = re.search(r'\((.+)\)', val)
                trend = trend_m.group(1) if trend_m else ""
                valor = re.sub(r'\(.+\)', '', val).strip()
                d["kpis"][key] = {"valor": valor, "trend": trend}
    else:
        d["kpis"] = {}
        sec_tam = parse_section_fuzzy(text, "Tamanho", "Saúde do Mercado", "Tamanho e Saúde")
        if sec_tam:
            m = re.search(r'R\$\s*([\d,\.]+\s*(?:bilh[oõ]es?|milh[oõ]es?|bi|mi)\b)', sec_tam, re.IGNORECASE)
            if m:
                d["kpis"]["tamanho_mercado"] = {"valor": f"R$ {m.group(1).strip()}", "trend": ""}
            m = re.search(r'crescimento[^.]{0,60}?([\d,\.]+%)', sec_tam, re.IGNORECASE)
            if m:
                d["kpis"]["crescimento_anual"] = {"valor": m.group(1), "trend": "crescimento"}
        sec_preco = parse_section_fuzzy(text, "Faixa de Preço", "Faixa de Preco", "Preços")
        if sec_preco:
            m = re.search(r'[Ff]aixa mais comum[^:]*:\s*(R\$\s*[\d.,]+(?:\s*a\s*R\$\s*[\d.,]+)?)', sec_preco)
            if m:
                d["kpis"]["ticket_medio"] = {"valor": m.group(1).strip(), "trend": "faixa mais comum"}

    # oportunidades
    sec_op = parse_section_fuzzy(text, "Oportunidades")
    d["oportunidades"] = parse_bullet_items(sec_op)

    # concorrentes — detecta colunas pelo cabeçalho da tabela
    d["concorrentes"] = []
    sec_conc = parse_section_fuzzy(text, "Principais Concorrentes", "Concorrentes")
    if sec_conc:
        conc_lines = [ln.strip() for ln in sec_conc.splitlines() if ln.strip().startswith("|")]
        if len(conc_lines) >= 2:
            hdr = [h.strip().lower() for h in conc_lines[0].strip("|").split("|")]
            def _col(*names):
                for n in names:
                    for i, h in enumerate(hdr):
                        if n in h:
                            return i
                return None
            idx_nome = _col("nome", "concorrente", "marca", "produto", "plataforma")
            idx_preco = _col("preço", "preco", "valor")
            idx_obs = _col("diferencial", "entregáveis", "entregaveis", "observ")
            idx_canal = _col("instagram", "insta")
            idx_link = _col("link da oferta", "pagina", "página", "site", "link")
            idx_prom = _col("promessa")
            if idx_nome is not None:
                for ln in conc_lines[2:]:
                    cells = [c.strip() for c in ln.strip("|").split("|")]
                    def _cell(idx, _cells=cells):
                        if idx is None or idx >= len(_cells):
                            return ""
                        return re.sub(r'\*+', '', _cells[idx]).strip()
                    nome = _cell(idx_nome)
                    if not nome or re.match(r'^[-:\s]+$', nome):
                        continue
                    d["concorrentes"].append({
                        "nome": nome,
                        "canal": _cell(idx_canal) or _cell(idx_link),
                        "preco": _cell(idx_preco),
                        "obs": _cell(idx_obs) or _cell(idx_prom),
                    })

    # reclamacoes (testar keywords mais especificas primeiro)
    sec_recl = parse_section_fuzzy(text, "Reclame Aqui", "Reclamações Reais", "Reclamações dos Alunos", "Reclamações", "Reclamacoes", "Objeções Reais")
    recl = parse_bullet_items(sec_recl)
    # fallback: extrair coluna "Objeção" de tabela markdown (formato da skill pesquisa-mercado)
    if not recl and sec_recl:
        for row in re.findall(r'^\|\s*\d+\s*\|\s*([^|]+)', sec_recl, re.MULTILINE):
            val = row.strip().strip('"')
            if val and not val.startswith('-'):
                recl.append(val)
    d["reclamacoes"] = recl

    # riscos
    sec_risk = parse_section_fuzzy(text, "Riscos", "Cuidados")
    d["riscos"] = parse_bullet_items(sec_risk)

    # termos em alta (keywords especificas, nao "Buscas" que casa com texto narrativo)
    sec_termos = parse_section_fuzzy(text, "Termos em Alta", "Trending", "Termos de Busca")
    d["termos_alta"] = parse_bullet_items(sec_termos) if sec_termos else []

    # padroes de anuncio
    sec_ads = parse_section_fuzzy(text, "Padrões de Anúncio", "Padroes de Anuncio", "Anúncios que Performam", "Ângulos de Anúncios", "Angulos de Anuncios")
    d["padroes_anuncio"] = parse_bullet_items(sec_ads) if sec_ads else []

    # youtube top 10 — tenta formato rico ### Vídeo X primeiro, tabela como fallback
    d["youtube"] = []
    sec_yt = parse_section_fuzzy(text, "Top 10 Vídeos", "Top 10 Videos", "YouTube Top 10", "Top 10 YouTube")
    if sec_yt:
        rich = parse_youtube_rich(sec_yt)
        if rich:
            d["youtube"] = rich
        else:
            yt_rows = re.findall(r'\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|\s*([^|]+)\s*\|', sec_yt)
            for row in yt_rows:
                titulo = row[0].strip()
                if titulo.startswith("---") or titulo.lower() in ("titulo", "título", "ranking", "#"):
                    continue
                d["youtube"].append({
                    "titulo": titulo, "canal": row[1].strip(),
                    "views": row[2].strip(), "link": row[3].strip(),
                    "thumb_texto": row[4].strip() if len(row) > 4 else "",
                    "comentarios": [], "thumbnail": {}, "angulo": "", "lacuna": "",
                })
        # fallback: bullets "Padrão X: titulo" ou lista simples
        if not d["youtube"]:
            for item in parse_bullet_items(sec_yt):
                titulo = re.sub(r'^Padr[aã]o\s*\d+[:\s]+', '', item, flags=re.IGNORECASE).strip()
                titulo = re.sub(r'\s*\([^)]+\)\s*$', '', titulo).strip().strip('"')
                if titulo:
                    d["youtube"].append({"titulo": titulo, "canal": "", "views": "", "link": "", "thumb_texto": "", "comentarios": [], "thumbnail": {}, "angulo": "", "lacuna": ""})

    # alertas regulatorios
    sec_alert = parse_section_fuzzy(text, "Alertas Regulatórios", "Alertas Regulatorios", "Alertas")
    d["alertas"] = parse_bullet_items(sec_alert) if sec_alert else []

    # fontes
    sec_fontes = parse_section_fuzzy(text, "Fontes", "Fontes Consultadas")
    d["fontes"] = parse_bullet_items(sec_fontes) if sec_fontes else []

    # Público-Alvo Real
    sec_pa = parse_section_fuzzy(text, "4. Público-Alvo Real", "4. Publico-Alvo Real", "Público-Alvo Real", "Publico-Alvo Real")
    publico_alvo: dict = {}
    if sec_pa:
        demo = parse_bullet_items(parse_section_fuzzy(sec_pa, "Demografic", "Perfil", level=3))
        comport = parse_bullet_items(parse_section_fuzzy(sec_pa, "Comportamento", level=3))
        consci = parse_bullet_items(parse_section_fuzzy(sec_pa, "Consciência", "Nivel de Consciencia", "Schwartz", level=3))
        publico_alvo = {"demo": demo, "comportamento": comport, "consciencia": consci}
        if not any(publico_alvo.values()):
            publico_alvo = {"raw": parse_bullet_items(sec_pa)}
    d["publico_alvo"] = publico_alvo

    # Assuntos Quentes e Ângulos Virais (seção 6)
    sec_assuntos = parse_section_fuzzy(text, "Assuntos Quentes", "Ângulos Virais", "Angulos Virais")
    assuntos_quentes: dict = {}
    if sec_assuntos:
        termos_sub = parse_section_fuzzy(sec_assuntos, "Termos em Alta", "Termos em alta", level=3)
        virais_sub = parse_section_fuzzy(sec_assuntos, "Conteúdos virais", "Conteudos virais", level=3)
        ganchos_sub = parse_section_fuzzy(sec_assuntos, "Ganchos", level=3)
        assuntos_quentes = {
            "termos": parse_bullet_items(termos_sub) if termos_sub else [],
            "virais": parse_bullet_items(virais_sub) if virais_sub else [],
            "ganchos": parse_bullet_items(ganchos_sub) if ganchos_sub else [],
        }
    d["assuntos_quentes"] = assuntos_quentes

    # Biblioteca de Anúncios (seção 8)
    sec_bibl = parse_section_fuzzy(text, "Biblioteca de Anúncios", "Biblioteca de Anuncios")
    biblioteca_anuncios: dict = {}
    if sec_bibl:
        headlines_sub = parse_section_fuzzy(sec_bibl, "Padrões de headline", "Padroes de headline", level=3)
        oferta_sub = parse_section_fuzzy(sec_bibl, "Padrões de oferta", "Padroes de oferta", level=3)
        criativos_sub = parse_section_fuzzy(sec_bibl, "Criativos ativos", level=3)
        obs_sub = parse_section_fuzzy(sec_bibl, "Observações", "Observacoes", level=3)
        biblioteca_anuncios = {
            "headlines": parse_bullet_items(headlines_sub) if headlines_sub else [],
            "padroes_oferta": parse_bullet_items(oferta_sub) if oferta_sub else [],
            "criativos": parse_bullet_items(criativos_sub) if criativos_sub else [],
            "observacoes": parse_bullet_items(obs_sub) if obs_sub else [],
        }
    d["biblioteca_anuncios"] = biblioteca_anuncios

    return d

# ── HTML builders ────────────────────────────────────────────────────

def build_macroetapas_html(macroetapas):
    html = ""
    for m in macroetapas:
        html += f'''<li class="timeline-item">
          <div class="tl-num">{m["num"]}</div>
          <div class="tl-body">
            <div class="tl-title">{esc(m["titulo"])}</div>
            <div class="tl-desc">{esc(m["desc"])}</div>
          </div>
        </li>\n'''
    return html

def build_accordion(badge_class, nome, label, items, is_first=False):
    open_class = " open" if is_first else ""
    items_html = "".join(f"<li>{esc(item)}</li>\n" for item in items)
    return f'''<div class="accordion{open_class}">
      <div class="accordion-header" onclick="toggleAccordion(this)">
        <span class="badge {badge_class}">{esc(nome)}</span>
        <span class="accordion-label">{esc(label)}</span>
        <span class="accordion-arrow">&#9662;</span>
      </div>
      <div class="accordion-body">
        <ul class="accordion-list">{items_html}</ul>
      </div>
    </div>\n'''

def build_decorados_html(decorados):
    html = ""
    first = True
    for cat_name, data in decorados.items():
        html += build_accordion(data["badge"], cat_name, data["label"], data["items"], is_first=first)
        first = False
    return html

def build_urgencias_html(urgencias):
    html = ""
    first = True
    for key, data in urgencias.items():
        label = f'{data["desc"]}  \u00b7  {len(data["items"])} itens'
        html += build_accordion(data["badge"], data["nome"], label, data["items"], is_first=first)
        first = False
    return html

def build_objecoes_html(objecoes):
    html = ""
    ARG_NAMES = [
        "1. Argumento incontestável",
        "2. Argumento lógico (causa e efeito)",
        "3. Argumento por analogia",
        "4. Argumento por exemplificação",
        "5. Argumento de valor",
        "6. Argumento de consequência",
        "7. Argumento de contradição",
    ]
    for i, obj in enumerate(objecoes, 1):
        args_html = ""
        for j, arg in enumerate(obj["argumentos"]):
            titulo = arg["titulo"]
            if not titulo and j < len(ARG_NAMES):
                titulo = ARG_NAMES[j]
            paras = "\n".join(f'<p style="margin-bottom:6px">{esc(p)}</p>' for p in arg["paragrafos"])
            args_html += f'''<div class="arg-block">
              <div class="arg-title">{esc(titulo)}</div>
              <div class="arg-text">{paras}</div>
            </div>\n'''

        mb = "" if i == len(objecoes) else ""
        html += f'''<div class="accordion"{' style="margin-bottom:0"' if i == len(objecoes) else ""}>
        <div class="accordion-header" onclick="toggleAccordion(this)">
          <span class="badge badge-pink">Objeção {i}</span>
          <span class="accordion-label">"{esc(obj["texto"])}"</span>
          <span class="accordion-arrow">&#9662;</span>
        </div>
        <div class="accordion-body">
          <div style="padding:0 20px 16px;display:grid;gap:12px">
            {args_html}
          </div>
        </div>
      </div>\n'''
    return html

def build_baldes_html(baldes):
    html = ""
    for i, balde in enumerate(baldes):
        items_html = "".join(f"<li>{esc(item)}</li>\n" for item in balde["items"])
        open_class = " open" if i == 0 else ""
        html += f'''<div class="accordion{open_class}" style="margin-top:{12 if i==0 else 0}px;box-shadow:none;border-color:var(--border-2)">
        <div class="accordion-header" onclick="toggleAccordion(this)">
          <span class="badge badge-neutral">{esc(balde["nome"])}</span>
          <span class="accordion-arrow" style="margin-left:auto">&#9662;</span>
        </div>
        <div class="accordion-body">
          <ul class="accordion-list">{items_html}</ul>
        </div>
      </div>\n'''
    return html

def build_pills(items, badge_class="badge-green"):
    return "".join(f'<span class="badge {badge_class}">{esc(item)}</span>\n' for item in items)

def _md_bold(text):
    """Converte **texto** para <strong>texto</strong> (após esc())."""
    return re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)

def build_bullet_list(items, style=""):
    style_attr = f' style="{style}"' if style else ""
    return "".join(f'<li{style_attr}>{_md_bold(esc(item))}</li>\n' for item in items)

def build_mantras_html(mantras):
    if not mantras:
        return '<div style="font-size:14px;color:var(--text-3);font-style:italic;padding:6px 14px">Nenhum ainda</div>'
    return "".join(
        f'<div style="font-size:14px;color:var(--text-2);font-style:italic;border-left:3px solid var(--primary);padding:6px 14px;background:var(--highlight-bg);border-radius:var(--r2)">&ldquo;{esc(m)}&rdquo;</div>\n'
        for m in mantras
    )

def build_referencias_html(refs):
    return "".join(
        f'<li><strong>{esc(r["nome"])}</strong>. {esc(r["desc"])}</li>\n' for r in refs
    )

def build_badges_completude(produto_path):
    badges = []
    if (produto_path / "perfil.md").exists():
        badges.append('<span class="badge badge-green">Perfil completo</span>')
    if (produto_path / "idconsumidor.md").exists():
        badges.append('<span class="badge badge-green">Identidade do consumidor</span>')
    perfil = read_file(produto_path / "perfil.md")
    if "Urgências Ocultas" in perfil or "Urgencias Ocultas" in perfil:
        badges.append('<span class="badge badge-green">Urgências ocultas</span>')
    return "\n".join(badges)

def build_demografico_html(idc):
    fields = [
        ("Gênero", idc.get("genero", "")),
        ("Idade", idc.get("idade", "")),
        ("Profissão", idc.get("profissao", "")),
        ("Renda", idc.get("renda", "")),
        ("Localização", idc.get("localizacao", "")),
        ("Nível de consciência", idc.get("nivel_consciencia", "")),
    ]
    return "<br>\n".join(f"<strong>{k}:</strong> {esc(v)}" for k, v in fields if v)

def build_comportamento_html(idc):
    fields = [
        ("Onde busca info", idc.get("onde_busca", "")),
        ("Sonho", ""),  # placeholder
    ]
    return "<br>\n".join(f"<strong>{k}:</strong> {esc(v)}" for k, v in fields if v)

# ── pesquisa de mercado HTML (completo) ──────────────────────────────

EMPTY_PESQUISA = {
    "kpis_html": '<div class="card" style="grid-column:1/-1"><div class="card-label">Pesquisa de mercado</div><div class="card-sub">Nenhuma pesquisa de mercado encontrada. Rode /pesquisa-mercado para gerar.</div></div>',
    "area_chart_svg": "", "donut_chart_svg": "", "crescimento_fonte": "",
    "reclamacoes_legenda_html": "", "oportunidades_html": "", "bar_chart_svg": "",
    "top5_html": "", "cuidados_html": "", "padroes_reclamacao_html": "",
    "tabela_concorrentes_html": "", "termos_alta_pills": "", "padroes_anuncio_html": "",
    "youtube_tabela_html": "", "youtube_detalhes_html": "", "padroes_youtube_html": "",
    "alertas_regulatorios_section": "", "circular_progress_svg": "",
    "qtd_fontes": "0", "fontes_html": "",
}

def build_kpi_card(label, valor, trend, grad_id):
    trend_class = "trend-up" if trend and any(c in trend for c in ["+", "acima", "cresci"]) else "trend-neutral"
    trend_icon = "&#9650;" if "trend-up" in trend_class else "&#9679;"
    return f'''<div class="card">
        <div class="card-label">{esc(label)}</div>
        <div class="kpi-value">{esc(valor)}</div>
        <div class="kpi-trend {trend_class}">{trend_icon} {esc(trend)}</div>
        <svg width="100%" height="36" viewBox="0 0 120 36" style="margin-top:8px;display:block">
          <defs><linearGradient id="{grad_id}" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="#22c55e" stop-opacity=".2"/><stop offset="100%" stop-color="#22c55e" stop-opacity="0"/></linearGradient></defs>
          <path d="M0,28 C20,24 40,20 60,16 C80,12 100,8 120,4" stroke="#22c55e" stroke-width="1.5" fill="none"/>
          <path d="M0,28 C20,24 40,20 60,16 C80,12 100,8 120,4 L120,36 L0,36 Z" fill="url(#{grad_id})"/>
        </svg>
      </div>'''

def build_bar_chart_svg(concorrentes, preco_produto):
    """Gera bar chart SVG de precos extraidos dos concorrentes."""
    # extrair todos os precos numericos
    todos_precos = []
    for c in concorrentes:
        p = c.get("preco", "")
        # pegar primeiro numero da string (ex: "R$ 187/mes" -> 187, "R$ 197-497" -> 197)
        nums = re.findall(r'(\d+)', p.replace(".", "").replace(",", ""))
        if nums:
            todos_precos.append(int(nums[0]))

    if len(todos_precos) < 3:
        return ""

    # criar faixas de preco automaticamente
    todos_precos.sort()
    faixas = {}
    for val in todos_precos:
        if val <= 50:
            faixas.setdefault("Entrada", []).append(val)
        elif val <= 150:
            faixas.setdefault("Basico", []).append(val)
        elif val <= 250:
            faixas.setdefault("Intermediario", []).append(val)
        elif val <= 400:
            faixas.setdefault("Premium", []).append(val)
        else:
            faixas.setdefault("High Ticket", []).append(val)

    if not faixas:
        return ""

    # media por faixa
    cats = []
    for nome, vals in faixas.items():
        media = sum(vals) // len(vals)
        cats.append((nome, media))
    cats.sort(key=lambda x: x[1])

    max_val = max(v for _, v in cats)
    bar_w = 50
    gap = 80
    total_w = len(cats) * gap + 40

    # preco do produto pra destacar
    preco_num = 0
    pnums = re.findall(r'(\d+)', str(preco_produto).replace(".", "").replace(",", ""))
    if pnums:
        preco_num = int(pnums[0])

    svg = f'<svg viewBox="0 0 {total_w} 220" width="100%" style="display:block;margin-top:12px">\n'
    for i, (cat, val) in enumerate(cats):
        x = 30 + i * gap
        h = max(20, int(180 * val / max_val))
        y = 200 - h
        # destacar faixa que contem o preco do produto
        is_product = preco_num > 0 and abs(val - preco_num) <= 50
        fill = "#16a34a" if is_product else "#22c55e"
        svg += f'  <rect x="{x}" y="{y}" width="{bar_w}" height="{h}" fill="{fill}" rx="3"/>\n'
        svg += f'  <text x="{x + bar_w//2}" y="{y - 5}" font-size="11" fill="#374151" text-anchor="middle" font-weight="600">R${val}</text>\n'
        svg += f'  <text x="{x + bar_w//2}" y="215" font-size="10" fill="#6b7280" text-anchor="middle">{esc(cat)}</text>\n'
        if is_product:
            svg += f'  <rect x="{x - 5}" y="{y - 44}" width="60" height="16" rx="8" fill="#dcfce7"/>\n'
            svg += f'  <text x="{x + bar_w//2}" y="{y - 33}" font-size="9" fill="#16a34a" text-anchor="middle" font-weight="700">SEU PRODUTO</text>\n'
    svg += '</svg>'
    return svg

def build_complaint_bars(reclamacoes):
    """Gera barras horizontais para reclamacoes (distribui % igualmente se nao tiver dados)."""
    if not reclamacoes:
        return ""
    n = len(reclamacoes)
    pct_each = 100 // n
    html = ""
    for i, r in enumerate(reclamacoes):
        pct = pct_each if i < n - 1 else 100 - pct_each * (n - 1)
        html += f'''<div class="complaint-row">
            <div class="complaint-label"><span>{esc(r[:60])}</span><span>{pct}%</span></div>
            <div class="complaint-bar-bg"><div class="complaint-bar-fill" style="width:{pct}%"></div></div>
          </div>\n'''
    return html

def build_pesquisa_html(pesq, perfil):
    """Gera HTML completo da tela de pesquisa. So mostra blocos que tem dados."""
    if not pesq.get("tem_pesquisa"):
        return {"pesquisa_completa_html": '<div class="card"><div class="card-label">Pesquisa de mercado</div><div class="card-sub">Nenhuma pesquisa de mercado encontrada. Rode /pesquisa-mercado para gerar.</div></div>'}

    # KPIs (so mostra cards com valor real, esconde N/D)
    kpis = pesq.get("kpis", {})
    n_conc = len(pesq.get("concorrentes", []))
    kpi_candidates = [
        ("Tamanho do Mercado", kpis.get("tamanho_mercado", {}).get("valor", ""), kpis.get("tamanho_mercado", {}).get("trend", ""), "g1"),
        ("Crescimento Anual", kpis.get("crescimento_anual", {}).get("valor", ""), kpis.get("crescimento_anual", {}).get("trend", ""), "g2"),
        ("Concorrentes Mapeados", str(n_conc) if n_conc > 0 else "", "amostra do nicho", "g3"),
        ("Ticket M\u00e9dio do Nicho", kpis.get("ticket_medio", {}).get("valor", ""), kpis.get("ticket_medio", {}).get("trend", ""), "g4"),
    ]
    kpi_items = [(l, v, t, g) for l, v, t, g in kpi_candidates if v and v != "N/D"]
    kpis_html = "\n".join(build_kpi_card(l, v, t, g) for l, v, t, g in kpi_items)

    # oportunidades
    opp_html = ""
    for i, opp in enumerate(pesq.get("oportunidades", []), 1):
        opp_html += f'<li class="opp-item"><div class="opp-num">{i}</div><div class="opp-text">{_md_bold(esc(opp))}</div></li>\n'

    # concorrentes top 5
    cores_avatar = ["#22c55e", "#1d4ed8", "#7c3aed", "#d97706", "#6b7280"]
    top5_html = ""
    for i, c in enumerate(pesq.get("concorrentes", [])[:5]):
        cor = cores_avatar[i % len(cores_avatar)]
        inicial = c["nome"][0].upper() if c["nome"] else "?"
        top5_html += f'''<div class="comp-row">
            <div class="comp-avatar" style="background:{cor}">{inicial}</div>
            <div class="comp-info"><div class="comp-name">{esc(c["nome"])}</div></div>
            <div class="comp-price"><span class="badge badge-blue">{esc(c["preco"])}</span></div>
          </div>\n'''

    # tabela completa
    tabela_html = ""
    for c in pesq.get("concorrentes", []):
        tabela_html += f'<tr><td>{esc(c["nome"])}</td><td>{esc(c.get("obs",""))}</td><td>{esc(c.get("canal",""))}</td><td><span class="badge badge-blue">{esc(c["preco"])}</span></td><td></td></tr>\n'

    # bar chart
    bar_svg = build_bar_chart_svg(pesq.get("concorrentes", []), perfil.get("preco", ""))

    # cuidados
    cuidados_html = build_bullet_list(pesq.get("riscos", []), style="color:var(--badge-orange-text)")

    # reclamacoes com barras
    padroes_recl_html = build_complaint_bars(pesq.get("reclamacoes", []))

    # termos em alta
    termos = pesq.get("termos_alta", [])
    termos_html = ""
    for t in termos:
        sz = "13px" if len(t) > 15 else "11px"
        termos_html += f'<span class="badge badge-green" style="font-size:{sz}">{esc(t)}</span>\n'

    # padroes de anuncio
    padroes_anuncio_html = build_bullet_list(pesq.get("padroes_anuncio", []))

    # youtube
    yt_videos = pesq.get("youtube", [])
    yt_cores = ["#fef3c7,#f59e0b", "#fce7f3,#db2777", "#dbeafe,#1d4ed8", "#dcfce7,#16a34a",
                "#ede9fe,#7c3aed", "#fef3c7,#d97706", "#e0e7ff,#4338ca", "#dcfce7,#16a34a",
                "#fce7f3,#db2777", "#dbeafe,#1d4ed8"]
    yt_tabela = ""
    for i, v in enumerate(yt_videos[:10]):
        cores = yt_cores[i % len(yt_cores)]
        c1, c2 = cores.split(",")
        thumb_text = esc(v.get("thumb_texto", v.get("titulo", "")[:10]))
        link_attr = f'href="{esc(v.get("link", "#"))}" target="_blank"' if v.get("link") else 'href="#"'
        yt_tabela += f'''<tr>
          <td><div style="width:28px;height:28px;border-radius:50%;background:var(--primary-light);color:var(--primary-dark);font-weight:700;font-size:12px;display:flex;align-items:center;justify-content:center">{i+1}</div></td>
          <td><div style="width:80px;height:45px;border-radius:6px;background:linear-gradient(135deg,{c1},{c2});display:flex;align-items:center;justify-content:center;color:#fff;font-size:10px;font-weight:700;text-align:center;line-height:1.2">{thumb_text[:20]}</div></td>
          <td><div style="font-weight:600;font-size:13px;color:var(--text-1)">{esc(v.get("titulo",""))}</div><div style="font-size:11px;color:var(--text-3);margin-top:2px">{esc(v.get("canal",""))}</div></td>
          <td><span class="badge badge-green">{esc(v.get("views",""))}</span></td>
          <td><a {link_attr} style="color:var(--primary);font-size:11px">&#8599; Abrir</a></td>
        </tr>\n'''
    if not yt_tabela:
        yt_tabela = '<tr><td colspan="5" style="text-align:center;color:var(--text-3);padding:20px">Dados do YouTube nao encontrados na pesquisa de mercado.</td></tr>'

    # alertas regulatorios
    alertas = pesq.get("alertas", [])
    alertas_section = ""
    if alertas:
        pills = "\n".join(f'<span class="badge badge-orange">{esc(a)}</span>' for a in alertas)
        alertas_section = f'''<div class="alert-card" style="margin-bottom:16px">
      <div class="alert-title">&#9650; Alertas Regulat\u00f3rios</div>
      <div style="font-size:13px;color:#92400e;line-height:1.7;margin-bottom:10px">Evite as express\u00f5es abaixo em an\u00fancios e p\u00e1ginas de vendas:</div>
      <div class="pill-cloud">{pills}</div>
    </div>'''

    # confianca
    n_fontes = len(pesq.get("fontes", []))
    if n_fontes == 0:
        n_fontes = min(6, len(pesq.get("concorrentes", [])) + len(pesq.get("reclamacoes", [])))
    pct_conf = min(95, max(40, n_fontes * 12 + len(pesq.get("oportunidades", [])) * 5))
    dash = int(289 * pct_conf / 100)
    cor_conf = "#22c55e" if pct_conf >= 70 else "#d97706" if pct_conf >= 50 else "#ef4444"
    circular_svg = f'''<svg viewBox="0 0 120 120" width="120">
            <circle cx="60" cy="60" r="46" stroke="#f3f4f6" stroke-width="10" fill="none"/>
            <circle cx="60" cy="60" r="46" stroke="{cor_conf}" stroke-width="10" fill="none"
              stroke-dasharray="{dash} 289" transform="rotate(-90 60 60)"/>
            <text x="60" y="56" font-size="22" font-weight="800" fill="#111827" text-anchor="middle">{pct_conf}%</text>
            <text x="60" y="72" font-size="10" fill="#6b7280" text-anchor="middle">Confian\u00e7a</text>
          </svg>'''

    # fontes
    fontes = pesq.get("fontes", [])
    if not fontes:
        fontes = ["Pesquisa de mercado do produto"]
    fontes_html = "\n".join(f'<div class="source-item">&#8599; {esc(f)}</div>' for f in fontes)

    # === MONTAR HTML CONDICIONAL (so mostra blocos com dados) ===
    blocks = []

    # KPIs (so mostra se tem pelo menos 1 KPI real, nao N/D)
    has_kpis = any(kpis.get(k, {}).get("valor", "N/D") != "N/D" for k in ["tamanho_mercado", "crescimento_anual", "ticket_medio"])
    if has_kpis or n_conc > 0:
        blocks.append(f'<div class="grid-4" style="margin-bottom:16px">{kpis_html}</div>')

    # Oportunidades
    if opp_html:
        blocks.append(f'''<div class="card" style="margin-bottom:16px">
      <div class="card-label" style="color:var(--primary)">Oportunidades Identificadas</div>
      <ul class="opp-list" style="margin-top:12px">{opp_html}</ul>
    </div>''')

    # Precos + Top 5 (so se tem concorrentes)
    if top5_html:
        left = f'<div class="card"><div class="card-label">Preco M\u00e9dio por Formato</div>{bar_svg}</div>' if bar_svg else ''
        right = f'<div class="card"><div class="card-label">Top 5 Concorrentes</div><div style="margin-top:12px">{top5_html}</div></div>'
        if left:
            blocks.append(f'<div class="grid-2" style="margin-bottom:16px">{left}{right}</div>')
        else:
            blocks.append(f'<div style="margin-bottom:16px">{right}</div>')

    # Cuidados + Reclamacoes (so se tem dados)
    has_cuidados = pesq.get("riscos", [])
    has_recl = pesq.get("reclamacoes", [])
    if has_cuidados or has_recl:
        left = f'<div class="card"><div class="card-label">Cuidados e Riscos</div><ul class="bullet-list" style="margin-top:12px">{cuidados_html}</ul></div>' if has_cuidados else ''
        right = f'<div class="card"><div class="card-label">Padr\u00f5es de Reclama\u00e7\u00e3o (Reclame Aqui)</div><div style="margin-top:12px">{padroes_recl_html}</div></div>' if has_recl else ''
        if left and right:
            blocks.append(f'<div class="grid-2" style="margin-bottom:16px">{left}{right}</div>')
        else:
            blocks.append(f'<div style="margin-bottom:16px">{left}{right}</div>')

    # Tabela de concorrentes (so se tem)
    if tabela_html:
        blocks.append(f'''<div class="card" style="margin-bottom:16px">
      <div class="card-label">An\u00e1lise Completa de Concorrentes</div>
      <div class="table-wrap" style="margin-top:12px">
        <table><thead><tr><th>Nome</th><th>Observa\u00e7\u00e3o</th><th>Canal</th><th>Pre\u00e7o</th><th>Links</th></tr></thead>
        <tbody>{tabela_html}</tbody></table>
      </div>
    </div>''')

    # Termos + Padroes de anuncio (so se tem)
    if termos_html or padroes_anuncio_html:
        left = f'<div class="card"><div class="card-label">Termos em Alta</div><div class="pill-cloud" style="margin-top:12px">{termos_html}</div></div>' if termos_html else ''
        right = f'<div class="card"><div class="card-label">Padr\u00f5es de An\u00fancio que Performam</div><ul class="bullet-list" style="margin-top:12px">{padroes_anuncio_html}</ul></div>' if padroes_anuncio_html else ''
        if left and right:
            blocks.append(f'<div class="grid-2" style="margin-bottom:16px">{left}{right}</div>')
        elif left or right:
            blocks.append(f'<div style="margin-bottom:16px">{left}{right}</div>')

    # YouTube — cards expandiveis com analise completa
    if yt_videos:
        cards_html = ""
        for i, v in enumerate(yt_videos[:10]):
            cores = yt_cores[i % len(yt_cores)]
            c1, c2 = cores.split(",")
            thumb_label = esc(v.get("thumb_texto") or v.get("titulo", "")[:20])
            link = v.get("link", "") or "#"
            link_html = f'<a href="{esc(link)}" target="_blank" rel="noopener" style="color:var(--primary);font-size:11px" onclick="event.stopPropagation()">&#8599; Assistir</a>' if link != "#" else ""
            meta = ""
            if v.get("views"):
                meta += f'<span class="badge badge-green">{esc(v["views"])}</span> '
            if v.get("data"):
                meta += f'<span style="font-size:10px;color:var(--text-3)">{esc(v["data"])}</span>'
            header = (
                f'<div class="yt-video-header" onclick="this.closest(\'.yt-video-card\').classList.toggle(\'yt-open\')">'
                f'<div class="yt-rank">{i+1}</div>'
                f'<div class="yt-thumb" style="background:linear-gradient(135deg,{c1},{c2})">{thumb_label[:28]}</div>'
                f'<div class="yt-info">'
                f'<div class="yt-title">{esc(v.get("titulo",""))}</div>'
                f'<div class="yt-canal">{esc(v.get("canal",""))}</div>'
                f'<div class="yt-meta">{meta}{link_html}</div>'
                f'</div><span class="yt-toggle">&#9662;</span></div>'
            )
            detail_parts = []
            if v.get("comentarios"):
                coms = "".join(f'<div class="yt-comment">&ldquo;{esc(c)}&rdquo;</div>' for c in v["comentarios"])
                detail_parts.append(f'<div class="yt-section-title">Comentarios em destaque</div>{coms}')
            if v.get("angulo"):
                detail_parts.append(f'<div class="yt-section-title">Angulo do titulo</div><div class="yt-insight" style="background:#eff6ff;color:#1e40af">{esc(v["angulo"])}</div>')
            if v.get("lacuna"):
                detail_parts.append(f'<div class="yt-section-title">Lacuna para o produto</div><div class="yt-insight">{esc(v["lacuna"])}</div>')
            thumb = v.get("thumbnail", {})
            if thumb:
                td = []
                if thumb.get("cores"): td.append(f"<strong>Cores:</strong> {esc(thumb['cores'])}")
                if thumb.get("expressao"): td.append(f"<strong>Expressao:</strong> {esc(thumb['expressao'])}")
                if thumb.get("texto"): td.append(f"<strong>Texto:</strong> {esc(thumb['texto'])}")
                if thumb.get("elementos"): td.append(f"<strong>Elementos:</strong> {esc(thumb['elementos'])}")
                if thumb.get("composicao"): td.append(f"<strong>Composicao:</strong> {esc(thumb['composicao'])}")
                if td:
                    detail_parts.append(f'<div class="yt-section-title">Analise da thumbnail</div><div class="yt-thumb-detail">{"<br>".join(td)}</div>')
            detail = f'<div class="yt-detail">{"".join(detail_parts)}</div>' if detail_parts else ""
            cards_html += f'<div class="yt-video-card">{header}{detail}</div>\n'
        blocks.append(f'<div class="card" style="margin-bottom:16px"><div class="card-label">Top 10 V\u00eddeos do YouTube no Nicho</div><div style="margin-top:12px">{cards_html}</div></div>')

    # Público-Alvo Real
    pa = pesq.get("publico_alvo") or {}
    if pa:
        raw = pa.get("raw") or []
        demo = pa.get("demo") or []
        comport = pa.get("comportamento") or []
        consci = pa.get("consciencia") or []
        if raw:
            lis = build_bullet_list(raw)
            blocks.append(f'<div class="card" style="margin-bottom:16px"><div class="card-label">P\u00fablico-Alvo Real</div><ul class="bullet-list" style="margin-top:12px">{lis}</ul></div>')
        elif any([demo, comport, consci]):
            left = f'<div class="card"><div class="card-label">Perfil Demogr\u00e1fico</div><ul class="bullet-list" style="margin-top:12px">{build_bullet_list(demo)}</ul></div>' if demo else ''
            mid = f'<div class="card"><div class="card-label">Comportamento</div><ul class="bullet-list" style="margin-top:12px">{build_bullet_list(comport)}</ul></div>' if comport else ''
            right = f'<div class="card"><div class="card-label">N\u00edvel de Consci\u00eancia (Schwartz)</div><ul class="bullet-list" style="margin-top:12px">{build_bullet_list(consci)}</ul></div>' if consci else ''
            blocks.append(f'<div class="grid-3" style="margin-bottom:16px">{left}{mid}{right}</div>')

    # Assuntos Quentes e Ângulos Virais
    assuntos = pesq.get("assuntos_quentes") or {}
    if assuntos and any(assuntos.values()):
        termos_aq = assuntos.get("termos", [])
        virais_aq = assuntos.get("virais", [])
        ganchos_aq = assuntos.get("ganchos", [])
        partes_aq = []
        if termos_aq:
            pills = "".join(f'<span class="badge badge-blue" style="font-size:12px">{esc(t)}</span>\n' for t in termos_aq)
            partes_aq.append(f'<div class="card-label" style="margin-bottom:8px;margin-top:4px">Termos em alta</div><div class="pill-cloud" style="margin-bottom:16px">{pills}</div>')
        if ganchos_aq:
            lis = build_bullet_list(ganchos_aq)
            partes_aq.append(f'<div class="card-label" style="margin-bottom:8px">Ganchos que performam</div><ul class="bullet-list" style="margin-bottom:16px">{lis}</ul>')
        if virais_aq:
            lis = build_bullet_list(virais_aq)
            partes_aq.append(f'<div class="card-label" style="margin-bottom:8px">Conteúdos virais recentes</div><ul class="bullet-list">{lis}</ul>')
        if partes_aq:
            blocks.append(f'<div class="card" style="margin-bottom:16px"><div class="card-label" style="color:var(--primary)">Assuntos Quentes e Ângulos Virais</div><div style="margin-top:12px">{"".join(partes_aq)}</div></div>')

    # Biblioteca de Anúncios
    bibl = pesq.get("biblioteca_anuncios") or {}
    if bibl and any(bibl.values()):
        headlines_bl = bibl.get("headlines", [])
        padroes_of = bibl.get("padroes_oferta", [])
        criativos_bl = bibl.get("criativos", [])
        obs_bl = bibl.get("observacoes", [])
        col_esq = ""
        col_dir = ""
        if headlines_bl:
            col_esq += f'<div class="card-label" style="margin-bottom:8px">Padrões de headline</div><ul class="bullet-list" style="margin-bottom:16px">{build_bullet_list(headlines_bl)}</ul>'
        if padroes_of:
            col_esq += f'<div class="card-label" style="margin-bottom:8px">Padrões de oferta</div><ul class="bullet-list">{build_bullet_list(padroes_of)}</ul>'
        if criativos_bl:
            col_dir += f'<div class="card-label" style="margin-bottom:8px">Criativos ativos no nicho</div><ul class="bullet-list" style="margin-bottom:16px">{build_bullet_list(criativos_bl)}</ul>'
        if obs_bl:
            col_dir += f'<div class="card-label" style="margin-bottom:8px">Observações</div><ul class="bullet-list">{build_bullet_list(obs_bl)}</ul>'
        if col_esq and col_dir:
            content_bl = f'<div style="display:grid;grid-template-columns:1fr 1fr;gap:16px"><div>{col_esq}</div><div>{col_dir}</div></div>'
        else:
            content_bl = f'<div>{col_esq}{col_dir}</div>'
        if col_esq or col_dir:
            blocks.append(f'<div class="card" style="margin-bottom:16px"><div class="card-label" style="color:var(--primary)">Biblioteca de Anúncios</div><div style="margin-top:12px">{content_bl}</div></div>')

    # Alertas
    if alertas_section:
        blocks.append(alertas_section)

    # Confianca + Fontes (sempre mostra)
    blocks.append(f'''<div class="card">
      <div class="circ-wrap">
        <div style="text-align:center">{circular_svg}<div class="circ-label">Confiabilidade da pesquisa</div></div>
        <div style="flex:1">
          <div class="card-label">Fontes Consultadas ({n_fontes})</div>
          <div class="sources-grid" style="margin-top:10px">{fontes_html}</div>
        </div>
      </div>
    </div>''')

    return {"pesquisa_completa_html": "\n\n".join(blocks)}

# ── main ─────────────────────────────────────────────────────────────

# ── diagnostico de formato ───────────────────────────────────────────

FORMATOS = {
    "macroetapas": "### Nome da Etapa\\nDescrição  OU  1. **Nome.** Descrição",
    "decorados": "### {cat}\\n- Item 1\\n- Item 2  (lista com -, 10 por categoria)",
    "urgencias": "### {cat}\\n- Item 1\\n- Item 2  (lista com -, 10 por categoria)",
    "argumentos": "- Argumento 1\\n- Argumento 2  (lista com -, dentro de ## Argumentos)",
    "objecoes": "### Objeção 1: \"Texto\"\\n**1. Argumento incontestável**\\nTexto...",
    "baldes": "> Pra quem e: Nome\\n1. Item  OU  > Pra quem e - Nome\\n1. Item",
    "paliativos": "- Paliativo 1\\n- Paliativo 2  (lista com -)",
    "reclamacoes": "Seção ## Reclamações ou ## Reclame Aqui\\n- Reclamação 1\\n- Reclamação 2",
    "oportunidades": "- Oportunidade 1\\n- Oportunidade 2  (lista com -)",
    "concorrentes": "| Nome | Canal | Preço | Obs |\\n|---|---|---|---|",
    "riscos": "- Risco 1\\n- Risco 2  (lista com -)",
}

def diagnose(raw_text, keywords, n_items, hint_key, cat=""):
    """Diagnostica falha de parse: seção ausente vs formato incompatível."""
    if not raw_text:
        return ""
    sec = parse_section_fuzzy(raw_text, *keywords)
    hint = FORMATOS.get(hint_key, "")
    if cat:
        hint = hint.replace("{cat}", cat)
    if not sec:
        return f"  >> CAUSA: seção '{keywords[0]}' não encontrada no .md\n      Formato aceito: {hint}"
    if cat:
        has_sub = bool(re.search(rf'^###\s+.*{re.escape(cat)}', sec, re.MULTILINE | re.IGNORECASE))
        if not has_sub:
            return f"  >> CAUSA: subseção '### {cat}' não encontrada dentro de '{keywords[0]}'\n      Formato aceito: {hint}"
        sub_match = re.search(rf'^###\s+.*{re.escape(cat)}.*?\n(.*?)(?=^###\s|\Z)', sec, re.MULTILINE | re.DOTALL | re.IGNORECASE)
        if sub_match and n_items == 0:
            trecho = sub_match.group(1)[:100].replace('\n', ' ').strip()
            return f"  >> CAUSA: subseção '### {cat}' existe mas itens não parseados (esperado: lista com -)\n      Trecho: \"{trecho}\"\n      Formato aceito: {hint}"
    if n_items == 0:
        trecho = sec[:100].replace('\n', ' ').strip()
        return f"  >> CAUSA: seção existe mas formato não reconhecido pelo parser\n      Trecho: \"{trecho}\"\n      Formato aceito: {hint}"
    return ""

# ── validacao ────────────────────────────────────────────────────────

def validate(data, rules):
    """Valida dados contra regras. Retorna lista de (status, msg)."""
    results = []
    for field, label, check_fn, expected in rules:
        value = data
        for key in field.split("."):
            value = value.get(key, {}) if isinstance(value, dict) else {}
        ok, detail = check_fn(value, expected)
        status = "OK" if ok else "!!"
        results.append((status, label, detail))
    return results

def check_not_empty(value, _):
    if isinstance(value, str) and value.strip():
        return True, f'"{value[:50]}..."' if len(str(value)) > 50 else f'"{value}"'
    if isinstance(value, list) and len(value) > 0:
        return True, f"{len(value)} itens"
    if isinstance(value, dict) and len(value) > 0:
        return True, f"{len(value)} campos"
    return False, "vazio"

def check_count(value, expected):
    if isinstance(value, list):
        n = len(value)
        if n >= expected:
            return True, f"{n}/{expected} itens"
        return False, f"{n}/{expected} itens (faltam {expected - n})"
    return False, "nao e uma lista"

def check_exact(value, expected):
    if isinstance(value, list):
        n = len(value)
        if n == expected:
            return True, f"{n}/{expected} itens"
        return False, f"{n}/{expected} itens"
    return False, "nao e uma lista"

def check_min(value, expected):
    if isinstance(value, list):
        n = len(value)
        if n >= expected:
            return True, f"{n} itens"
        return False, f"{n} itens (minimo {expected})"
    if isinstance(value, str) and value.strip():
        return True, "preenchido"
    return False, "vazio"

def build_quiz_card(produto_path):
    """
    Le quiz-meta.json (gerado por /lt-quiz no passo 6.3) e devolve HTML do card.
    Se nao houver quiz gerado, devolve string vazia (card nao aparece).
    """
    meta_path = produto_path / "entregas" / "quiz" / "quiz-meta.json"
    if not meta_path.exists():
        # detecta fallback: arquivo do prompt foi gerado mas o meta ainda nao
        quiz_dir = produto_path / "entregas" / "quiz"
        if quiz_dir.exists():
            md_files = list(quiz_dir.glob("quiz-*.md"))
            if md_files:
                rel_path = md_files[0].relative_to(produto_path.parent.parent).as_posix()
                return (
                    '<div class="card" style="margin-bottom:24px;border-left:4px solid var(--gold-light, #D4A373);">'
                    '<div class="card-label" style="display:flex;align-items:center;gap:8px;">'
                    '<span>Funil. Quiz no Lovable</span>'
                    '<span class="badge badge-yellow" style="font-size:11px;">Sem metadados</span>'
                    '</div>'
                    '<div style="margin-top:12px;font-size:13px;color:var(--text-2);">'
                    f'<strong>Prompt salvo em:</strong> <code>{esc(rel_path)}</code><br>'
                    'Rode <code>/lt-quiz</code> de novo para registrar o link do Lovable e gerar o <code>quiz-meta.json</code>.'
                    '</div>'
                    '</div>'
                )
        return ""

    try:
        meta = json.loads(meta_path.read_text(encoding="utf-8"))
    except Exception:
        return ""

    prompt_path = meta.get("prompt_path", "")
    lovable_url = meta.get("lovable_url", "nao_publicado")
    generated_at = meta.get("generated_at", "")
    url_updated_at = meta.get("url_updated_at", "")

    is_published = lovable_url and lovable_url != "nao_publicado" and (
        lovable_url.startswith("http://") or lovable_url.startswith("https://")
    )

    if is_published:
        link_html = (
            f'<a href="{esc(lovable_url)}" target="_blank" rel="noopener" '
            'style="color:var(--gold-light, #D4A373);text-decoration:underline;font-weight:600;">'
            f'{esc(lovable_url)}</a>'
        )
        status_badge = '<span class="badge badge-green" style="font-size:11px;">Publicado</span>'
    else:
        link_html = (
            '<span style="color:var(--text-3);font-style:italic;">Quiz ainda nao publicado no Lovable. '
            'Rode <code>/lt-quiz</code> ou <code>/quiz-link</code> para registrar o link.</span>'
        )
        status_badge = '<span class="badge badge-yellow" style="font-size:11px;">Pendente</span>'

    return (
        '<div class="card" style="margin-bottom:24px;border-left:4px solid var(--gold-light, #D4A373);">'
        '<div class="card-label" style="display:flex;align-items:center;gap:8px;">'
        '<span>Funil. Quiz no Lovable</span>'
        f'{status_badge}'
        '</div>'
        '<div style="margin-top:12px;display:grid;gap:8px;font-size:13px;color:var(--text-2);">'
        f'<div><strong>Prompt para Lovable:</strong> <code>{esc(prompt_path)}</code></div>'
        f'<div><strong>Link publicado:</strong> {link_html}</div>'
        f'<div style="font-size:11px;color:var(--text-3);">Gerado em: {esc(generated_at)}'
        + (f' &middot; Link atualizado em: {esc(url_updated_at)}' if url_updated_at else '')
        + '</div>'
        '</div>'
        '</div>'
    )


def validate_copy_pagina(produto_path, slug):
    """Valida e imprime status da secao Copy da Pagina.
    Retorna dict com blocos, arquivo_relativo, arquivo_existe, warnings."""
    dados = _tmpl.parse_copy_pagina(produto_path, slug, ROOT)
    blocos = dados.get("blocos", [])
    existe = dados.get("arquivo_existe", False)
    total = len(blocos)

    print("\nCOPY-PAGINA/COPY-{slug}.MD".replace("{slug}", slug))
    warnings = []
    if not existe:
        print("  [!!] Arquivo nao encontrado (entregas/copy-pagina/copy-{}.md)".format(slug))
        print("       Rode /copy-pagina para gerar a copy nos 16 blocos.")
        warnings.append("copy-pagina: arquivo nao encontrado")
    elif total == 0:
        print("  [!!] Arquivo existe mas nao tem blocos no padrao '## Bloco NN - Nome'")
        warnings.append("copy-pagina: 0 blocos detectados (checar formato '## Bloco 01 - Hero' etc.)")
    elif total < 16:
        print(f"  [!!] Blocos aprovados: {total}/16. Faltam {16 - total} para completar a copy.")
        numeros_presentes = {b["numero"] for b in blocos}
        faltantes = [f"{n:02d}" for n in range(1, 17) if n not in numeros_presentes]
        print(f"       Faltantes: {', '.join(faltantes)}")
        warnings.append(f"copy-pagina: {total}/16 blocos (faltam {', '.join(faltantes)})")
    else:
        print(f"  [OK] Blocos aprovados: {total}/16 (completo)")
    return dados, warnings


def run_validation(perfil, idc, pesq, tipo, perfil_text="", idc_text="", pesq_text=""):
    """Roda todas as validacoes e retorna relatorio com diagnostico de formato."""
    is_low = "low" in tipo.lower()
    warnings = []
    total_ok = 0
    total_warn = 0

    print("\n=== VALIDACAO DO PAINEL DE ENTREGAS ===\n")

    # --- PERFIL.MD ---
    print("PERFIL.MD")
    perfil_checks = [
        ("quadro", "Quadro", check_not_empty, None),
        ("nome_metodo", "Furadeira > Nome do metodo", check_not_empty, None),
        ("macroetapas", "Furadeira > Macroetapas", check_min, 2),
        ("comunicador_nome", "Comunicador > Nome", check_not_empty, None),
        ("valores", "Comunicador > Valores", check_min, 1),
        ("tom_de_voz", "Comunicador > Tom de voz", check_not_empty, None),
        ("posicionamento", "Comunicador > Posicionamento", check_not_empty, None),
        ("tonalidade_emocional", "Comunicador > Tonalidade emocional", check_not_empty, None),
        ("formatos", "Comunicador > Formatos", check_min, 1),
        ("referencias", "Comunicador > Referencias", check_min, 1),
        ("argumentos", "Argumentos Incontestaveis", check_min, 4),
        ("preco", "Preco", check_not_empty, None),
        ("nicho", "Nicho", check_not_empty, None),
        ("diferencial_raw", "Diferencial", check_not_empty, None),
        ("formato_produto", "Formato", check_not_empty, None),
    ]
    # mapa de diagnostico para campos estruturados do perfil
    perfil_diag_map = {
        "macroetapas": (["Furadeira"], "macroetapas"),
        "argumentos": (["Argumentos Incontestáveis", "Argumentos Incontestaveis"], "argumentos"),
    }
    for field, label, fn, expected in perfil_checks:
        value = perfil.get(field, "")
        ok, detail = fn(value, expected)
        status = "OK" if ok else "!!"
        print(f"  [{status}] {label}: {detail}")
        if ok:
            total_ok += 1
        else:
            total_warn += 1
            if field in perfil_diag_map:
                kw, hk = perfil_diag_map[field]
                n = len(value) if isinstance(value, list) else 0
                diag = diagnose(perfil_text, kw, n, hk)
                if diag:
                    print(diag)
            warnings.append(f"perfil.md > {label}: {detail}")

    # decorados
    dec = perfil.get("decorados", {})
    for cat in ["Financeiro", "Tempo", "Autoestima", "Reputação", "Crescimento"]:
        items = dec.get(cat, {}).get("items", [])
        ok = len(items) == 10
        status = "OK" if ok else "!!"
        detail = f"{len(items)}/10 itens"
        print(f"  [{status}] Decorados > {cat}: {detail}")
        if ok:
            total_ok += 1
        else:
            total_warn += 1
            diag = diagnose(perfil_text, ["Decorados"], len(items), "decorados", cat)
            if diag:
                print(diag)
            warnings.append(f"perfil.md > Decorados > {cat}: {detail}")

    # urgencias
    urg = perfil.get("urgencias", {})
    urg_names = {
        "Dores": "Dores",
        "Dúvidas": "Duvidas",
        "Desejos": "Desejos",
        "Assuntos Relacionados": "Assuntos Relacionados",
        "Urgências Quentes": "Urgencias Quentes",
        "Urgências Frias": "Urgencias Frias",
        "Urgências Inusitadas": "Urgencias Inusitadas",
    }
    for key, display in urg_names.items():
        items = urg.get(key, {}).get("items", [])
        ok = len(items) == 10
        status = "OK" if ok else "!!"
        detail = f"{len(items)}/10 itens"
        print(f"  [{status}] Urgencias > {display}: {detail}")
        if ok:
            total_ok += 1
        else:
            total_warn += 1
            diag = diagnose(perfil_text, ["Urgências Ocultas", "Urgencias Ocultas"], len(items), "urgencias", key)
            if diag:
                print(diag)
            warnings.append(f"perfil.md > Urgencias > {display}: {detail}")

    # --- IDCONSUMIDOR.MD ---
    print("\nIDCONSUMIDOR.MD")
    if not idc:
        print("  [!!] Arquivo nao encontrado")
        total_warn += 1
        warnings.append("idconsumidor.md: arquivo nao encontrado")
    else:
        idc_checks = [
            ("para_quem_e", "Para Quem E", check_not_empty, None),
            ("genero", "Perfil > Genero", check_not_empty, None),
            ("idade", "Perfil > Idade", check_not_empty, None),
            ("profissao", "Perfil > Profissao", check_not_empty, None),
            ("renda", "Perfil > Renda", check_not_empty, None),
            ("nivel_consciencia", "Perfil > Nivel consciencia", check_not_empty, None),
            ("onde_busca", "Perfil > Onde busca info", check_not_empty, None),
            ("palavras_conectam", "Palavras que conectam", check_min, 5),
            ("palavras_afastam", "Palavras que afastam", check_min, 5),
        ]
        for field, label, fn, expected in idc_checks:
            value = idc.get(field, "")
            ok, detail = fn(value, expected)
            status = "OK" if ok else "!!"
            print(f"  [{status}] {label}: {detail}")
            if ok:
                total_ok += 1
            else:
                total_warn += 1
                warnings.append(f"idconsumidor.md > {label}: {detail}")

        # objecoes
        objs = idc.get("objecoes", [])
        ok_obj = len(objs) == 5
        status = "OK" if ok_obj else "!!"
        print(f"  [{status}] Objecoes: {len(objs)}/5")
        if ok_obj:
            total_ok += 1
        else:
            total_warn += 1
            diag = diagnose(idc_text, ["Objeções de Compra", "Objecoes de Compra"], len(objs), "objecoes")
            if diag:
                print(diag)
            warnings.append(f"idconsumidor.md > Objecoes: {len(objs)}/5")

        for i, obj in enumerate(objs, 1):
            n_args = len(obj.get("argumentos", []))
            ok_a = n_args == 7
            status = "OK" if ok_a else "!!"
            print(f"  [{status}] Objecao {i} argumentos: {n_args}/7")
            if ok_a:
                total_ok += 1
            else:
                total_warn += 1
                if n_args == 0:
                    print(f"  CAUSA: argumentos da objeção {i} não parseados. Formato: **1. Argumento incontestável**\\nTexto...")
                warnings.append(f"idconsumidor.md > Objecao {i}: {n_args}/7 argumentos")

        # baldes
        baldes = idc.get("baldes", [])
        ok_b = 3 <= len(baldes) <= 5
        status = "OK" if ok_b else "!!"
        print(f"  [{status}] Baldes: {len(baldes)} (esperado 3-5)")
        if ok_b:
            total_ok += 1
        else:
            total_warn += 1
            diag = diagnose(idc_text, ["Baldes de Para Quem"], len(baldes), "baldes")
            if diag:
                print(diag)
            warnings.append(f"idconsumidor.md > Baldes: {len(baldes)} (esperado 3-5)")

        # paliativos (so middle ticket)
        if not is_low:
            pals = idc.get("paliativos", [])
            ok_p = len(pals) >= 3
            status = "OK" if ok_p else "!!"
            print(f"  [{status}] Paliativos (Middle Ticket): {len(pals)} itens")
            if ok_p:
                total_ok += 1
            else:
                total_warn += 1
                diag = diagnose(idc_text, ["Paliativos"], len(pals), "paliativos")
                if diag:
                    print(diag)
                warnings.append(f"idconsumidor.md > Paliativos: {len(pals)} itens (minimo 3)")

    # --- PESQUISA-MERCADO.MD ---
    print("\nPESQUISA-MERCADO.MD")
    if not pesq.get("tem_pesquisa"):
        print("  [!!] Arquivo nao encontrado")
        total_warn += 1
        warnings.append("pesquisa-mercado.md: arquivo nao encontrado")
    else:
        pesq_checks = [
            ("oportunidades", "Oportunidades", check_min, 3),
            ("concorrentes", "Concorrentes", check_min, 5),
            ("reclamacoes", "Reclamacoes", check_min, 2),
            ("riscos", "Cuidados e Riscos", check_min, 2),
        ]
        pesq_diag_map = {
            "oportunidades": (["Oportunidades"], "oportunidades"),
            "concorrentes": (["Principais Concorrentes", "Concorrentes"], "concorrentes"),
            "reclamacoes": (["Reclame Aqui", "Reclamações Reais", "Reclamações", "Reclamacoes"], "reclamacoes"),
            "riscos": (["Riscos", "Cuidados"], "riscos"),
        }
        for field, label, fn, expected in pesq_checks:
            value = pesq.get(field, [])
            ok, detail = fn(value, expected)
            status = "OK" if ok else "!!"
            print(f"  [{status}] {label}: {detail}")
            if ok:
                total_ok += 1
            else:
                total_warn += 1
                if field in pesq_diag_map:
                    kw, hk = pesq_diag_map[field]
                    n = len(value) if isinstance(value, list) else 0
                    diag = diagnose(pesq_text, kw, n, hk)
                    if diag:
                        print(diag)
                warnings.append(f"pesquisa-mercado.md > {label}: {detail}")

    # resumo
    print(f"\nRESULTADO: {total_ok} OK, {total_warn} avisos.")
    if warnings:
        print("Secoes com problemas:")
        for w in warnings:
            print(f"  - {w}")
        print(f"\nPainel gerado com {total_warn} secoes incompletas.")
        print("Corrigir os .md e rodar novamente: py -3 scripts/build-painel-entregas.py")
    else:
        print("Tudo OK. Painel completo.")

    return warnings


def save_json_cache(produto_path, perfil, idc, pesq, tipo, copy_dados=None):
    """Salva cache JSON dos dados parseados."""
    copy_dados = copy_dados or {}
    cache = {
        "perfil": {
            "nome_produto": perfil.get("nome_produto_field", perfil.get("nome_produto", "")),
            "quadro": perfil.get("quadro", ""),
            "nome_metodo": perfil.get("nome_metodo", ""),
            "macroetapas": perfil.get("macroetapas", []),
            "preco": perfil.get("preco", ""),
            "nicho": perfil.get("nicho", ""),
            "diferencial": perfil.get("diferencial_raw", ""),
            "formato": perfil.get("formato_produto", ""),
            "comunicador": {
                "nome": perfil.get("comunicador_nome", ""),
                "especialidade": perfil.get("comunicador_especialidade", ""),
                "valores": perfil.get("valores", []),
                "tom_de_voz": perfil.get("tom_de_voz", ""),
                "posicionamento": perfil.get("posicionamento", ""),
                "tonalidade_emocional": perfil.get("tonalidade_emocional", ""),
                "mantras": perfil.get("mantras", []),
                "referencias": perfil.get("referencias", []),
                "formatos": perfil.get("formatos", []),
                "estilo_visual": perfil.get("estilo_visual", []),
            },
            "decorados": {k: v.get("items", []) for k, v in perfil.get("decorados", {}).items()},
            "urgencias": {k: v.get("items", []) for k, v in perfil.get("urgencias", {}).items()},
            "argumentos": perfil.get("argumentos", []),
        },
        "idconsumidor": {
            "para_quem_e": idc.get("para_quem_e", ""),
            "genero": idc.get("genero", ""),
            "idade": idc.get("idade", ""),
            "profissao": idc.get("profissao", ""),
            "renda": idc.get("renda", ""),
            "localizacao": idc.get("localizacao", ""),
            "nivel_consciencia": idc.get("nivel_consciencia", ""),
            "onde_busca": idc.get("onde_busca", ""),
            "palavras_conectam": idc.get("palavras_conectam", []),
            "palavras_afastam": idc.get("palavras_afastam", []),
            "objecoes": idc.get("objecoes", []),
            "baldes": idc.get("baldes", []),
            "paliativos": idc.get("paliativos", []),
        },
        "pesquisa": {
            "tem_pesquisa": pesq.get("tem_pesquisa", False),
            "oportunidades": pesq.get("oportunidades", []),
            "concorrentes": pesq.get("concorrentes", []),
            "reclamacoes": pesq.get("reclamacoes", []),
            "riscos": pesq.get("riscos", []),
        },
        "copy_pagina": {
            "arquivo_existe": copy_dados.get("arquivo_existe", False),
            "arquivo_relativo": copy_dados.get("arquivo_relativo", ""),
            "total_blocos": len(copy_dados.get("blocos", [])),
            "numeros_aprovados": sorted(
                b.get("numero") for b in copy_dados.get("blocos", []) if b.get("numero")
            ),
        },
        "tipo": tipo,
    }

    cache_path = produto_path / "painel-cache.json"
    cache_path.write_text(json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8")
    return cache_path


def main():
    slug = get_slug()
    produto_path = PRODUTOS / slug

    print(f"Produto: {slug}")
    print(f"Pasta: {produto_path}")

    # ler arquivos
    perfil_text = read_file(produto_path / "perfil.md")
    idc_text = read_file(produto_path / "idconsumidor.md")
    pesq_text = read_file(produto_path / "pesquisa-mercado.md")
    tipo_text = read_file(produto_path / "tipo.md").strip()

    if not perfil_text:
        print("Erro: perfil.md nao encontrado. Rode /produto-concepcao primeiro.")
        sys.exit(1)

    # parsear
    perfil = parse_perfil(perfil_text)
    idc = parse_idconsumidor(idc_text) if idc_text else {}
    pesq = parse_pesquisa(pesq_text) if pesq_text else {"tem_pesquisa": False}

    tipo = tipo_text or perfil.get("tipo_raw", "Middle Ticket")
    is_low = "low" in tipo.lower()

    # validar
    warnings = run_validation(perfil, idc, pesq, tipo, perfil_text, idc_text, pesq_text)

    # validar copy da pagina (secao entregas)
    copy_dados, copy_warnings = validate_copy_pagina(produto_path, slug)
    warnings.extend(copy_warnings)

    # salvar cache JSON
    cache_path = save_json_cache(produto_path, perfil, idc, pesq, tipo, copy_dados)
    print(f"\nCache JSON salvo em: {cache_path.name}")

    # ler template
    template = TEMPLATE.read_text(encoding="utf-8")

    # montar diferencial
    dif_raw = perfil.get("diferencial_raw", "")
    dif_parts = dif_raw.split(".", 1) if dif_raw else ["", ""]
    dif_titulo = dif_parts[0].strip() if dif_parts[0] else dif_raw
    dif_desc = dif_parts[1].strip() if len(dif_parts) > 1 else ""

    # paliativos section
    pal_section = ""
    if not is_low and idc.get("paliativos"):
        pal_items = build_bullet_list(idc["paliativos"])
        pal_section = f'''<div class="card" style="margin-bottom:16px">
      <div class="card-label">Paliativos</div>
      <ul class="bullet-list" style="margin-top:12px">{pal_items}</ul>
    </div>'''

    # pesquisa html
    pesq_html = build_pesquisa_html(pesq, perfil)

    # furadeira PNG (gerada por /furadeira-visual)
    furadeira_path = produto_path / "entregas" / "furadeira" / "furadeira.png"
    if furadeira_path.exists():
        botao_furadeira = (
            '<div style="margin-top:24px;padding:16px;background:rgba(255,255,255,0.04);'
            'border:1px solid rgba(255,255,255,0.08);border-radius:8px;text-align:center;">'
            '<img src="entregas/furadeira/furadeira.png" alt="Furadeira do metodo" '
            'style="max-width:100%;height:auto;border-radius:4px;display:block;margin:0 auto;" />'
            '</div>'
        )
    else:
        botao_furadeira = ''

    # substituicoes
    replacements = {
        "{{ nome_produto }}": perfil.get("nome_produto_field", perfil["nome_produto"]),
        "{{ nome_comunicador }}": perfil.get("comunicador_nome", ""),
        "{{ subtitulo_produto }}": perfil.get("nicho", ""),
        "{{ tipo_produto }}": tipo,
        "{{ formato_produto }}": perfil.get("formato_produto", ""),
        "{{ preco }}": perfil.get("preco", ""),
        "{{ posicionamento_preco }}": "Posicionamento do nicho",
        "{{ quadro }}": perfil.get("quadro", ""),
        "{{ nicho }}": perfil.get("nicho", ""),
        "{{ nicho_subtitulo }}": perfil.get("nicho_subtitulo", ""),
        "{{ diferencial_titulo }}": dif_titulo,
        "{{ diferencial_descricao }}": dif_desc,
        "{{ badges_completude }}": build_badges_completude(produto_path),
        "{{ nome_metodo }}": perfil.get("nome_metodo", ""),
        "{{ macroetapas_html }}": build_macroetapas_html(perfil.get("macroetapas", [])),
        "{{ botao_furadeira_visual }}": botao_furadeira,
        "{{ decorados_html }}": build_decorados_html(perfil.get("decorados", {})),
        "{{ urgencias_html }}": build_urgencias_html(perfil.get("urgencias", {})),
        "{{ diferencial_texto }}": dif_raw,
        "{{ formato_texto }}": perfil.get("formato_produto", ""),
        "{{ argumentos_html }}": build_bullet_list(perfil.get("argumentos", [])),
        "{{ objecoes_html }}": build_objecoes_html(idc.get("objecoes", [])),
        "{{ para_quem_e }}": idc.get("para_quem_e", ""),
        "{{ perfil_demografico_html }}": build_demografico_html(idc),
        "{{ comportamento_html }}": build_comportamento_html(idc),
        "{{ paliativos_section }}": pal_section,
        "{{ baldes_html }}": build_baldes_html(idc.get("baldes", [])),
        "{{ comunicador_nome }}": perfil.get("comunicador_nome", ""),
        "{{ comunicador_especialidade }}": perfil.get("comunicador_especialidade", ""),
        "{{ valores_pills }}": build_pills(perfil.get("valores", []), "badge-green"),
        "{{ tonalidade_emocional }}": perfil.get("tonalidade_emocional", ""),
        "{{ mantras_html }}": build_mantras_html(perfil.get("mantras", [])),
        "{{ tom_de_voz }}": perfil.get("tom_de_voz", ""),
        "{{ posicionamento }}": perfil.get("posicionamento", ""),
        "{{ formatos_html }}": build_bullet_list(perfil.get("formatos", [])),
        "{{ estilo_visual_pills }}": build_pills(perfil.get("estilo_visual", []), "badge-neutral"),
        "{{ referencias_html }}": build_referencias_html(perfil.get("referencias", [])),
        "{{ palavras_conectam_pills }}": build_pills(idc.get("palavras_conectam", []), "badge-green"),
        "{{ palavras_afastam_pills }}": build_pills(idc.get("palavras_afastam", []), "badge-pink"),
    }

    # pesquisa placeholders
    for key, value in pesq_html.items():
        replacements[f"{{{{ {key} }}}}"] = str(value)

    # copy da pagina (usa render centralizado do painel_template)
    replacements["{{ copy_pagina_html }}"] = _tmpl.render_copy_pagina_miolo(copy_dados)

    # quiz card (le quiz-meta.json gerado por /lt-quiz)
    replacements["{{ quiz_card }}"] = build_quiz_card(produto_path)

    # aplicar substituicoes
    html = template
    for placeholder, value in replacements.items():
        html = html.replace(placeholder, value)

    # salvar
    output = produto_path / "painel-entregas.html"
    output.write_text(html, encoding="utf-8")
    print(f"\nPainel gerado em: {output}")
    print(f"Tamanho: {len(html):,} bytes")
    print(f"\nPara visualizar:")
    print(f"file:///{output.as_posix()}")

if __name__ == "__main__":
    main()
