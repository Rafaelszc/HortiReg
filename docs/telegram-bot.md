# Bot do Telegram — HortiReg (`@HortRegBot`)

Documentação de arquitetura, operação e modos de recebimento de mensagens do bot **HortiReg** (`@HortRegBot`) na API do SGV-WA.

> **Estratégia atual e próximo passo**
>
> - **Agora (desenvolvimento local):** estamos utilizando a **Opção 1 — Long Polling (`getUpdates`)**, para que o bot funcione imediatamente em `localhost` sem necessidade de túnel ou HTTPS público.
> - **Em seguida (homologação / produção):** migraremos para a **Opção 2 — Webhook (`POST /webhook/telegram`)**, que é o modo recomendado para ambientes publicados com HTTPS. Toda a estrutura de webhook, autenticação e rotas administrativas já está implementada na API — a troca depende apenas de configuração de ambiente e registro da URL.

---

## Visão geral da implementação

Os dois modos compartilham exatamente a mesma lógica de atendimento de pedidos (texto, áudio, catálogo, expiração e confirmação por `1`/`2`/`3` ou botões inline). Apenas a forma como os updates chegam até a função `processar_update` muda.

| Componente | Arquivo | Responsabilidade |
|---|---|---|
| Configuração | `backend/app/config.py` | Lê `TELEGRAM_BOT_TOKEN`, `TELEGRAM_BOT_NAME`, `TELEGRAM_BOT_USERNAME`, `TELEGRAM_WEBHOOK_SECRET`, `TELEGRAM_WEBHOOK_URL` e `TELEGRAM_POLLING` |
| Cliente Bot API | `backend/app/services/telegram.py` | Chamadas HTTP à Bot API (`sendMessage`, `answerCallbackQuery`, `getFile`, `getUpdates`, `setWebhook`, `deleteWebhook`, `getWebhookInfo`, `getMe`) |
| Lógica do bot | `backend/app/services/telegram_bot.py` | Processamento de `/start`, `/ajuda`, texto, áudio, callbacks inline, idempotência e loop de polling (`rodar_polling`) |
| Autenticação | `backend/app/services/webhook_auth.py` | Valida o cabeçalho `X-Telegram-Bot-Api-Secret-Token` no webhook (`exigir_secret_telegram`) |
| Rotas | `backend/app/routers/telegram.py` | `POST /webhook/telegram` e rotas administrativas `/telegram/*` |
| Ciclo de vida | `backend/app/main.py` | Inicia `rodar_polling()` automaticamente apenas quando `TELEGRAM_POLLING=true`, `TELEGRAM_BOT_TOKEN` está preenchido e `TELEGRAM_WEBHOOK_URL` está vazio |

---

## Opção 1: Long Polling (`getUpdates`) — *Modo atual (desenvolvimento)*

### Como funciona

A própria API abre conexões de saída para os servidores do Telegram em um loop contínuo perguntando se há novas mensagens:

```text
API local  ──(POST /getUpdates)──────▶  Servidores do Telegram
API local  ◀──(retorna "/start")──────  Servidores do Telegram
API local  ──(POST /sendMessage)─────▶  Servidores do Telegram  ──▶  App do cliente
```

Ao iniciar, `rodar_polling()` remove qualquer webhook anterior (`deleteWebhook`) para evitar conflito (`409 Conflict`), consulta `getUpdates` com timeout de 25s, avança o `offset` (`update_id + 1`) e entrega cada evento para `processar_update()`.

### Vantagens e limitações

- **Vantagens:**
  - Funciona diretamente em `localhost` / Docker local, sem `ngrok`, `cloudflared` ou certificado HTTPS.
  - Configuração mínima (basta informar o token e ativar o polling).
- **Limitações:**
  - Apenas **uma instância** da API pode fazer polling com o mesmo token por vez (múltiplas réplicas geram erro `409 Conflict`).
  - Mantém uma tarefa em segundo plano aberta durante toda a execução da API.

### Como configurar (desenvolvimento local)

No arquivo `.env` (e em `backend/.env` caso rode `uvicorn` fora do Docker):

```env
TELEGRAM_BOT_TOKEN=seu-token-do-botfather
TELEGRAM_BOT_NAME=HortiReg
TELEGRAM_BOT_USERNAME=HortRegBot
TELEGRAM_WEBHOOK_SECRET=
TELEGRAM_WEBHOOK_URL=
TELEGRAM_POLLING=true
```

Depois, reinicie a API (`docker compose up -d api`). Nos logs deverá aparecer:

```text
INFO:sgv.telegram:Iniciando long polling do Telegram (@HortRegBot)
```

---

## Opção 2: Webhook (`POST /webhook/telegram`) — *Próximo passo (homologação / produção)*

### Como funciona

Em vez de a API ficar consultando o Telegram, registramos uma URL pública HTTPS na Bot API (`setWebhook`). Sempre que um cliente envia uma mensagem ou clica em um botão, o Telegram faz um `POST` diretamente para a nossa API:

```text
App do cliente ──▶ Servidores do Telegram ──(POST https://seu-dominio/webhook/telegram)──▶ API HortiReg
```

A rota `POST /webhook/telegram` valida o segredo do cabeçalho `X-Telegram-Bot-Api-Secret-Token`, responde `200 OK` imediatamente e processa o update em `BackgroundTasks`.

### Vantagens e limitações

- **Vantagens:**
  - Entrega imediata orientada a eventos (sem loop de polling).
  - Escalável em ambientes com múltiplas instâncias/containers.
  - Autenticação nativa por cabeçalho secreto (`X-Telegram-Bot-Api-Secret-Token`).
- **Limitações:**
  - Exige obrigatoriamente uma **URL pública com HTTPS válido** (o Telegram não envia webhooks para `localhost` nem para HTTP puro).
  - Para testar webhook localmente, é necessário um túnel HTTPS (ex.: `ngrok http 8000` ou `cloudflared tunnel --url http://localhost:8000`).

### Como migrar da Opção 1 para a Opção 2

Quando a API estiver acessível em um domínio HTTPS (ou túnel HTTPS para testes):

1. **Gere um segredo para o webhook:**
   ```bash
   openssl rand -hex 24
   ```

2. **Atualize o `.env`:**
   ```env
   TELEGRAM_BOT_TOKEN=seu-token-do-botfather
   TELEGRAM_BOT_NAME=HortiReg
   TELEGRAM_BOT_USERNAME=HortRegBot
   TELEGRAM_WEBHOOK_SECRET=segredo-gerado-acima
   TELEGRAM_WEBHOOK_URL=https://seu-dominio.com/webhook/telegram
   TELEGRAM_POLLING=false
   ```
   > Mesmo que `TELEGRAM_POLLING` continue `true`, o polling é desativado automaticamente assim que `TELEGRAM_WEBHOOK_URL` é preenchido.

3. **Reinicie a API** para carregar as novas variáveis.

4. **Registre o webhook no Telegram** (usando um token JWT de administrador obtido em `POST /auth/login`):
   ```bash
   curl -X POST https://seu-dominio.com/telegram/webhook \
     -H "Authorization: Bearer <SEU_TOKEN_ADMIN>"
   ```
   *(Opcionalmente, você pode enviar `{"url": "https://..."}` no corpo da requisição para sobrescrever `TELEGRAM_WEBHOOK_URL`.)*

5. **Confirme o registro:**
   ```bash
   curl https://seu-dominio.com/telegram/webhook \
     -H "Authorization: Bearer <SEU_TOKEN_ADMIN>"
   ```

---

## Comparativo rápido

| Critério | Opção 1: Long Polling (`getUpdates`) | Opção 2: Webhook (`POST /webhook/telegram`) |
|---|---|---|
| **Status no projeto** | **Em uso agora (dev local)** | **Próximo passo (staging / produção)** |
| **Funciona em `localhost`?** | Sim, direto | Não (exige HTTPS público ou túnel) |
| **Infraestrutura extra** | Nenhuma | Domínio HTTPS + `TELEGRAM_WEBHOOK_SECRET` |
| **Escala com várias réplicas?** | Não (`409 Conflict`) | Sim |
| **Latência / carga** | Requisições contínuas em loop | Push instantâneo sob demanda |

---

## Endpoints do bot na API

| Método | Rota | Autenticação | Descrição |
|---|---|---|---|
| `POST` | `/webhook/telegram` | `X-Telegram-Bot-Api-Secret-Token` (se configurado) | Recebe updates enviados pela Bot API do Telegram |
| `GET` | `/telegram/info` | Bearer Admin | Retorna nome, username, status do token e URL configurada |
| `GET` | `/telegram/webhook` | Bearer Admin | Consulta o status atual do webhook no Telegram (`getWebhookInfo`) |
| `POST` | `/telegram/webhook` | Bearer Admin | Registra a URL do webhook no Telegram (`setWebhook`) |
| `DELETE` | `/telegram/webhook` | Bearer Admin | Remove o webhook registrado no Telegram (`deleteWebhook`) |
