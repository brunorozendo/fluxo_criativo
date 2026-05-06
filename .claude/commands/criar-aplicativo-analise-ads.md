---
name: workshop-marketing:criar-aplicativo-analise-ads
description: Guia passo a passo para criar um App no Facebook Developers com acesso à Marketing API, necessário para gerar o token de acesso ao Facebook Ads.
allowed-tools: Read, Write, Edit, Glob, Bash, WebFetch, WebSearch
model: sonnet
---

# Criar Aplicativo de Análise de Ads no Facebook

Guia para criar o App no Facebook Developers. So precisa fazer uma vez. O App e o que permite gerar o token de acesso a Marketing API.

---

## Fluxo de criacao (5 etapas)

Acesse developers.facebook.com e faca login com a conta de admin do negocio. Clique em "Meus Apps" > "Criar App".

**Etapa 1. Detalhes do app**
- Nome do app: use "Relatorio de Anuncios" ou qualquer nome simples
- Email de contato: ja vem preenchido com o email do Facebook, pode deixar como esta
- Clique em "Avancar"

**Etapa 2. Casos de uso**
- A tela abre com o filtro "Em Destaque" selecionado, mostrando apenas 6 opcoes
- Troque o filtro para "Tudo" para ver todas as opcoes disponiveis
- Localize e selecione "Mensurar dados de desempenho do anuncio com a API de Marketing"
- Clique em "Avancar"

**Etapa 3. Empresa**
- Selecione o Portfolio Empresarial (Business Manager) que contem a conta de anuncios que voce quer monitorar
- Se nao aparecer nenhuma opcao, verifique se esta logado com a conta de admin do BM
- Clique em "Avancar"

**Etapa 4. Requisitos**
- Nenhuma acao necessaria nessa tela
- Clique em "Avancar"

**Etapa 5. Visao geral**
- Revise as informacoes do app
- Clique em "Criar Aplicativo"

---

## Apos criar o App: configurar e publicar

**Passo 1. Adicionar politica de privacidade**
- No menu lateral do app, clique em "Configuracoes do App" > "Basico"
- No campo "URL da Politica de Privacidade", cole a URL da pagina de politica de privacidade do negocio
- A URL precisa ser real e acessivel (nao aceita placeholder)
- Se nao tiver uma pagina de politica pronta, pode usar o link da pagina de politica do site existente, ou criar uma pagina simples no Notion, Google Sites ou similar
- Clique em "Salvar alteracoes"

**Passo 2. Publicar o app**
- No menu lateral, clique em "Publicar"
- Clique no botao "Publicar"
- O app precisa estar publicado para que o token funcione corretamente

---

## Apos criar o App: gerar o token de acesso

Execute a skill `gerar-token-permanente-facebook-ads`. Ela guia o usuario pelo processo completo de criacao do Usuario do Sistema e geracao do token permanente.

---

## Como encontrar o ID da conta de anuncios

- Acesse o Gerenciador de Anuncios (facebook.com/adsmanager)
- O ID aparece no canto superior esquerdo: `Conta: XXXXXXXXXX`
- Ou olhe na URL: o numero apos `act=`
- Copie so os numeros (sem "act_")

---

## Se o usuario nao encontrar alguma opcao

Use `WebFetch` para buscar a documentacao atualizada antes de responder:

```
URL 1: https://developers.facebook.com/docs/marketing-apis/get-started
URL 2: https://developers.facebook.com/docs/marketing-api/system-users
```

Se as URLs retornarem erro ou conteudo vago, use WebSearch com a query: `site:developers.facebook.com marketing api access token tutorial`

Adapte as instrucoes com base no conteudo retornado. Nao cite que buscou na documentacao.
