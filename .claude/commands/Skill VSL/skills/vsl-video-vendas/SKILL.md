---
name: vsl-video-vendas
description: Cria roteiros completos de VSL (Carta de Vendas em Vídeo) usando a megaestrutura de 12 blocos com calibração por produto e público. Use quando o usuário pedir VSL, vídeo de vendas longo, carta de vendas em vídeo, roteiro completo para página de vendas em vídeo, ou script VSL.
---

# VSL — Vídeo de Vendas (Megaestrutura 12 Blocos)

Cria roteiros completos de VSL prontos para narração em áudio/vídeo, seguindo a megaestrutura de 12 blocos com calibração automática baseada no produto e no perfil do público.

**Target:** 1.200 palavras | Hard cap: 1.500 palavras | Tom: fala natural, frases curtas, pausas com "..."

## Pré-requisito

Antes de iniciar, leia:
- `meus-produtos/.ativo` — produto ativo
- `meus-produtos/{ativo}/perfil.md` — Quadro, Furadeira, Decorados, oferta, provas
- `meus-produtos/{ativo}/idconsumidor.md` — dores, objeções, linguagem do público

Se algum arquivo não existir, oriente a criar com `/meu-produto` ou `/idconsumidor`.

---

## Etapa 1 — Calibração (UMA pergunta por vez)

Após ler o contexto do produto, conduza a calibração. Cada pergunta deve aparecer sozinha, numerada, com exemplos.

### Bloco 1/4 — Produto e Oferta

```
Qual o ticket do produto?

1. Baixo — até R$ 297
2. Médio — R$ 297 a R$ 997
3. Alto — R$ 997 a R$ 2.997
4. Premium — acima de R$ 2.997

Digite o número:
```

```
O produto tem bônus para mencionar na oferta?
(ex: "Sim, tenho planilha X e acesso ao grupo" / "Não")
```

```
Tem garantia? Se sim, quantos dias?
(ex: "7 dias incondicional" / "30 dias" / "Não tenho")
```

```
--- Bloco 1/4 concluído ---
Ticket: [resposta]
Bônus: [resposta]
Garantia: [resposta]
Próximo: Público e Provas
---
```

### Bloco 2/4 — Público e Provas

```
Quantas provas, depoimentos ou casos de resultado você tem?

1. Nenhum — produto novo, sem resultados ainda
2. Poucos — 1 a 3 cases ou depoimentos
3. Alguns — 4 a 10 cases ou depoimentos
4. Muitos — mais de 10 cases ou depoimentos
```

```
O público já conhece esse tipo de solução?

1. Não conhece — nunca ouviu falar do assunto
2. Conhece o problema — sabe que tem o problema, mas não a solução
3. Conhece a solução — já tentou alternativas que não funcionaram
4. Conhece concorrentes — já comprou algo parecido antes
```

```
--- Bloco 2/4 concluído ---
Volume de provas: [resposta]
Nível de consciência: [resposta]
Próximo: História e Diferencial
---
```

### Bloco 3/4 — História e Diferencial

```
Você tem uma história pessoal de transformação ligada ao produto?

1. Sim, história forte — crise real, virada, resultado comprovado
2. Sim, história moderada — contexto e aprendizado, sem drama
3. Não — sem história pessoal, mas tenho casos de clientes
4. Não — sem história nem casos, produto recém-criado
```

```
Qual a objeção principal do seu público?

1. "Isso não funciona" — ceticismo sobre o resultado
2. "Não confio no expert" — falta de autoridade percebida
3. "Não é prioridade agora" — momento de vida ou urgência baixa
4. "Não tenho dinheiro" — objeção de preço
```

```
--- Bloco 3/4 concluído ---
História: [resposta]
Objeção dominante: [resposta]
Próximo: Tom e Formato
---
```

### Bloco 4/4 — Tom e Formato

```
Qual o tom da VSL?

1. Direto — vai ao ponto rápido, menos storytelling
2. Narrativo — história central, emoção, identificação
3. Educativo — ensina algo valioso antes de vender
4. Emocional — apelo forte à identidade e transformação de vida
```

```
Onde a VSL será usada?

1. Página de vendas — vídeo principal da PV
2. Meta Ads — anúncio em vídeo longo
3. YouTube Ads — pre-roll ou vídeo de conteúdo com oferta
4. Lançamento — vídeo de abertura ou CPL
```

**Confirmação antes de gerar:**

```
Resumo da VSL que vou criar:

Produto: [nome do produto]
Quadro: [transformação principal]
Ticket: [faixa de preço]
Provas: [quantidade]
História: [tem/não tem]
Objeção dominante: [tipo]
Tom: [tom escolhido]
Destino: [onde será usada]

1. Tudo certo, pode gerar
2. Quero ajustar algo
```

---

## Etapa 2 — Calibração Interna (não mostrar ao usuário)

Com base nas respostas, defina internamente:

**Hook Type:**
- Público nível 1-2 → `pain` (dor visceral) ou `violation` (crença quebrada)
- Público nível 3-4 → `result_first` (resultado concreto) ou `demo` (demonstração)

**Proof Mode:**
- Sem provas → `logic_only` (zero depoimentos — apenas lógica e analogia)
- 1-3 provas → `hybrid` (combinar depoimentos com lógica)
- 4+ provas → `social_proof` (depoimentos distribuídos)

**Budget por bloco (total = 1.200 palavras):**

| Ticket | Hook | Oferta/Close |
|--------|------|--------------|
| Baixo | 80-100 | 300-350 |
| Médio | 100-120 | 350-400 |
| Alto | 120-150 | 400-500 |

Ajustes automáticos:
- Sem história → reduzir bloco 4 para 60 palavras; compensar em blocos 5 e 7
- Sem provas → bloco 7 usa prova lógica/analógica; aumentar bloco 5
- Objeção é preço → ampliar bloco 10 (ancoragem) e bloco 8 (custo da inércia)

---

## Etapa 3 — Geração dos 12 Blocos

Gere o roteiro completo como texto contínuo, como se fosse fala. Para detalhes de cada bloco, consulte [references/blocos-vsl.md](references/blocos-vsl.md).

**Estrutura obrigatória (ordem fixa):**

1. **Hook + Prova Imediata** — quebrar inércia, violar crença ou provar resultado. Nunca começar com "Oi, tudo bem?" ou apresentação.
2. **O Que Não É** — limpar associações negativas: "Isso aqui não é [X], não é [Y], não é [Z]."
3. **Roadmap** — "Nos próximos minutos vou te mostrar 3 coisas: [X], [Y] e [Z]."
4. **História de Origem** — jornada do expert ou caso de cliente. Se sem história, usar Mecanismo como âncora narrativa.
5. **Mecanismo Único** — nome próprio obrigatório. Causa raiz + por que as alternativas falham.
6. **Destruição de Alternativas** — fechar saídas: "Você já deve ter tentado [X] e [Y]... e não funcionou."
7. **Prova Social** — depoimentos reais OU prova lógica/estatística (conforme proof_mode).
8. **Amplificação de Desejo** — visualização positiva + custo da inércia.
9. **Stack da Oferta** — cada entrega conectada a uma dor/desejo do avatar.
10. **Ancoragem de Preço** — 3 camadas: somar valor total, comparar com alternativas, comparar com cotidiano. Revelar preço.
11. **Bônus Pós-Preço** — empilhar valor após o preço: "E eu ainda não terminei..."
12. **Fechamento** — bifurcação de 2 caminhos, garantia, CTA repetido 2-3x, fechamento emocional.

**Regras de escrita (APLICAR EM TODOS OS BLOCOS):**
- Fala natural: frases de 10-20 palavras, pausas com "..."
- Sem bullets, caps, emojis dentro da copy
- Transições suaves entre blocos
- Nomear o mecanismo com nome próprio (ex: "Método da Inversão", "Sistema 3F")

---

## Etapa 4 — Checklist Light Copy (varredura obrigatória antes de entregar)

Antes de mostrar o resultado, verifique e corrija:

- [ ] Nenhum travessão (—) — reescreva a frase sem ele
- [ ] Nenhum ponto de exclamação — substitua por ponto final ou reescreva
- [ ] Nenhuma pergunta no gancho — sempre afirmação ou premissa
- [ ] Nenhuma estrutura "Não é X. É Y." — desenvolva de outra forma
- [ ] Nenhum "mesmo que" ou "sem precisar" como muleta
- [ ] Nenhuma promessa vaga — substituir por dado ou situação concreta
- [ ] Mecanismo tem nome próprio no bloco 5
- [ ] CTA aparece pelo menos 2 vezes no bloco 12
- [ ] Garantia mencionada no bloco 12
- [ ] Total entre 900 e 1.500 palavras

---

## Etapa 5 — Aprovação e Entrega

**Mostrar o script completo** e perguntar:

```
1. Aprovar e salvar
2. Quero ajustar algo
```

Se aprovado, salvar em:
`meus-produtos/{ativo}/entregas/textos-de-venda/vsl-[produto].md`

Após salvar:
```
VSL salva em meus-produtos/{ativo}/entregas/textos-de-venda/vsl-[produto].md

Próximos passos sugeridos:
- /roteiro-de-video → adaptar para Reels 60s (versão curta desta VSL)
- /copy-anuncio → criar anúncios derivados do hook desta VSL
- /copy-pagina → criar página HTML com este script como VSL embutida
```

---

## Referências

- Detalhes dos 12 blocos: [references/blocos-vsl.md](references/blocos-vsl.md)
- Questionário completo de calibração (21 perguntas): [references/calibracao-vsl.md](references/calibracao-vsl.md)
