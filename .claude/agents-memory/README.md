# Memória dos Agentes

Pasta onde os agentes (em `.claude/agents/*.md`) armazenam memória persistente entre invocações.

## Como funciona

Cada agente é stateless por padrão no Claude Code: cada invocação começa do zero. Para dar continuidade entre sessões, os agentes deste projeto seguem uma convenção de memória em dois escopos:

| Escopo | Local | O que guarda |
|---|---|---|
| **Global** (por agente) | `.claude/agents-memory/{nome-agente}.md` | Preferências gerais do aluno, estilo, padrões de decisão que valem pra qualquer produto |
| **Por produto** (por agente × produto ativo) | `meus-produtos/{ativo}/agentes/{nome-agente}.md` | Contexto específico daquele produto, decisões tomadas, histórico de interações |

Ambas as pastas ficam **fora do git** (ignoradas pelo `.gitignore`). Cada aluno gera as suas memórias localmente conforme usa os agentes. O único arquivo versionado aqui é este `README.md` (e o `.gitkeep`).

## O que um agente faz

Todo agente (`.claude/agents/*.md`) tem um bloco de instrução padronizado que manda:

**No início da invocação:**
1. Ler `.claude/agents-memory/{seu-nome}.md` se existir (memória global).
2. Ler `meus-produtos/.ativo` pra saber o produto ativo.
3. Ler `meus-produtos/{ativo}/agentes/{seu-nome}.md` se existir (memória por produto).

**No final da invocação:**
1. Anexar aprendizados genéricos (estilo, preferências do aluno) em `.claude/agents-memory/{seu-nome}.md`.
2. Anexar aprendizados específicos do produto em `meus-produtos/{ativo}/agentes/{seu-nome}.md` (cria se não existir).

## Schema do arquivo de memória

Quando um agente cria a primeira memória, usa este template:

```markdown
# Memória do agente {nome}

> Auto-gerado pelo agente. Edite manualmente se quiser corrigir ou podar.

## Preferências observadas
- (o agente preenche conforme nota padrões do aluno)

## Padrões validados
- (decisões que funcionaram bem no passado e devem ser repetidas)

## Notas por sessão
- `2026-04-17`: descrição curta do que foi decidido ou aprendido.
```

## Regras de higiene

- **Nunca** gravar chaves de API, tokens, senhas ou dados sensíveis.
- Cada entrada em "Notas por sessão" tem data no formato `YYYY-MM-DD`.
- Máximo ~500 linhas por arquivo. Se passar, consolidar as entradas mais antigas num resumo.
- Se o aluno pedir explicitamente "ignore memória" ou "não use memória nesta tarefa", o agente não carrega nem atualiza.

## Limpar memórias

Pra zerar tudo, basta apagar os arquivos `.md` dentro desta pasta e dentro de `meus-produtos/*/agentes/`. A pasta e o README continuam de pé.
