---
name: workshop-marketing:criativo-estatico
description: Gerar criativo estatico de anuncio (imagem) em 3 passos AIDA. Comeca perguntando o modo (prompt para colar em ferramenta externa OU geracao automatica via API OpenRouter/Freepik). Os 3 passos sao sequenciais. cena (Atencao), layout e cores (Interesse e Desejo), texto da imagem (Acao). No modo prompt entrega prompt consolidado em ingles. No modo API gera as imagens diretamente.
allowed-tools: Read, Write, Bash, WebSearch
---

# Criativo Estatico. Anuncio em Imagem AIDA com Modo Prompt ou API

Gera criativo estatico de anuncio dividido em 3 passos AIDA. Antes de iniciar pergunta o modo: prompt para ferramenta externa ou geracao automatica via API. Cada passo e validado antes de avancar para o proximo.

**Por que 3 passos separados:**
A maioria dos criativos falha porque o texto e escrito antes do layout ser definido.
O texto nao cabe na composicao, o visual nao reforca a mensagem, o botao some no fundo.
Este fluxo inverte: primeiro a imagem que para o scroll, depois onde cada coisa fica, depois o texto que cabe naquele espaco.

## Usage

```
/criativo-estatico
```

## O Que Fazer

### 0. Contexto

Leia `meus-produtos/.ativo`, depois `meus-produtos/{ativo}/perfil.md` e
`meus-produtos/{ativo}/idconsumidor.md` (se existir).

Extraia:
- Quadro (transformacao principal)
- Nicho e publico
- Top 5 Urgencias Ocultas mais fortes (priorizando Dores, Desejos e Urgencias Quentes)
- Identidade do Consumidor (estetica, tom, cultura visual se disponivel)

### 1. Modo de Execucao (PRIMEIRA pergunta, antes de tudo)

```
Como voce quer gerar o criativo?

1. Prompt para colar em ferramenta externa (gratuito, sem API)
   Eu monto o prompt em ingles ja consolidado e voce cola no Midjourney,
   Gemini, ImageFX, Ideogram, Leonardo ou outra ferramenta da sua escolha.

2. Geracao automatica via API (OpenRouter ou Freepik)
   Eu gero as 3 variacoes ja salvas como PNG na sua pasta de entregas.
   Precisa ter OPENROUTER_API_KEY ou FREEPIK_API_KEY no .env.

Digite o numero:
```

**Se escolher 2:** verifique `.env` na ordem:
1. `OPENROUTER_API_KEY` existe e nao vazio. usar OpenRouter
2. `FREEPIK_API_KEY` existe e nao vazio. usar Freepik (fallback)
3. Nenhuma chave. orientar:

```
Para o modo API voce precisa configurar uma chave primeiro.
Recomendado: OpenRouter (custa menos de R$ 0,10 por imagem).

1. Configurar agora (uso o /configurar-imagens para guiar)
2. Voltar e usar o modo prompt
```

Se escolher 1 do submenu, oriente conforme `/configurar-imagens` e retome aqui apos a chave salva.

```
--- Modo definido ---
Execucao: [Prompt externo / OpenRouter / Freepik]
Proximo: Pesquisa de referencias virais (opcional)
---
```

### 2. Pesquisa de Referencias Virais (opcional, recomendado)

Pergunte:

```
Quer que eu pesquise referencias virais antes de criar?
Demora cerca de 60 segundos e melhora a qualidade visual.

1. Sim, pesquisar agora
2. Nao, pular e ir direto para a entrevista
```

**Se escolher 1**, anuncie e execute:

```
🔍 Próximo passo: pesquisar formatos virais de anúncio estático no nicho. Tempo estimado: cerca de 1 minuto.
```

Faca 2 buscas (WebSearch):
- `"Instagram static ad formats high converting [mes/ano atual]"`
- `"Instagram ad examples [nicho do produto] [ano atual]"`

Cruze com a referencia interna em `.claude/skills/anuncios/references/formatos-virais-instagram.md`.

Apresente:

```
✅ Concluído: pesquisa de virais.

Os formatos que mais estao convertendo no seu nicho:
1. [Formato A]. [por que funciona]
2. [Formato B]. [por que funciona]
3. [Formato C]. [por que funciona]

Vou usar essas referencias como inspiracao para a cena do Passo 1.
```

### 3. Entrevista (2 perguntas)

**Pergunta 1/2. Formato:**

```
Qual formato de imagem?

1. Feed retrato (4:5, 1080x1350). mais espaco na tela, melhor para feed
2. Quadrado (1:1, 1080x1080). classico, funciona em tudo
3. Stories ou Reels (9:16, 1080x1920). tela cheia vertical

Digite o numero:
```

**Pergunta 2/2. Urgencia base:**

Liste as top 5 urgencias ocultas do perfil numeradas, priorizando Dores, Urgencias Quentes e Desejos.

```
Qual situacao vai inspirar o criativo?
(escolha a que mais ressoa com o momento de compra)

1. [Urgencia 1 exata do perfil]
2. [Urgencia 2 exata do perfil]
3. [Urgencia 3 exata do perfil]
4. [Urgencia 4 exata do perfil]
5. [Urgencia 5 exata do perfil]

Digite o numero:
```

```
--- Entrevista concluida ---
Formato: [formato]
Urgencia: [urgencia escolhida]
CTA padrao: Saiba mais (para trocar, diga a qualquer momento)
Proximo: Passo 1 de 3 (imagem de fundo)
---
```

### 4. Passo 1 de 3: Imagem de Fundo (Atencao)

**Objetivo:** gerar a imagem de fundo que para o scroll.
Sem texto. Sem botao. Apenas o visual que cria impacto emocional imediato.

**Logica de construcao:**

A urgencia oculta escolhida mapeia para uma categoria visual:

| Categoria de urgencia | Direcao visual |
|---|---|
| Dor fisica ou emocional | Cena do instante em que o problema ainda persiste (nao apos a derrota aceita). Tensao presente que convida "como resolve?" nao resignacao que conclui "nao tem saida". Preferir objetos que contam a historia ou detalhe de costas/maos. Luz neutra ou quente. Luz fria + postura caida = derrota (estado fechado). |
| Desejo de resultado | Cena de conquista ou de resultado ja tangivel, luz quente, espaco aberto, postura confiante ou relaxada |
| Urgencia quente (evento proximo) | Cena de tempo passando ou decisao iminente, contraste claro/escuro, elemento que transmite prazo |
| Urgencia fria (acumulo de tempo) | Cena de padrao que se repete, peso de longa data sem resignacao. Transmite "mais uma vez aqui" nao "desisti de mudar". Tons neutros aceitos se a composicao transmite repeticao, nao fechamento. |
| Urgencia inusitada | Cena de contraste inesperado, elemento fora de lugar, composicao que gera curiosidade antes de qualquer texto |

**Regras do prompt de fundo:**
- Sempre em ingles
- Descrever composicao primeiro (o que esta em primeiro plano, angulo)
- Iluminacao especificada explicitamente
- Referencia de camera/lente para fotorrealismo (ex: "shot on Sony A7, 85mm")
- Mood emocional no final
- Sem rostos completos e visiveis (preferir costas, maos, objetos ou detalhe de corpo; silhueta com postura caida e luz fria gera visual de derrota. Usar silhueta apenas em cenas aspiracionais ou de movimento)
- Sujeito humano SEMPRE vestido de forma adequada para anuncios de midia social. Especificar a roupa no prompt (ex: "wearing a bikini", "in a dress", "in casual clothes"). Nunca omitir a vestimenta.
- Sem texto, logo ou watermark na cena
- Negative prompt separado quando a ferramenta suportar

**Estrutura interna do prompt (referencia para construcao):**

```
[Composicao: o que esta em cena e angulo], [sujeito sem rosto ou silhueta],
[acao ou estado], [ambiente e contexto], [iluminacao: tipo, direcao, temperatura],
[referencia de camera se fotorrealista], [paleta de cor dominante],
[mood emocional final]. --no text, faces, watermark, logo
```

**Derivar os ingredientes visuais do produto antes de criar as opcoes:**

Antes de escrever qualquer prompt, extraia do perfil do produto:
- Ambiente tipico do consumidor: onde ele esta quando sente essa urgencia? (quarto, cozinha, academia, escritorio, praia, vestiario, consultorio, carro?)
- Objeto do cotidiano diretamente ligado a urgencia: o que ele ve, toca ou evita nesse momento? (balanca, espelho, prato, calca que nao fecha, agenda lotada, carteira vazia, celular com notificacao?)
- Situacao concreta e especifica: nao "ela se sente mal" mas "ela esta olhando para a calca jeans dobrada na gaveta ha tres meses"
- Elemento do nicho que qualquer pessoa do publico reconhece de imediato

Esses 4 ingredientes sao a materia-prima das 3 opcoes. Nao gere opcoes sem eles.

**Gere 3 opcoes de imagem de fundo**, cada uma com uma tecnica de composicao diferente:

- Opcao A: close extremo em objeto do nicho. Sem pessoa ou apenas detalhe (maos, costas, silhueta de costas). O objeto conta a historia sozinho. A cena convida "como muda isso?" nao conclui "ja acabou". Luz neutra ou quente. Ex: a calca dobrada, a balanca, o prato intocado.
- Opcao B: cena de cotidiano exata. O consumidor no ambiente e momento especifico da urgencia, angulo de camera natural como se alguem fotografasse sem que a pessoa soubesse. Luz realista do ambiente. Ex: ela sentada na beira da cama olhando para o espelho, ele na mesa de trabalho as 22h.
- Opcao C: composicao de contraste ou surpresa. Elemento fora do lugar, angulo inesperado (de cima para baixo, de baixo para cima, close em detalhe minusculo), ou dois elementos opostos no mesmo quadro. Cria curiosidade antes de qualquer leitura de texto.

Apresente as 3 opcoes com apenas descricao em portugues. O prompt em ingles e derivado internamente apos a escolha e aparece somente no prompt consolidado final (ou no JSON de config se modo API).

```
Passo 1 de 3: imagem de fundo

Escolha a cena que vai parar o scroll:

Opcao A. [nome descritivo em portugues]:
[descricao visual em portugues, 2 a 3 frases. O que aparece, o angulo, a luz,
o mood. Como se voce estivesse descrevendo um quadro para alguem que nao pode ver.]

Opcao B. [nome descritivo em portugues]:
[descricao visual em portugues, 2 a 3 frases]

Opcao C. [nome descritivo em portugues]:
[descricao visual em portugues, 2 a 3 frases]

Cada opcao representa um momento especifico da urgencia escolhida. O kicker do Passo 3 deve capturar o momento da opcao escolhida, nao uma versao generica da urgencia.

---
1. Usar Opcao A
2. Usar Opcao B
3. Usar Opcao C
4. Quero ajustar uma das opcoes
```

Apos aprovacao, avance para o Passo 2.

### 5. Passo 2 de 3: Layout e Cores (Interesse e Desejo)

**Objetivo:** definir onde cada elemento vai ficar e como vai se parecer.
Esta etapa acontece ANTES de escrever o texto para que as palavras sejam escritas
dentro dos limites reais do espaco disponivel.

**Logica de construcao do layout:**

O layout cria uma hierarquia visual que guia o olho na sequencia:
1. Imagem de fundo capta a atencao (Passo 1)
2. Titulo gera interesse em menos de 2 segundos
3. Apoio cria desejo aprofundando o beneficio
4. Botao converte o desejo em acao

**Zonas padrao por formato:**

ATENCAO: o Meta Ads sobrepoe na base da imagem o nome do anunciante e o botao nativo
("Saiba mais"). Essa sobreposicao ocupa aproximadamente os ultimos 10-12% da imagem.
Todos os elementos do criativo (apoio, botao, instrucao de clique) devem estar
posicionados acima dessa zona, com folga de pelo menos 10% extra no rodape para
nao colidir com a UI nativa da plataforma.

Para feed retrato (4:5, 1080x1350):
- Zona A (imagem limpa, topo, 60-65%): cena fotografica sem texto, iluminada naturalmente
- Zona B (bloco de texto, base, 25-30%): kicker + headline + apoio + instrucao de clique
- Zona C (rodape, 10-12%): VAZIA, reservada para sobreposicao nativa do Meta

Zona B. Ordem dos elementos de cima para baixo dentro do bloco escuro:
  1. Kicker (linha pequena no topo do bloco)
  2. Headline (elemento dominante, fonte enorme, ocupa a maior parte visual da zona)
  3. Apoio linha 1 (dado concreto, abaixo do headline)
  4. Apoio linha 2 (complemento, opcional)
  5. Instrucao de clique (alinhada a esquerda, base do bloco)

Para quadrado (1:1, 1080x1080):
- Zona A (imagem limpa, topo, 60%): cena fotografica sem texto
- Zona B (bloco de texto, base, 28%): kicker + headline + apoio + instrucao
- Zona C (rodape, 12%): VAZIA

Para stories/reels (9:16, 1080x1920):
- Zona A (imagem limpa, topo, 55%): cena fotografica sem texto
- Zona B (bloco de texto, base, 31%): kicker + headline + apoio + instrucao
- Zona C (rodape, 14%): VAZIA (safe zone)

**Derivar cor de destaque pela categoria de urgencia (nao pelo nicho):**

A cor do headline deve ser brilhante e saturada. O fundo escuro natural faz o trabalho de contraste sem precisar de sombra.

| Categoria de urgencia | Cor de destaque do headline | Uso |
|---|---|---|
| Dor fisica ou emocional | Laranja-vermelho (#FF4500) ou Ambar (#FF8C00) | Tensao, urgencia, peso |
| Desejo de resultado | Verde eletrico (#00D400) ou Dourado (#FFD700) | Aspiracao, conquista, leveza |
| Urgencia quente (evento proximo) | Laranja eletrico (#FF6600) ou Vermelho (#FF2D55) | Prazo, decisao iminente |
| Urgencia fria (acumulo de tempo) | Teal brilhante (#00CED1) ou Branco puro (#FFFFFF) | Reflexao, padrao repetido |
| Urgencia inusitada | Roxo eletrico (#8B5CF6) ou Lima (#A3E635) | Curiosidade, contraste |

Kicker e apoio sempre em branco puro (#FFFFFF). So o headline recebe a cor de destaque.
A cor de destaque vai em TODO o texto do headline, nao apenas em uma palavra.

**Layout calculado internamente. Nao apresentar ao usuario como etapa separada.**

Com base no formato escolhido na Entrevista e na categoria de urgencia, determine silenciosamente:
- Cor de destaque do headline (tabela acima)
- Limites de caractere internos por zona (kicker: 50, headline: 30, apoio: 55 cada, instrucao: 55)

Mostre apenas uma linha de transicao apos o usuario escolher a cena, antes de gerar o texto:

```
Layout definido: [cor hex] ([nome da cor]). Gerando as versoes de texto.
```

Avance diretamente para o Passo 3 sem pedir aprovacao do layout.

### 6. Passo 3 de 3: Texto da Imagem (Acao)

**Objetivo:** escrever o texto exato de cada zona definida no Passo 2.
O texto e escrito para caber no espaco real, nao o contrario.

**Regras de texto interno (Light Copy aplicada a imagem):**

- Kicker: voz de monologo interno, nao narrador. O kicker e o pensamento que passa pela cabeca da pessoa naquele momento, nao uma marca descrevendo a situacao de fora. Teste: a pessoa poderia pensar isso com essas palavras exatas em conversa com uma amiga? Se nao, reescreva. Bom: "Mais um verao guardando o biquini no fundo da gaveta" (pensamento dela, primeira pessoa implicita). Ruim: "Esse biquini esperou tempo demais na gaveta" (narrador apontando de fora, tom de marca). Para qualquer nicho: bom = "Mais um mes olhando para a fatura sem saber por onde comecar". Ruim = "Suas dividas cresceram enquanto voce tentava economizar".
- Kicker: afirmacao curta. Sem exclamacao, sem pergunta.
- Kicker: fala sobre o estado atual do leitor, nao sobre o produto
- Kicker: tempo presente ou padrao recorrente ainda ativo. Nunca derrota passada ja encerrada. "Mais um mes no mesmo ponto" funciona (padrao que continua). "Mais uma tentativa que ficou para tras" nao funciona (ciclo encerrado, estado fechado).
- Kicker: deve capturar o MOMENTO ESPECIFICO da cena escolhida no Passo 1, nao uma versao generica da urgencia. O especifico cria identificacao imediata. O generico passa despercebido.
- Titulo: sem ponto de exclamacao, sem pergunta, sem travessao
- Titulo: dado concreto ou afirmacao direta (nunca promessa vaga)
- Headline: escrito em CAIXA ALTA (ALL CAPS). Fonte enorme exige brevidade. Max 30 chars.
- Headline: todo o texto na cor de destaque brilhante da categoria (ver Passo 2). Nao usar warm white. A cor vai em todo o headline, nao apenas em uma palavra.
- Kicker + Titulo: escrito como trava e chave. O kicker abre uma pergunta implicita ("por que nao funciona?", "quando isso muda?", "existe outro caminho?"). O titulo fecha exatamente essa pergunta com dado concreto. O titulo deve responder diretamente ao kicker, nao ser independente. Exemplo: Kicker "Mais um mes no mesmo ponto de partida" entao Titulo "[resultado concreto] em [prazo] acontece quando muda o metodo, nao o esforco". Exemplo: Kicker "Seis tentativas e o padrao continua igual" entao Titulo "[resultado concreto] para quem parou de repetir o mesmo caminho". Regra pratica: se voce cobrir o titulo e o kicker ainda fizer sentido sozinho, o par nao esta funcionando. Se o titulo pudesse existir sem o kicker, o par esta desconectado.
- Apoio linha 1: o dado concreto isolado (numero, prazo, resultado especifico)
- Apoio linha 2: o argumento ou complemento da linha 1 (o "como" ou "sem X"). PROIBIDO usar termos tecnicos ou nomes de categorias. Use o vocabulario que a pessoa usaria com uma amiga: nao "grupo alimentar" mas "doce, pao, arroz com feijao"; nao "sedentarismo" mas "sem sair do sofa ou da mesa de trabalho"; nao "gestao emocional" mas "sem explodir com todo mundo a toa"; nao "renda passiva" mas "dinheiro caindo na conta enquanto voce dorme". Dois ou tres exemplos concretos valem mais que um nome de categoria.
- Instrucao de clique: SEMPRE gerar o complemento completo. O CTA padrao e "Saiba mais". Se o usuario indicou outro em qualquer momento, usar esse. Nunca inventar CTA.
- Instrucao de clique: SEMPRE gerar o complemento completo, nunca deixar como placeholder. O complemento e uma frase de curiosidade ou desejo que conecta com o kicker ou o titulo. Comeca com "e" (conectivo suave). Usa verbo de descoberta: "veja", "descubra", "entenda", "confira". Nao menciona "curso", "treinamento", "compra". Pode ter 1 ou 2 linhas. Max 55 chars. Exemplos: "e veja com os seus proprios olhos o porque", "e descubra o que muda nas primeiras 2 semanas", "e entenda por que tantas pessoas estao conseguindo".
- Nenhuma zona pode ter texto que nao caiba no limite de caracteres do Passo 2

**Logica AIDA para o texto:**

- Passo 1 (visual) cumpriu ATENCAO
- Passo 2 (layout) define onde INTERESSE e DESEJO vao aparecer
- Passo 3 (texto): kicker cria identificacao, titulo entrega INTERESSE, apoio cria DESEJO, botao converte em ACAO

**Verificar antes de gerar as versoes:**
- O headline esta em CAIXA ALTA (ALL CAPS) e tem no maximo 30 chars? Se nao, converter e cortar.
- O headline usa a cor de destaque brilhante da categoria (nao warm white)? Se nao, corrigir.
- O kicker esta no presente ou em padrao recorrente ainda ativo? Se estiver no passado de derrota concluida, reescrever para tensao presente antes de continuar.
- O kicker captura o MOMENTO ESPECIFICO da cena escolhida no Passo 1 ou virou generico? Se virou generico, retornar ao momento especifico.
- O kicker abre uma pergunta implicita que o titulo responde? Se o titulo pudesse existir sem o kicker, o par esta desconectado.
- O tom emocional do kicker combina com o tom visual da cena? Cena de tensao presente + kicker de tensao presente = coerente. Cena neutra + kicker de derrota = incoerente.
- O kicker soa como pensamento humano ou como narrador/marca descrevendo de fora? Teste: a pessoa poderia pensar isso com essas palavras exatas? Se nao, reescrever na voz interna do leitor antes de continuar.
- O apoio usa termos tecnicos ou nomes de categorias (grupo alimentar, sedentarismo, gestao emocional, renda passiva)? Se sim, substituir por exemplos concretos do vocabulario cotidiano antes de continuar.

**Antes de mostrar as versoes:** aplicar a rotina de auto-revisao de copy obrigatoria do CLAUDE.md (carregar Manual da Copy + acionar revisora) e corrigir direto no texto. Nao mostrar versao bruta.

**Gere 2 versoes completas do anuncio**, cada uma com kicker, titulo, apoio (2 linhas) e botao ja combinados.
Nao apresentar opcoes separadas por zona. O usuario escolhe a versao inteira.

**INSTRUCAO DE CLIQUE. OBRIGATORIA EM AMBAS AS VERSOES:** Nunca deixar o complemento como placeholder. Gere uma frase concreta baseada no kicker ou no titulo da versao. O complemento comeca com "e" e usa verbo de descoberta ("veja", "descubra", "entenda", "confira"). Max 55 chars. Exemplos: "e veja o que muda nas primeiras semanas", "e descubra por que quem ja tentou antes consegue com este metodo", "e entenda o que faz a diferenca desta vez".

Apresente assim (sem contadores de caractere, que sao verificacao interna, nao output):

```
Versao 1:
"[kicker 1]"
[HEADLINE 1 EM CAIXA ALTA]
[apoio linha 1]
[apoio linha 2]
👆 Clique em "[CTA]" e [complemento]

Versao 2:
"[kicker 2]"
[HEADLINE 2 EM CAIXA ALTA]
[apoio linha 1]
[apoio linha 2]
👆 Clique em "[CTA]" e [complemento]

---
1. Versao 1
2. Versao 2
3. Quero ajustar algo
```

Apos o usuario escolher, montar a saida de acordo com o modo definido no Passo 1.

### 7. Saida Condicional

#### Modo Prompt (escolha 1 do Passo 1)

Monte o PROMPT FINAL CONSOLIDADO em ingles. Esse e o unico output que o aluno precisa para gerar o criativo.

REGRA CRITICA: usar linguagem visual espacial (upper area, lower band, centered),
NUNCA porcentagens numericas. Porcentagens sao apenas para calculo interno no Passo 2.
O modelo de imagem nao deve renderizar nenhuma anotacao de layout.

```
Generate a complete Instagram feed ad ([dimensoes]px).

SCENE: [descricao visual completa do Passo 1 em ingles,
com o sujeito vestido de forma adequada para anuncios de midia social.]
The upper area of the image must be a clean, well-lit photographic scene
with no text and no dark areas. The photograph should look natural and bright.
The lower band must fade into a very deep dark gradient
(near-black at the bottom, fade begins around two-thirds from the top).
IMPORTANT: leave a large empty margin at the very bottom of the image.
The bottom quarter must be completely free of any text, icon, or element.
The entire text block must sit in the upper half of the dark band,
well above the bottom edge of the image.

TEXT ON PHOTO (all text in the dark lower zone only, concentrated in the upper
portion of that zone. No text near the bottom edge):
- In the upper part of the dark lower zone: small regular white sans-serif
  text, no bold, clean, centered (dark background provides contrast,
  no shadow needed):
  "[kicker do Passo 3]"
- Immediately below the kicker: ENORMOUS ultra-bold black-weight all-caps
  sans-serif text (the dominant visual element, 3 to 5 times larger than
  the kicker), in bright saturated [cor hex destaque], centered,
  max 2 lines, no shadow needed:
  "[HEADLINE DO PASSO 3 EM MAIUSCULAS]"
- Below the headline: small regular white sans-serif text, clean, centered:
  "[apoio linha 1 do Passo 3]"
- Immediately below: slightly smaller regular white sans-serif text, centered:
  "[apoio linha 2 do Passo 3]"
- Below the support lines, still well above the bottom quarter safe zone,
  left-aligned: a small hand cursor tap icon followed by light gray (#BBBBBB)
  regular small sans-serif text: Clique em, then "[CTA]" in bold white,
  then in light gray: "[instrucao de clique do Passo 3]"

Style: professional Instagram ad, photorealistic clean scene in the upper zone,
bold dominant typography in the upper portion of the dark lower zone, generous
empty space at the very bottom. No text in the photographic area.
No background bands, no colored rectangles, no overlay boxes,
no percentage labels, no zone markers, no annotations.
```

Salve dois arquivos imediatamente apos o usuario escolher a versao de texto, sem pedir aprovacao adicional.

**Arquivo 1: JSON completo**
`meus-produtos/{ativo}/entregas/criativos/criativo-estatico-{slug}-{numero}.json`

**Arquivo 2: Briefing legivel**
`meus-produtos/{ativo}/entregas/criativos/criativo-estatico-{slug}-{numero}.md`

Conteudo do briefing:
- Nome do criativo, data, formato, urgencia base
- Cena escolhida (descricao em portugues)
- Layout em topicos (zonas, fontes, cores)
- Texto escolhido (kicker, headline, apoio, instrucao)
- Prompt final consolidado em ingles em bloco de codigo

Depois apresente:

```
Pronto. Cole esse prompt no seu gerador de imagem:

[PROMPT CONSOLIDADO EM INGLES]

Adaptar para sua ferramenta:
- Gemini / ImageFX: cole como esta, sem alteracao
- Midjourney: adicione ao final: --ar [ratio] --v 6.1 --style raw --s 250 --no text, faces, watermark
- Ideogram: adicione ao final: Style: Realistic, Aspect Ratio: [ratio]
- Leonardo.ai: cole o prompt principal; mova "--no text, faces, watermark, logo" para o campo Negative Prompt

Criativo salvo em meus-produtos/{ativo}/entregas/criativos/

Quer ajustar algum dos 3 passos?
1. Trocar a cena
2. Mudar a cor ou o layout
3. Reescrever o texto
```

#### Modo API (escolha 2 do Passo 1)

Anuncie:

```
🔍 Próximo passo: gerar 3 variacoes via [OpenRouter/Freepik]. Tempo estimado: cerca de 2 minutos.
```

Sistema hibrido em 3 camadas:
1. IA gera o visual de fundo (foto, textura) via OpenRouter ou Freepik
2. Template HTML compoe texto + layout + cores por cima
3. Chrome/Edge headless exporta PNG final

Crie um arquivo JSON de config em `meus-produtos/{ativo}/entregas/criativos/config-criativo-estatico-{slug}.json` com 3 slides (3 variacoes da versao escolhida no Passo 3, com leves ajustes de cena), todos no tema `theme-custom` com a cor de destaque definida no Passo 2.

REGRA ABSOLUTA: textos do JSON em portugues com acentos corretos (UTF-8). "não", "padrão", "você". Nunca "nao", "voce". Os prompts de IA (em ingles) nao precisam de acentos.

Estrutura do JSON:

```json
{
  "output_dir": "meus-produtos/{ativo}/entregas/criativos/",
  "colors": {"bg": "#0F0F0F", "text": "#FFFFFF", "accent": "[cor hex destaque]"},
  "slides": [
    {
      "theme": "theme-custom",
      "layout": "layout-gancho",
      "kicker": "[kicker em portugues]",
      "headline": "[HEADLINE EM CAIXA ALTA]",
      "apoio_1": "[apoio linha 1]",
      "apoio_2": "[apoio linha 2]",
      "cta": "[CTA] e [complemento]",
      "ai_prompt": "[prompt de cena em ingles, da Opcao escolhida no Passo 1]",
      "filename": "criativo-estatico-v1-{slug}"
    },
    { "...slide 2 com pequena variacao de cena..." },
    { "...slide 3 com pequena variacao de cena..." }
  ]
}
```

Rode o script:

```bash
py -3 scripts/generate-creative.py --config meus-produtos/{ativo}/entregas/criativos/config-criativo-estatico-{slug}.json
```

Router inteligente de modelos (definido em `scripts/openrouter_model_router.py`):

| Categoria | Modelo escolhido | Quando usar |
|---|---|---|
| photorealistic | Flux 2 Pro (`black-forest-labs/flux.2-pro`) | Fotos reais, retratos, produtos |
| complex_scene | GPT-5 Image Mini (`openai/gpt-5-image-mini`) | Composicoes complexas, mockups |
| infographic | GPT-5 Image Mini (`openai/gpt-5-image-mini`) | Infograficos, dashboards |
| clean_minimal | Gemini 3.1 Flash | Backgrounds, texturas, CTAs |
| abstract_mood | Gemini 3.1 Flash | Gradientes, vidro, 3D |
| artistic | Flux 2 Flex | Arte digital, colagens |

Se preferir forcar um modelo:

```bash
py -3 scripts/generate-creative.py \
  --config meus-produtos/{ativo}/entregas/criativos/config-criativo-estatico-{slug}.json \
  --force-model google/gemini-3.1-flash-image-preview
```

Para Freepik (caso `OPENROUTER_API_KEY` ausente e `FREEPIK_API_KEY` presente), o `generate-creative.py` chama a API do Freepik internamente.

Apos a execucao do script:

```
✅ Concluído: 3 variacoes geradas.

Imagens salvas em:
- meus-produtos/{ativo}/entregas/criativos/criativo-estatico-v1-{slug}.png
- meus-produtos/{ativo}/entregas/criativos/criativo-estatico-v2-{slug}.png
- meus-produtos/{ativo}/entregas/criativos/criativo-estatico-v3-{slug}.png

Briefing tecnico salvo em:
- meus-produtos/{ativo}/entregas/criativos/criativo-estatico-{slug}.md

Proximo passo: use /copy-anuncio para criar a copy (texto) dos anuncios que vao acompanhar essas imagens.

Quer ajustar algum dos 3 passos?
1. Trocar a cena
2. Mudar a cor ou o layout
3. Reescrever o texto
```

### 8. Modo Iterativo

Se o usuario quiser refinar um passo especifico depois de salvar:

```
Qual passo quer ajustar?

1. Passo 1: imagem de fundo (trocar a cena)
2. Passo 2: layout e cores (ajustar zonas, fontes ou paleta)
3. Passo 3: texto da imagem (kicker, headline, apoio ou botao)

O que quer mudar?
```

Ajuste apenas o passo solicitado, atualize os arquivos mantendo os outros passos intactos. No modo API, regere apenas a imagem afetada.

## Regras

- Nao escrever texto antes do Passo 2 estar definido. O texto do Passo 3 depende dos limites de caractere definidos no layout.
- Nunca inventar urgencia. A urgencia base vem obrigatoriamente das Urgencias Ocultas do perfil.
- Prompt do Passo 1 sempre em ingles, adaptado ao formato nativo da ferramenta escolhida.
- Light Copy obrigatoria no Passo 3: sem travessao, sem ponto de exclamacao, sem pergunta, sem promessa vaga.
- Auto-revisao obrigatoria de copy (Manual + revisora) antes de mostrar as versoes ao usuario.
- O numero do criativo e sequencial dentro da pasta do produto. Verificar arquivos existentes antes de numerar.
- No Passo 1, mostrar apenas descricoes em portugues para as 3 opcoes. O prompt em ingles da cena escolhida e derivado internamente e incluido somente no prompt consolidado final (ou no JSON de config se modo API).
- Passo 3 gera SEMPRE 2 versoes completas (kicker+headline+apoio+botao juntos), nunca opcoes isoladas por zona.
- Prompt final consolidado usa linguagem visual espacial (upper area, lower band, centered). NUNCA incluir porcentagens numericas. Porcentagens sao apenas para calculo interno do limite de caracteres no Passo 2.
- Sujeito humano no prompt do Passo 1 deve estar vestido de forma adequada para anuncios. Especificar a roupa explicitamente no prompt. Nunca omitir a vestimenta.
- CTA: o padrao e "Saiba mais". Se o usuario indicou outro em qualquer momento, usar esse. Nunca inventar.
- Headline: sempre em CAIXA ALTA (ALL CAPS), max 30 chars, todo na cor de destaque brilhante da categoria. Nunca warm white. Nunca destacar so uma palavra.
- Texto no Passo 3: sem sombra. O fundo escuro natural e a cor saturada do headline garantem contraste.
- Kicker: tensao presente ou padrao recorrente ainda ativo. Nunca derrota passada concluida. Voz de monologo interno do leitor, nao narrador. Captura o MOMENTO ESPECIFICO da cena do Passo 1.
- Apoio sem jargao tecnico: nunca usar nomes de categorias (grupo alimentar, sedentarismo, gestao emocional, renda passiva). Usar palavras especificas que a pessoa usa no dia a dia.
- Cenas de dor: preferir objetos, maos ou detalhe de costas. Silhueta com postura caida e luz fria gera imagem de derrota (estado fechado).
- Opcoes do Passo 1: cada cena deve usar pelo menos um elemento visual concreto do nicho. Proibido cenas genericas que poderiam servir para qualquer produto.
- Opcoes do Passo 1: as 3 opcoes devem diferir em tecnica de composicao, nao apenas em "tom emocional".
- Modo API: textos do JSON em portugues com acentos UTF-8 corretos. Prompts de IA em ingles.
