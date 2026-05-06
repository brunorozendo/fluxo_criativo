---
name: workshop-marketing:ads-relatorio
description: Configura as credenciais e preferências do relatório de Facebook Ads (canal, métricas, filtro de campanhas) e oferece envio imediato via /enviar-relatorio-ads. Telegram ou WhatsApp. Suporta modo CLI (recomendado, Python) e modo Manual (PowerShell legado).
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, AskUserQuestion
model: sonnet
---

# Configurar Relatorio de Ads

Configura o canal de envio, as credenciais e as preferencias do relatorio de Facebook Ads. Ao final, voce pode enviar um relatorio imediatamente.

O mentoreado nunca abre arquivo, nunca instala nada manualmente. So cola as chaves no chat e segue as instrucoes.

## COMO FUNCIONA

1. Claude detecta ou pergunta o modo de integracao (CLI ou Manual)
2. Claude guia a instalacao e configuracao de credenciais
3. Claude registra as preferencias de metricas e filtro de campanhas
4. Ao final, voce pode enviar um relatorio imediatamente com `/enviar-relatorio-ads`

---

## PASSO 0. Selecionar Modo de Integracao

Leia `.env`. Se `RELATORIO_AUTH_MODO` ja existir com valor `CLI` ou `MANUAL`:
- `CLI` → pule para o **Passo 0-CLI**
- `MANUAL` → pule para o **Passo 0-CANAL**

Se nao existir, exiba:

```
Como voce prefere integrar com o Facebook Ads?

1. Meta Ads CLI (recomendado)
   Python 3.12+, funciona no Windows, Mac e Linux.
   Comandos simples, sem construir URLs de API na mao.

2. API manual via PowerShell (metodo anterior)
   Nao precisa de Python. So funciona no Windows.
   Bom se voce ja esta no Windows e nao quer instalar mais nada.

Digite o numero:
```

**Se escolher opcao 1 (CLI):** salve `RELATORIO_AUTH_MODO=CLI` no `.env` e siga para o **Passo 0-CLI**.

**Se escolher opcao 2 (Manual):** salve `RELATORIO_AUTH_MODO=MANUAL` no `.env` e pule para o **Passo 0-CANAL**.

---

## PASSO 0-CLI. Configurar o Meta Ads CLI

### CLI-1. Verificar Python

Execute:

```bash
python --version 2>&1 || python3 --version 2>&1
```

- Se retornar `Python 3.12` ou superior: continue.
- Se retornar versao inferior a 3.12 ou nao encontrado: exiba a mensagem abaixo e pare ate o usuario resolver.

```
O Meta Ads CLI exige Python 3.12 ou superior.

Versao detectada: [versao encontrada ou "nao encontrado"]

Para instalar:
- Windows: acesse https://python.org/downloads e baixe a versao mais recente
- Mac: brew install python@3.12
- Linux: sudo apt install python3.12

Apos instalar, rode o comando "/ads-relatorio" novamente.
```

### CLI-2. Instalar o meta-ads

Use Bash para verificar se ja esta instalado:

```bash
meta --version 2>&1 || python -m meta --version 2>&1 || python3 -m meta --version 2>&1
```

Se ja estiver instalado, informe "Meta Ads CLI ja instalado." e avance.

Se nao estiver instalado, informe "Instalando o Meta Ads CLI..." e use Bash para instalar:

```bash
pip install meta-ads
```

Se `pip` retornar erro, use Bash para tentar:

```bash
pip3 install meta-ads
```

Apos instalar, use Bash para confirmar:

```bash
meta --help 2>&1 | head -5
```

Se retornar a ajuda do CLI, informe "Meta Ads CLI instalado com sucesso." e avance.
Se retornar erro mesmo apos instalar, informe o erro exato ao usuario e pare.

### CLI-3. Verificar ou Configurar Credenciais do Facebook Ads

Leia `.env`. Verifique se alguma dessas variaveis ja existe com valor preenchido:
- `ACCESS_TOKEN`
- `FB_ACCESS_TOKEN_PERMANENTE`
- `FB_ACCESS_TOKEN_TEMPORARIO`

E tambem:
- `AD_ACCOUNT_ID`
- `FB_AD_ACCOUNT_ID`

**Se ja tiver credenciais (qualquer combinacao acima):**

Informe:

```
Encontrei credenciais existentes do Facebook Ads.

Vou configurar os nomes de variavel que o CLI usa (ACCESS_TOKEN e AD_ACCOUNT_ID)
aproveitando os valores que voce ja tem. Nenhum token novo precisa ser gerado.
```

Use `Edit` para adicionar (sem sobrescrever os existentes):
- Se tem `FB_ACCESS_TOKEN_PERMANENTE`: adicione `ACCESS_TOKEN=[mesmo valor]`
- Se tem apenas `FB_ACCESS_TOKEN_TEMPORARIO`: adicione `ACCESS_TOKEN=[mesmo valor]`
- Se tem `FB_AD_ACCOUNT_ID`: adicione `AD_ACCOUNT_ID=[mesmo valor]`

Se `ACCESS_TOKEN` ou `AD_ACCOUNT_ID` ja existirem no `.env`, nao sobrescreva.

**Se NAO tiver nenhuma credencial do Facebook Ads:**

Exiba:

```
Para conectar ao Facebook Ads, precisamos do token de acesso e do ID da conta.

Voce ja criou o App no Facebook Developers (developers.facebook.com)?

1. Sim, ja tenho o App criado
2. Nao tenho ainda
```

- **Opcao 1 (ja tem o App):** execute a skill `gerar-token-permanente-facebook-ads`. Ela cria o Usuario do Sistema, atribui a conta de anuncios e gera o token permanente. Apos concluir, retorne aqui e salve tambem `ACCESS_TOKEN=[valor do token gerado]` e `AD_ACCOUNT_ID=[valor do FB_AD_ACCOUNT_ID]` no `.env`.

- **Opcao 2 (nao tem o App):** execute a skill `criar-aplicativo-analise-ads` e depois `gerar-token-permanente-facebook-ads`. Apos concluir, retorne aqui e salve `ACCESS_TOKEN` e `AD_ACCOUNT_ID` como descrito acima.

### CLI-4. Testar a conexao

Execute o teste de conexao com o CLI:

```bash
meta ads insights get --date-preset yesterday --fields spend --format json --no-input
```

- Se retornar JSON com `"data"`: conexao validada. Informe "Conexao com o Facebook Ads confirmada."
- Se retornar erro de autenticacao (codigo 3 ou mensagem de token invalido): o token nao tem permissoes suficientes. Execute novamente a skill `gerar-token-permanente-facebook-ads` e certifique-se de selecionar todas as permissoes.
- Se o comando `meta` nao for reconhecido: verifique se o Python esta no PATH e tente `python -m meta.ads insights get ...`

Continue para o **Passo 0-CANAL**.

---

## PASSO 0-CANAL. Verificar Canal de Envio

Leia `.env`. Se `RELATORIO_CANAL` ja existir com valor `TELEGRAM` ou `WHATSAPP`, pule para o **Passo 0.5**.

Se nao existir, exiba:

```
Por qual canal quer receber o relatorio?

1. Telegram (Recomendado)
2. WhatsApp

Digite o numero:
```

Se o usuario perguntar por que Telegram e recomendado, explique: "O Telegram e gratuito e nao tem risco de bloqueio. Automacoes de mensagem no WhatsApp podem levar ao banimento do numero."

**Se escolher Telegram (opcao 1):**
- Salve `RELATORIO_CANAL=TELEGRAM` no `.env` com `Edit`

**Se escolher WhatsApp (opcao 2):**
- Salve `RELATORIO_CANAL=WHATSAPP` no `.env` com `Edit`
- Exiba o aviso abaixo antes de continuar:

```
Aviso importante sobre WhatsApp:

Automacoes de mensagem tem risco de banimento do numero.
Use um numero secundario aquecido, nunca o numero principal da sua operacao.
```

---

## PASSO 0.5. Verificar Chaves de Canal Existentes

Leia `.env`.

**Se `RELATORIO_CANAL=TELEGRAM`:** verifique `TELEGRAM_BOT_TOKEN` e `TELEGRAM_CHAT_ID`.

**Se `RELATORIO_CANAL=WHATSAPP`:** verifique `ZAPI_INSTANCE_ID`, `ZAPI_TOKEN`, `ZAPI_CLIENT_TOKEN`, `RELATORIO_WHATSAPP_NUMERO`.

Se todas as chaves do canal estiverem presentes, pule para o **Passo 2**.

---

## PASSO 1. Coletar Credenciais do Canal de Envio

### 1.1 Facebook Ads (apenas MODO MANUAL)

Esta secao so se aplica se `RELATORIO_AUTH_MODO=MANUAL`.

Se o modo for CLI, as credenciais ja foram configuradas no Passo 0-CLI. Pule para o **Passo 1.2**.

```
Para buscar os dados do Facebook Ads, precisamos de 2 informacoes:

1. Token de acesso (Access Token)
2. ID da conta de anuncios

Voce tem esses dados?

1. Sim, tenho os dois
2. Nao sei onde pegar
```

**Se nao souber onde pegar:**

```
Voce ja tem um App criado no Facebook Developers (developers.facebook.com)?

1. Sim, ja tenho
2. Nao tenho ainda
```

- **Opcao 2 (nao tem App):** execute a skill `criar-aplicativo-analise-ads`

Pergunte um por vez:

```
Cole seu Facebook Access Token:
```

Use `Edit` para salvar `FB_ACCESS_TOKEN_TEMPORARIO=valor` no `.env`. Depois:

```
Cole o ID da sua conta de anuncios (so os numeros):
```

Salve `FB_AD_ACCOUNT_ID=valor` no `.env`.

**Teste de conexao (modo Manual):**

```bash
powershell.exe -ExecutionPolicy Bypass -File "scripts/relatorio-ads.ps1"
```

Se o script buscar metricas sem erro, conexao validada.
Se retornar erro de credencial, token invalido ou ID errado, corrija o `.env`.

### 1.2 Credenciais do Canal de Envio

**Se `RELATORIO_CANAL=TELEGRAM`:**

Verifique se `TELEGRAM_BOT_TOKEN` e `TELEGRAM_CHAT_ID` existem no `.env`.

Se existirem, avance sem imprimir o token no terminal. Para testar, execute a skill `configurar-telegram`.

Se nao existirem: **execute a skill `configurar-telegram`**

---

**Se `RELATORIO_CANAL=WHATSAPP`:**

```
Agora as credenciais do Z-API para enviar no WhatsApp.

Voce tem conta na Z-API com instancia e WhatsApp conectado?

1. Sim, ja tenho
2. Nao tenho ainda
```

**Se nao tiver (opcao 2):** execute a skill `configurar-zapi`

Pergunte um por vez:

```
Cole o Instance ID da Z-API:
```

```
Cole o Token da Z-API:
```

```
Cole o Client-Token (Security Token):
```

Salve os tres no `.env`.

**Teste de conexao Z-API:**

Se `RELATORIO_AUTH_MODO=CLI`:
```bash
python scripts/relatorio-ads-cli.py 1
```

Se `RELATORIO_AUTH_MODO=MANUAL`:
```bash
powershell.exe -ExecutionPolicy Bypass -File "scripts/relatorio-ads.ps1"
```

Se o envio concluir sem erro, WhatsApp conectado.

### 1.3 Numero de destino (somente para WhatsApp)

Esta etapa so se aplica se `RELATORIO_CANAL=WHATSAPP`.

```
Para qual numero do WhatsApp devo enviar o relatorio?

Digite no formato internacional sem + e sem espacos.
(ex: 5511999887766)

Lembre: use um numero secundario aquecido, nao o numero principal da operacao.
```

Salve como `RELATORIO_WHATSAPP_NUMERO=valor` no `.env`.

---

## PASSO 2. Escolher Metricas

```
Quais metricas quer ver no relatorio?

1. Basico: gasto, alcance e impressoes
2. Completo: gasto, alcance, impressoes, cliques, CTR, CPM, CPC
3. Completo + conversoes (compras ou leads e custo por resultado)
4. Tudo acima

Digite o numero:
```

Salve a escolha no `.env` como `RELATORIO_METRICAS=1` (ou 2, 3, 4).

---

## PASSO 3. Filtro de Campanhas

```
Quais campanhas incluir no relatorio?

1. Todas as campanhas ativas
2. Todas (ativas e pausadas)
3. Filtrar por nome (eu digo o termo)

Digite o numero:
```

Se opcao 3: pergunte o termo de filtro (ex: "baixo custo", "produto X"). Salve como `RELATORIO_FILTRO_CAMPANHA=valor` no `.env`. Para opcoes 1 e 2, salve `RELATORIO_FILTRO_CAMPANHA=ativas` ou `RELATORIO_FILTRO_CAMPANHA=todas`.

---

## PASSO 4. Confirmacao

Mostre o resumo da configuracao salva:

**Se Telegram:**
```
Configuracao salva.

- Modo: [CLI ou Manual]
- Conta Meta Ads: [nome retornado no teste]
- Canal: Telegram (@username_do_bot)
- Metricas: [descricao da escolha]
- Campanhas: [descricao do filtro]

1. Tudo certo
2. Quero ajustar algo
```

**Se WhatsApp:**
```
Configuracao salva.

- Modo: [CLI ou Manual]
- Conta Meta Ads: [nome retornado no teste]
- Canal: WhatsApp [numero mascarado, ex: 5511****7766]
- Metricas: [descricao da escolha]
- Campanhas: [descricao do filtro]

1. Tudo certo
2. Quero ajustar algo
```

---

## PASSO 5. Oferecer Envio Imediato

Apos a confirmacao, pergunte:

```
Quer enviar um relatorio agora?

1. Sim, enviar relatorio de ontem
2. Nao, so queria configurar
```

Se opcao 1: execute a skill `enviar-relatorio-ads`. Ela cuida do periodo, busca os dados e envia no canal configurado.

Se opcao 2: encerre com a mensagem abaixo.

---

## PASSO 6. Entrega

```
Configuracao concluida.

Modo: [CLI ou Manual]
Canal: [Telegram ou WhatsApp]
Metricas: [descricao]
Campanhas: [descricao]

Para enviar um relatorio a qualquer momento: /enviar-relatorio-ads
```

---

## CHECKPOINTS OBRIGATORIOS

| Etapa | Aprovacao? |
|---|---|
| Teste de conexao Facebook (CLI ou Manual) | Confirmado antes de continuar |
| Teste de conexao Telegram ou Z-API | Confirmado antes de continuar |
| Confirmacao geral (resumo) | Sim, obrigatoria |

---

## REGRAS

- Nunca sobrescrever chaves ja existentes no `.env` sem perguntar. Usar `Edit` cirurgico.
- Nao exibir scripts ou arquivos de configuracao no chat. Salvar silenciosamente e informar apenas o caminho.
- Se a conta nao tiver dados no periodo, o relatorio informa "sem dados" e envia assim mesmo.
- Se o usuario ja tem `RELATORIO_CANAL` salvo e quiser trocar de canal: salvar novo valor e refazer o passo de credenciais do novo canal.
- Se o usuario quiser trocar de modo (CLI para Manual ou vice-versa): salvar novo `RELATORIO_AUTH_MODO` e refazer os passos de credenciais do modo escolhido.
- Modo CLI: usa `ACCESS_TOKEN` e `AD_ACCOUNT_ID`. Modo Manual: usa `FB_ACCESS_TOKEN_PERMANENTE`/`FB_ACCESS_TOKEN_TEMPORARIO` e `FB_AD_ACCOUNT_ID`. Ambos podem coexistir no `.env`.
