---
name: workshop-marketing:enviar-relatorio-ads
description: Busca as métricas do Facebook Ads e envia o relatório pelo Telegram ou WhatsApp. Detecta automaticamente o modo configurado (CLI Python ou Manual PowerShell).
allowed-tools: Read, Bash
model: sonnet
---

# Enviar Relatorio de Ads

Executa imediatamente: busca as metricas do Facebook Ads do periodo escolhido e envia no canal configurado (Telegram ou WhatsApp). Sem agendamento.

Detecta `RELATORIO_AUTH_MODO` no `.env` e usa o script correto:
- `CLI`: `scripts/relatorio-ads-cli.py` (Python, cross-platform)
- `MANUAL` ou nao definido: `scripts/relatorio-ads.ps1` (PowerShell, Windows)

## PASSO 1. Verificar credenciais

Leia `.env`.

**Detectar o modo:**

Se `RELATORIO_AUTH_MODO=CLI` (ou nao definido mas `ACCESS_TOKEN` existir):
- Verificar `ACCESS_TOKEN` (ou fallback `FB_ACCESS_TOKEN_PERMANENTE` / `FB_ACCESS_TOKEN_TEMPORARIO`)
- Verificar `AD_ACCOUNT_ID` (ou fallback `FB_AD_ACCOUNT_ID`)
- Se faltar: oriente a rodar `/ads-relatorio` primeiro para configurar o modo CLI.

Se `RELATORIO_AUTH_MODO=MANUAL` (ou nao definido e `ACCESS_TOKEN` nao existir):
- Verificar pelo menos uma das variaveis: `FB_ACCESS_TOKEN_PERMANENTE` ou `FB_ACCESS_TOKEN_TEMPORARIO`
- Verificar `FB_AD_ACCOUNT_ID`
- Se faltar token: pergunte se tem App no Facebook Developers
  - Se sim: execute a skill `gerar-token-permanente-facebook-ads`
  - Se nao: execute a skill `criar-aplicativo-analise-ads`, depois `gerar-token-permanente-facebook-ads`
- Se faltar `FB_AD_ACCOUNT_ID`: execute a skill `obter-id-conta-anuncios`

**Canal de envio:**
- Se `RELATORIO_CANAL` nao existir no `.env`, pergunte:

```
Por qual canal quer enviar o relatorio?

1. Telegram (Recomendado)
2. WhatsApp

Digite o numero:
```

Se o usuario perguntar por que Telegram e recomendado: "O Telegram e gratuito e nao tem risco de bloqueio. Automacoes no WhatsApp podem banir o numero."

Se WhatsApp, exiba antes de continuar: "Atencao: use um numero secundario aquecido, nao o numero principal da operacao."

Salve `RELATORIO_CANAL=TELEGRAM` ou `RELATORIO_CANAL=WHATSAPP` no `.env` com `Edit`.

**Se `RELATORIO_CANAL=TELEGRAM`:**
- Verificar `TELEGRAM_BOT_TOKEN` e `TELEGRAM_CHAT_ID`
- Se faltar qualquer um: execute a skill `configurar-telegram`, depois retorne

**Se `RELATORIO_CANAL=WHATSAPP`:**
- Verificar `ZAPI_INSTANCE_ID`, `ZAPI_TOKEN`, `ZAPI_CLIENT_TOKEN`, `RELATORIO_WHATSAPP_NUMERO`
- Se faltar qualquer credencial Z-API: pergunte se tem conta na Z-API
  - Se sim: peca as 3 credenciais uma por vez e salve no `.env` com `Edit`
  - Se nao: execute a skill `configurar-zapi`, depois retorne
- Se faltar `RELATORIO_WHATSAPP_NUMERO`:

```
Para qual numero do WhatsApp devo enviar o relatorio?

Digite no formato internacional sem + e sem espacos.
(ex: 5511999887766)
```

Salve como `RELATORIO_WHATSAPP_NUMERO=valor` no `.env`.

**Quando todas as credenciais estiverem presentes:** avance para o Passo 2.

## PASSO 2. Perguntar o periodo

Pergunte ao usuario:

```
Qual periodo voce quer no relatorio?

1. Ontem
2. Ultimos 7 dias
3. Ultimos 30 dias
4. Periodo personalizado (informar data inicial e final)

Digite o numero:
```

- Opcao 1: calcule `INICIO_ISO` e `FIM_ISO` como ontem. Label do periodo: `{ONTEM_BR}`.
- Opcao 2: `INICIO_ISO` = hoje menos 7 dias, `FIM_ISO` = ontem. Label: `Ultimos 7 dias`.
- Opcao 3: `INICIO_ISO` = hoje menos 30 dias, `FIM_ISO` = ontem. Label: `Ultimos 30 dias`.
- Opcao 4: peca a data inicial (formato DD/MM/AAAA) e a data final (formato DD/MM/AAAA), converta para ISO (AAAA-MM-DD). Label: `{INICIO_BR} a {FIM_BR}`.

Para calcular as datas use Bash:
```bash
# Ontem
date -d "yesterday" +%Y-%m-%d 2>/dev/null || date -v-1d +%Y-%m-%d
# 7 dias atras
date -d "7 days ago" +%Y-%m-%d 2>/dev/null || date -v-7d +%Y-%m-%d
# 30 dias atras
date -d "30 days ago" +%Y-%m-%d 2>/dev/null || date -v-30d +%Y-%m-%d
```

Guarde `INICIO_ISO`, `FIM_ISO` e `LABEL_PERIODO`.

## PASSO 3. Executar busca de dados

Use o script adequado ao modo configurado. Ambos le o `.env`, mascaram segredos nos logs e retornam os dados formatados.

**Se `RELATORIO_AUTH_MODO=CLI`:**

Determine o comando Python correto primeiro:
```bash
python --version 2>&1 || python3 --version 2>&1
```

Depois execute (substitua `python` por `python3` se necessario):
```bash
python scripts/relatorio-ads-cli.py {ESCOLHA_PERIODO} {INICIO_BR} {FIM_BR}
```

Onde `{ESCOLHA_PERIODO}` e o numero escolhido no Passo 2 (1, 2, 3 ou 4). Para opcao 4, passe tambem inicio e fim no formato DD/MM/AAAA. Exemplos:
- Ontem: `python scripts/relatorio-ads-cli.py 1`
- Ultimos 7 dias: `python scripts/relatorio-ads-cli.py 2`
- Personalizado: `python scripts/relatorio-ads-cli.py 4 01/04/2026 30/04/2026`

**Se `RELATORIO_AUTH_MODO=MANUAL` (ou nao definido):**
```bash
powershell.exe -ExecutionPolicy Bypass -File "scripts/relatorio-ads.ps1"
```

Nunca passe `ACCESS_TOKEN`, `ZAPI_TOKEN`, `TELEGRAM_BOT_TOKEN` ou qualquer chave pela URL, pelo chat ou por comando que possa aparecer no historico do terminal.

## PASSO 4. Montar a mensagem

Se `data` vier vazio (`[]`):

```
*Relatorio Meta Ads - {LABEL_PERIODO}*

Sem dados para o periodo. Verifique se ha campanhas ativas.
```

Se `data` tiver conteudo, monte:

```
*Relatorio Meta Ads - {LABEL_PERIODO}*

*Investimento e Alcance*
Gasto: R$ X,XX
Alcance: X.XXX
Impressoes: X.XXX

*Engajamento*
Cliques: X.XXX
CTR: X,XX%
CPM: R$ X,XX
CPC: R$ X,XX
```

Se houver `actions` com `action_type` igual a `purchase` ou `lead`, adicione:

```
*Conversoes*
Resultados: X
Custo por resultado: R$ X,XX
```

Formatacao numerica: valores monetarios com virgula decimal e ponto milhar (ex: `R$ 1.234,56`). Percentuais com virgula (ex: `3,42%`).

## PASSO 5. Confirmar envio

**Se Telegram:**

```
Relatorio pronto. Deseja enviar para o seu Telegram?

1. Sim, enviar agora
2. Nao, apenas exibir aqui
```

**Se WhatsApp:**

```
Relatorio pronto. Deseja enviar para o WhatsApp {NUMERO_MASCARADO}?

1. Sim, enviar agora
2. Nao, apenas exibir aqui
```

Se opcao 2: encerre sem chamar nenhuma API de envio.

## PASSO 6. Enviar

O script ja cuida do envio internamente. Basta executar o mesmo comando do Passo 3 se o usuario confirmar:

**Se `RELATORIO_AUTH_MODO=CLI`:**
```bash
python scripts/relatorio-ads-cli.py {ESCOLHA_PERIODO}
```

**Se `RELATORIO_AUTH_MODO=MANUAL` (ou nao definido):**
```bash
powershell.exe -ExecutionPolicy Bypass -File "scripts/relatorio-ads.ps1"
```

Nao use `curl` manual com token em URL ou header escrito no comando.

## PASSO 7. Resultado

**Se Telegram:**

- Sucesso (`"ok":true`): informe "Relatorio enviado para o seu Telegram."
- Erro: mostre a mensagem de erro e oriente:
  - `"Unauthorized"` ou error_code 401: token do bot invalido. Rode `/configurar-telegram` para reconfigurar.
  - `"chat not found"`: Chat ID errado. Rode `/configurar-telegram` para obter o Chat ID correto.
  - Qualquer outro erro: mostre o retorno bruto para diagnostico.

**Se WhatsApp (Z-API):**

- Sucesso: informe "Relatorio enviado para {numero mascarado}."
- Erro, mostre a mensagem e oriente:
  - `"subscribe to this instance again"`: assinatura Z-API expirada. Acesse o painel da Z-API e renove o plano.
  - `"connected":false`: WhatsApp desconectado. Acesse o painel da Z-API e reconecte pelo QR Code.
  - Qualquer outro erro: mostre o retorno bruto para diagnostico.
