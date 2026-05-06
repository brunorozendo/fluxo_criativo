---
name: workshop-marketing:gerar-token-permanente-facebook-ads
description: Guia para gerar token permanente de acesso ao Facebook Ads via Usuário do Sistema no Business Manager. Token nunca expira e não precisa ser renovado.
allowed-tools: Read, Write, Edit, Glob, Bash, WebFetch, WebSearch
model: sonnet
---

# Gerar Token Permanente do Facebook Ads

Token via Usuario do Sistema. Nao expira. Nao precisa renovar.

Prerequisito: ter o App criado conforme a skill `criar-aplicativo-analise-ads`.

---

## Passo 1. Criar o Usuario do Sistema

- Acesse business.facebook.com/latest/settings
- No menu lateral, em "Usuarios", clique em "Usuarios do sistema"
- No canto superior direito, clique em "Adicionar"
- Na tela que abrir:
  - Nomeie o usuario: use "Relatorio Ads" ou qualquer nome simples
  - Em "System user role", selecione "Admin"
  - Clique em "Adicionar"

---

## Passo 2. Atribuir Ativos ao Usuario

Com o usuario do sistema criado e selecionado, clique em "Atribuir Ativos". Uma tela vai abrir com menu lateral. Faca as duas atribuicoes abaixo:

**Contas de anuncio (a tela ja abre aqui):**
- A tela abre diretamente em "Contas de anuncio"
- Selecione todas as contas que deseja monitorar
- Ative "Controle total" em cada uma
- Clique em "Atribuir ativos"

**Apps:**
- No menu lateral, clique em "Apps"
- Selecione o app criado ("Relatorio de Anuncios" ou o nome que usou)
- Ative "Controle total"
- Clique em "Atribuir ativos"

---

## Passo 3. Gerar o Token

- Ao lado do nome do usuario de sistema, clique em "Gerar token"
- Uma tela com 4 etapas vai abrir:

**Etapa 1. Selecionar app**
- Selecione o app criado ("Relatorio de Anuncios")
- Clique em "Avancar"

**Etapa 2. Definir expiracao**
- Selecione "Nunca" (nao selecione "60 dias" para evitar manutencao futura)
- Clique em "Avancar"

**Etapa 3. Atribuir permissoes**

O Facebook mostra apenas os escopos disponiveis para o tipo de app criado. Marque todos que aparecerem. Os 7 escopos que o Meta Ads CLI precisa sao:

| Escopo | Para que serve |
|---|---|
| `ads_management` | Criar e gerenciar campanhas, conjuntos e anuncios |
| `ads_read` | Ler dados de anuncios e metricas |
| `business_management` | Acesso ao Business Manager e ativos |
| `read_insights` | Buscar relatorios e insights de desempenho |
| `pages_read_engagement` | Dados de engajamento de paginas vinculadas |
| `pages_show_list` | Listar paginas vinculadas ao negocio |
| `catalog_management` | Gerenciar catalogos de produtos (necessario para o CLI) |

Se algum desses nao aparecer na tela, nao se preocupe: o Facebook so exibe os que sao compativeis com o caso de uso escolhido no app. Marque tudo que estiver disponivel.

- Clique em "Gerar token"

**Etapa 4. Concluir**
- O token vai aparecer na tela
- Copie o token e guarde em um lugar seguro (ele nao aparece novamente)
- Clique em "Concluir"

---

## Passo 4. Validar o token

Execute o comando abaixo no terminal (substitua TOKEN pelo token copiado):

```bash
curl "https://graph.facebook.com/v25.0/me?access_token=TOKEN"
```

Se retornar `{"id":"...","name":"Relatorio Ads"}` (ou o nome que deu ao usuario): token valido.
Se retornar `{"error":...}`: token invalido ou sem permissao. Repita o Passo 3 garantindo que todas as permissoes foram selecionadas.

---

## Apos validar o token

Salve o token no `.env` com o nome exato:

```
FB_ACCESS_TOKEN_PERMANENTE=seu_token_aqui
```

Use `Edit` cirurgico para adicionar ou atualizar essa linha no `.env`. Nao sobrescreva outras variaveis.

Em seguida, execute a skill `obter-id-conta-anuncios` para localizar o ID da conta de anuncios.

Se o usuario disser que nao encontrou alguma opcao ou que a tela esta diferente, use WebFetch para buscar a documentacao atualizada:

```
https://developers.facebook.com/docs/marketing-api/system-users
```

Adapte as instrucoes com base no conteudo retornado. Nao cite que buscou na documentacao.
