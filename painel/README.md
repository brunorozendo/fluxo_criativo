# Painel do Aluno

Espelho visual do que o Claude Code está executando no seu projeto. Cada um dos 7 agentes do painel representa uma área do trabalho VTSD (PROD, COPY, PAG, AD, VID, SALES, DATA) e reage em tempo real conforme o Claude trabalha.

## Como usar

1. Abra `painel/index.html` no navegador (duplo clique ou via servidor estático).
2. No terminal, em outra aba, rode comandos do Workshop normalmente: `/produto-novo`, `/copy-pagina`, `/pagina-visual`, `/copy-anuncio`, etc.
3. O painel reage em tempo real: o boneco da categoria correspondente caminha até a estação certa, a sala acende e a bolha mostra o "Próximo passo".

## Como funciona

- O hook do projeto (`.claude/hooks/agent-status-writer.js`) escreve em `.claude/agents-memory/agents-status.js` toda vez que um agente do Workshop entra em ação.
- A Sala dos Agentes (`workshop-live-office.html`, embutida via iframe no painel) faz polling desse arquivo a cada 1,5s.
- Cada poll é diferenciado contra o estado anterior, e o painel dispara apenas as animações necessárias (`idle → trabalhando`, troca de skill, conclusão com `✅`).
- Não há lógica autônoma: se o hook não escreve, o painel não inventa. Os agentes ficam parados em modo idle dentro de suas próprias salas.

## Mapeamento de comandos

Cada `/comando` ou skill conhecida leva o agente para uma estação específica dentro da sala dele. Exemplos:

- `/produto-novo`, `/produto-concepcao` → mesa de reunião da PROD
- `/gerar-furadeira`, `/furadeira-visual` → quadro kanban da PROD
- `/copy-pagina`, `/copy-anuncio` → escrivaninha com luminária da COPY
- `/elementos-literarios`, `WebSearch`, `WebFetch` → estante de livros da COPY
- `/pagina-visual`, `/pagina-ajuste` → arco de monitores da PAG
- `/pagina-performance`, `/feedback-pagina` → mesa digitalizadora da PAG
- `/copy-anuncio` (no AD) → mural de pôsteres
- `/criativo-estatico`, `/avat-whisk`, `/banner-visual` → tripé de câmera
- `/video-heygen`, `/video-remotion` → ilha de edição da VID
- `/video-editar`, `/video-efeitos` → microfone da VID
- `/comercial-playbook` → mesa redonda da SALES
- `/lt-funil`, `/lt-quiz`, `/lt-pagina`, `/lt-criar-produto` → gráfico de barras da SALES
- `/ads-relatorio`, `instagram-dashboard`, `tiktok-dashboard`, `youtube-dashboard` → rack de servidores da DATA
- `/dados-instagram`, `/lt-otimizar`, `/pesquisa-mercado` → mesa em L da DATA

Comandos não mapeados explicitamente caem em uma estação padrão (`_default`) da sala correspondente. A lista completa fica em `COMMAND_SPOTS`, dentro de `workshop-live-office.html`.

## Estado inicial

Todos os agentes começam parados, em modo idle, em suas salas. É o estado correto antes de qualquer comando. O log de atividade mostra `aguardando atividade…` e o cabeçalho marca `claude inativo`.

## Resetar

Para zerar o painel (todos em idle, log vazio):

```
cp .claude/agents-memory/agents-status.template.js \
   .claude/agents-memory/agents-status.js
```

Em seguida, recarregue a página do navegador.

## Indicadores do cabeçalho

- **claude inativo** (cinza): nenhuma atualização nos últimos 20 segundos. Não significa erro: o Claude pode só estar pensando ou aguardando o próximo comando.
- **claude ativo** (verde, por 3 segundos): atividade acabou de retomar. Depois desse período o painel mostra apenas a hora do último evento.

## Estrutura de arquivos

```
painel/
  index.html                     ← shell que monta a navegação e carrega o painel do produto ativo
  sala-assets/
    bonecos/{prod,copy,...}.png  ← sprite sheets dos 7 agentes (4 direções de caminhar)
workshop-live-office.html        ← Sala dos Agentes (mapa, móveis, polling, diff handler)
.claude/agents-memory/
  agents-status.js               ← arquivo lido pelo painel (escrito pelo hook)
  agents-status.template.js      ← template para resetar
```
