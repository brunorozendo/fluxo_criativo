# Workshop Inteligente. Assistente de Marketing IA

Toolkit completo de marketing digital, copy e infoprodutos baseado nas metodologias **VTSD (Venda Todo Santo Dia)**, **Light Copy**, **C10X (High Ticket)** e **Low Ticket**. Roda dentro do **Claude Code** (VS Code) ou no **Cursor**, transformando o chat em um consultor especialista que entrega materiais prontos para uso.

Não é software tradicional: é um sistema de prompts estruturados (CLAUDE.md, regras, comandos, agentes, skills e scripts) que orquestra o assistente do início ao fim de um funil.

## Por onde começar

| Arquivo | Para quê serve |
|---|---|
| `COMO-USAR.md` | Guia passo a passo para o usuário final. Inclui seção Cursor. |
| `CLAUDE.md` | Instruções e regras do assistente. Autoritativo, lido em toda conversa. |
| `AGENTS.md` | Mapa rápido para agentes de IDEs (Cursor, etc.) |
| `ARQUITETURA.md` | Visão técnica da arquitetura. Como inserir novas capacidades. |
| `scripts/README-creative.md` | Processo de geração de criativos via `generate-creative.py`. |
| `/configurar-heygen` | Setup de vídeo com avatar IA (slash command). |
| `/configurar-imagens` | Setup de geração de imagens para anúncios (slash command). |
| `/gerar-furadeira` | Gerar a Furadeira (método) do produto ativo no `perfil.md`. Decide automaticamente qual das 6 mecânicas (Fases, Lógica Condicional, Enquadramento, Listas, Empecilhos, Dinâmica de Entrega) cabe melhor no nicho. |
| `/furadeira-visual` | Gerar a imagem PNG da Furadeira já escrita no `perfil.md`. Monta um prompt em inglês para o aluno colar no ChatGPT, recebe a imagem de volta e salva no projeto + painel de entregas. |

## Onde roda

### Claude Code (VS Code)
Abra a pasta do projeto, instale a extensão Claude Code, use os slash commands `/copy-pagina`, `/lt-funil`, etc.

### Cursor
Abra a pasta com **File → Open Folder**. As regras em `.cursor/rules/` e o `CLAUDE.md` passam a orientar o chat. No Cursor, a barra `/` não é equivalente à do Claude Code. Para seguir um fluxo, diga no chat "segue o comando copy-pagina" ou anexe o arquivo `.claude/commands/copy-pagina.md` com `@`.

## Pré-requisitos

### Obrigatórios (o toolkit não funciona sem eles)

| Ferramenta | Como instalar | Para que serve |
|---|---|---|
| **Claude Code** | Extensão do VS Code (recomendado) ou `npm install -g @anthropic-ai/claude-code` | Runtime do assistente |
| **Python 3** | 3.10+ — o assistente guia a instalação se necessário | Scripts do painel, playbook e páginas |
| **Git** | [git-scm.com](https://git-scm.com) | Clonar e atualizar o repositório |

### Opcionais (instalados automaticamente pelo assistente quando necessário)

| Ferramenta | Ativa |
|---|---|
| **Vercel CLI** | `/pagina-vercel` (publicar páginas) |
| **FFmpeg** | `/video-editar` (corte, legenda, compressão) |
| **Remotion** | `/video-remotion` (vídeo animado para Ads) |

### APIs (todas opcionais — o toolkit funciona 100% sem nenhuma)

Copie `.env.example` para `.env` e preencha apenas o que for usar:

| Nível | O que preencher | O que desbloqueia |
|---|---|---|
| **Básico** | Nada | Todos os entregáveis em arquivo local |
| **Intermediário** | `VERCEL_TOKEN`, `FREEPIK_API_KEY` ou `OPENROUTER_API_KEY` | Páginas publicadas + criativos automáticos |
| **Avançado** | `HEYGEN_API_KEY`, `FB_ACCESS_TOKEN_PERMANENTE`, `TELEGRAM_BOT_TOKEN` | Vídeo com avatar IA + relatório diário de Ads automático |

Para configurar qualquer integração, use o comando correspondente no chat (`/configurar-heygen`, `/configurar-apify`, `/ads-relatorio`, etc.) — ele guia o processo completo.

## Metodologias base

- **VTSD (Venda Todo Santo Dia).** Quadro (transformação), Furadeira (método), Decorados (50 benefícios), 3 Identidades (Comunicador, Consumidor, Produto), Urgências Ocultas (7 categorias x 10 itens = 70 itens por produto), Mandala da Criatividade (18 tipos de anúncio x 4 objetivos x 3 momentos), Estrutura 8D (11 seções de página de vendas), VVV (vídeo de vendas), 26 Elementos Literários.
- **Light Copy.** Argumentativa, lógica, conversacional, não óbvia. Proibições duras: travessão, ponto de exclamação, pergunta no gancho, "Não é X. É Y.", "mesmo que", "sem precisar", nome do produto no lead.
- **C10X (High Ticket).** Retiros online, webinar, pitch de palco, call SPIN, WhatsApp, proposta comercial, follow-up pós-evento.
- **Low Ticket.** Produto de entrada (R$37-97) com quiz ou página direta, desafio, agente GPT, copy para Hotmart/Kiwify, otimização de Ads.

## Regras absolutas de estilo

1. **Nada de travessão (—)** em nenhum texto gerado. Sem exceção.
2. **Português do Brasil** em tudo que é visível ao usuário.
3. **Nunca mostrar código HTML no chat.** Salvar silenciosamente e informar o caminho.
4. **Sempre pedir aprovação antes de salvar.** Resumo + opções numeradas.
5. **Uma pergunta por vez** nas entrevistas, com progresso visual entre blocos.
6. **Produto não aparece no lead.** Sem "curso", "treinamento", nome do produto ou sigla no início da copy.

Checklists completos (Light Copy + Design HTML) estão no topo do `CLAUDE.md`.

## Arquitetura

4 tipos de componentes trabalham juntos:

| Componente | Local | Papel |
|---|---|---|
| **CLAUDE.md** | raiz | Persona, regras globais, fluxo padrão. Lido em toda conversa. |
| **Commands** | `.claude/commands/*.md` | Slash commands interativos (`/copy-pagina`, `/lt-funil`, etc.) |
| **Agents** | `.claude/agents/*.md` | Subprocessos autônomos (orquestradores e especialistas) |
| **Skills** | `.claude/skills/` | Base de conhecimento consultada por commands e agents |

**Fluxo típico:**
```
Usuário digita /comando
  → Command carrega .md correspondente
  → Lê meus-produtos/{ativo}/perfil.md e idconsumidor.md (contexto)
  → Consulta a skill relevante (conhecimento)
  → Roda entrevista (perguntas uma por vez)
  → Pede aprovação
  → Salva em meus-produtos/{ativo}/entregas/[tipo]/
  → Sugere próximo comando
```

## Estrutura de pastas

```
workshop_inteligente/
├── CLAUDE.md                    Regras e papel do assistente (autoritativo)
├── AGENTS.md                    Mapa para IDEs
├── ARQUITETURA.md               Guia técnico completo
├── COMO-USAR.md                 Guia passo a passo
├── README.md                    Este arquivo
│
├── .claude/                     Núcleo do assistente
│   ├── commands/                Slash commands (60+ arquivos .md)
│   ├── agents/                  Agentes orquestradores e especialistas
│   ├── skills/                  Base de conhecimento (vtsd-completo, paginas, anuncios, etc.)
│   └── settings.json            Permissões
│
├── .cursor/rules/               Regras específicas do Cursor (.mdc)
│
├── scripts/                     Utilitários Python e PowerShell
│   ├── README-creative.md           Processo de criação de criativos
│   ├── painel-incremental.py        Gera/atualiza painel-entregas.html por produto (seção a seção)
│   ├── painel_template.py           Shell HTML e renderers de cada seção do painel
│   ├── painel-atualizar.py          Regenera manifest meus-produtos/index.js
│   ├── montar-pagina-copias.py      Monta HTML final a partir das cópias de seção (/pagina-visual)
│   ├── playbook-montar.py           Monta HTML do playbook comercial
│   ├── playbook-briefing.py         Gera briefing do playbook a partir do perfil
│   ├── generate-avatar-video.py     Aciona HeyGen via API
│   ├── generate-creative.py         Geração de criativos visuais
│   ├── relatorio-ads.ps1            Rotina diária de relatório Facebook Ads
│   └── creative-templates/
│
├── meus-produtos/               Produtos do aluno (ignorado pelo git)
│   ├── .ativo                   Slug do produto ativo
│   ├── index.js                 Manifest gerado pelo painel-atualizar.py
│   └── {slug-do-produto}/
│       ├── perfil.md            Quadro, Furadeira, Decorados, Urgências
│       ├── idconsumidor.md      Identidade do consumidor
│       ├── pesquisa-mercado.md  Pesquisa de nicho
│       ├── tipo.md              Low/Middle/High ticket
│       ├── nome.txt             Nome amigável (opcional, override)
│       ├── painel-entregas.html Painel do produto (gerado por /produto-concepcao)
│       └── entregas/            Output do assistente (por produto)
│           ├── paginas/         HTML de vendas, captura, obrigado
│           │   └── copias/      Cópias de seção geradas por /pagina-visual
│           ├── copy-pagina/     Copy markdown por bloco
│           ├── anuncios/        Pacotes de anúncios
│           ├── conteudo-social/ Posts, carrosséis, Reels
│           ├── criativos/       Prompts de imagem e referências
│           ├── comercial/       Scripts de venda 1:1 (HTML)
│           ├── videos/          HeyGen, Remotion, roteiros
│           └── produto/         E-book, checklist, mini-curso final
│
├── docs/                        Área local de desenvolvimento (ignorada pelo git)
├── _prompts-gpt/                Material complementar do workshop
├── package.json
├── vercel.json
└── .env.example                 Modelo de chaves de API
```

Observação: a pasta `meus-produtos/` contém os dados de cada aluno e não sobe para o git. A `docs/` também é ignorada e serve para plans/rascunhos locais.

## Painel de entregas

Cada produto tem seu `painel-entregas.html` em `meus-produtos/{slug}/`. O painel é gerado e atualizado seção a seção pelo `painel-incremental.py` conforme o aluno avança nos commands. Inclui um seletor de produto no sidebar para navegar entre todos os produtos cadastrados.

- **Gerar/atualizar uma seção:** `py -3 scripts/painel-incremental.py --secao quadro`
- **Atualizar o manifest:** `py -3 scripts/painel-atualizar.py` (ou `/painel-atualizar` no chat)

## Comandos disponíveis

### Produto
`/produto-novo`, `/produto-concepcao`, `/produto-trocar`, `/produto-excluir`, `/produto-zerar`

### Copy
`/copy-pagina`, `/copy-anuncio`, `/copy-social`, `/copy-roteiro`, `/copy-variacao-post`, `/elementos-literarios`

### Imagem e vídeo
`/criativo-estatico`, `/criativo`, `/avat-whisk`, `/furadeira-visual`, `/video-heygen`, `/video-remotion`, `/video-editar`

### Low Ticket
`/lt-funil`, `/lt-criar-produto`, `/lt-quiz`, `/lt-pagina`, `/lt-otimizar`

### Estratégia
`/estrategia-funil`, `/estrategia-lancamento`

### Comercial
`/comercial-playbook`

### Infraestrutura de página (após gerar o HTML)
`/pagina-ajuste`, `/pagina-performance`, `/pagina-pixel`, `/pagina-checkout`, `/pagina-active`, `/pagina-precheckout`, `/pagina-lovable`, `/pagina-vercel`, `/pagina-visual`

### Feedback e auditoria
`/feedback-pagina`, `/feedback-low-ticket`

### Toolkit (projetos estruturados)
`/toolkit-novo`, `/toolkit-planejar`, `/toolkit-executar`, `/toolkit-verificar`, `/toolkit-progresso`, `/toolkit-anotar`, `/toolkit-pausar`, `/toolkit-retomar`

Fluxo proprietário para conduzir projetos grandes (lançamento, funil completo, reestruturação). Quebra o objetivo em etapas, aciona as skills certas uma a uma e mantém o estado em `meus-produtos/{ativo}/projeto/{slug}/` entre sessões. Não use para tarefa simples de uma skill só.

### Dados e automações
`/ads-relatorio`, `/enviar-relatorio-ads`, `/dados-instagram`, `/app-saas`, `/criar-gpt`, `/adaptar-plataforma`

### Dashboards de redes sociais
`/instagram-dashboard`, `/tiktok-dashboard`, `/youtube-dashboard`

Dashboards HTML com métricas de Instagram, TikTok e YouTube via Apify. O aluno roda o script de cada plataforma para atualizar os dados manualmente.

### Configuração de integrações
`/configurar-apify`, `/configurar-zapi`, `/configurar-heygen`, `/configurar-imagens`, `/gerar-token-permanente-facebook-ads`, `/obter-id-conta-anuncios`, `/criar-aplicativo-analise-ads`

A lista completa com descrições está no `CLAUDE.md`.

## Agentes especialistas

Orquestradores autônomos que executam tarefas completas acionando múltiplas skills:

- `estrategista-de-produto`. Sessão completa de concepção VTSD.
- `estrategista-low-ticket`. Funil low ticket do zero à página publicável.
- `estrategista-middle-ticket`. Funil perpétuo de produto principal.
- `construtor-de-paginas`. Páginas profissionais do zero.
- `clonador-de-bloco-visual`. Reproduz seções de página a partir de prints de referência (usado internamente por `/pagina-visual`).
- `criador-de-campanhas`. Campanha de tráfego completa.
- `consultor-comercial`. Playbook comercial 1:1.
- `copywriter`. Orquestrador de copy (página, anúncio, roteiro, social).
- `video-maker`. Orquestrador de produção de vídeo.
- `executor-de-plano-de-acao`. Executa plano de ação acionando skills e agentes.

Para tarefas complexas multi-etapas (lançamentos, funis inteiros, reestruturações), use os comandos `/toolkit-*` (fluxo proprietário do workshop com estado persistente).

## Skills (base de conhecimento)

Dentro de `.claude/skills/`:

- `vtsd-completo/`. Metodologia VTSD integral.
- `concepcao-produto/`. Quadro, Furadeira, 3 Identidades, Urgências Ocultas.
- `paginas/`. Estrutura 8D, design system, referências de blocos atômicos.
- `anuncios/`, `anuncios-texto/`, `anuncios-video/`. Mandala, formatos Meta Ads e Google Ads.
- `conteudo/`. Frameworks de copy, gatilhos, exemplos de VSL.
- `trafego-pago/`. Pixel, métricas, campanhas.
- `instagram-dashboard/`, `tiktok-dashboard/`, `youtube-dashboard/`. Dashboards de métricas por plataforma via Apify.
- `revisora/`. Checklist Light Copy e manual de copy aplicado a todo material gerado.
- `ferramentas/`. Integrações externas.

Skills não são acionadas pelo usuário: são consultadas pelos commands e agents quando precisam de conhecimento especializado.

## Scripts principais

### Painel de entregas
```
py -3 scripts/painel-incremental.py --secao quadro
py -3 scripts/painel-atualizar.py
```
O primeiro atualiza uma seção específica do `painel-entregas.html` do produto ativo. O segundo regenera o manifest `meus-produtos/index.js` (lista de produtos usada pelo seletor no painel).

### Páginas de vendas (fluxo visual)
```
py -3 scripts/montar-pagina-copias.py --slug {slug}
```
Monta o HTML final a partir das cópias de seção geradas por `/pagina-visual` em `meus-produtos/{slug}/entregas/paginas/copias/`.

### Playbook comercial
```
py -3 scripts/playbook-briefing.py --slug {slug}
py -3 scripts/playbook-montar.py --slug {slug}
```

### Geração de vídeo e imagens
- `scripts/generate-avatar-video.py`. HeyGen via API.
- `scripts/generate-creative.py` e `generate-openrouter-nano-banana-images.py`. Criativos via OpenRouter.

### Relatório diário de Ads
- `scripts/relatorio-ads.ps1`. Busca métricas do Facebook Ads e envia no WhatsApp via Z-API, agendado na nuvem do Claude.

## Integrações externas (opcionais)

Configuradas via `.env` (veja `.env.example`):

| Integração | Finalidade | Comando de setup |
|---|---|---|
| Facebook Marketing API | Relatório diário de Ads, otimização low ticket | `/gerar-token-permanente-facebook-ads`, `/criar-aplicativo-analise-ads` |
| Z-API | Envio de mensagens WhatsApp automatizadas | `/configurar-zapi` |
| Apify | Coleta de dados do Instagram, TikTok e YouTube | `/configurar-apify` |
| HeyGen | Vídeo com avatar IA | `/configurar-heygen` |
| OpenRouter | Geração de imagens via nano-banana | `/configurar-imagens` |
| Lovable / Vercel | Publicação de páginas | `/pagina-lovable`, `/pagina-vercel` |
| Hotmart, Kiwify, Eduzz, Cakto, Pepper, Stripe | Checkout das páginas | `/pagina-checkout` |
| ActiveCampaign | Lista de leads e automação de email | `/pagina-active` |

## Fluxos recomendados

### Começar a vender
1. `/produto-novo` ou `/produto-concepcao` (gera perfil + identidade do consumidor + painel)
2. `/copy-pagina`
3. `/copy-anuncio`

### Lançamento
1. `/produto-concepcao`
2. `/estrategia-lancamento`
3. `/copy-pagina` (evento + vendas)
4. `/copy-anuncio`
5. `/carrossel`

### Perpétuo
1. `/produto-concepcao`
2. `/estrategia-funil`
3. `/copy-pagina` (captura + vendas + obrigado)
4. `/copy-anuncio`

### Low Ticket
1. `/produto-concepcao`
2. `/lt-funil`
3. `/lt-criar-produto` (e-book, checklist, agente GPT)
4. `/lt-pagina` ou `/lt-quiz`
5. `/copy-anuncio` (formatos low ticket)
6. `/lt-otimizar` (com planilha do Gerenciador)

### High Ticket C10X
1. `/ht-big-idea`
2. `/ht-oferta`
3. `/ht-pagina-inscricao`
4. `/ht-comunicacao-pre`
5. `/ht-cronograma` e `/ht-conteudo`
6. `/ht-pitch-palco`
7. `/ht-spin`, `/ht-fechamento`, `/ht-objecoes`, `/ht-whatsapp`
8. `/ht-follow-up`

## Fluxo padrão de qualquer comando (6 passos)

1. **Contexto.** Ler `meus-produtos/.ativo`, depois `perfil.md` e `idconsumidor.md`.
2. **Entrevista.** 3 a 5 perguntas, uma por vez, com progresso visual.
3. **Confirmação.** Resumo do que vai criar, pedir OK numerado.
4. **Geração.** Criar o entregável aplicando a metodologia VTSD.
5. **Aprovação.** Mostrar o resultado e perguntar `1. Aprovar e salvar / 2. Ajustar`.
6. **Entrega.** Salvar, informar caminho, sugerir próximo comando.

## O que sobe para o git

**Sobe:** `.claude/commands/`, `.claude/agents/`, `.claude/skills/`, `.claude/settings.json`, `CLAUDE.md`, `AGENTS.md`, `ARQUITETURA.md`, `README.md`, `COMO-USAR.md`, `.env.example`, `scripts/`.

**Não sobe:** `.env`, `meus-produtos/` (dados do aluno), `docs/` (plans e rascunhos locais), `deploy-painel-workshop/`, `.claude/projects/` e demais arquivos de runtime.

## Adicionando novas capacidades

Para criar um novo command, agent, skill ou integração, siga o guia completo em `ARQUITETURA.md` (seções 5 a 8). Inclui frontmatter obrigatório, checklist e exemplo completo de como adicionar suporte a um novo domínio (ex: webinars).
