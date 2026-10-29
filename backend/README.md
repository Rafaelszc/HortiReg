# SGV-WA – Sistema de Gestão de Vendas via WhatsApp

Automação de pedidos de hortifrúti: o cliente manda áudio/texto no WhatsApp, uma LLM (Gemini) extrai os itens, o cliente confirma com SIM/NÃO e o feirante recebe a lista consolidada de separação.

## 1. Como as peças se conectam

```
 Cliente (WhatsApp)
        │  mensagem / áudio
        ▼
 Evolution API  (container, porta 8080)   ← conversa com o WhatsApp (QR Code)
        │  webhook POST /webhook/whatsapp
        ▼
 FastAPI  (container "api", porta 8000)   ← seu código Python
        │            │
        │            └──► Gemini API (internet): áudio/texto → JSON
        ▼
 PostgreSQL (container, porta 5432)       ← bancos "sgv" (seu) e "evolution" (dela)
        ▲
 Redis (container)  ← cache da Evolution API
```

Tudo roda com **um comando** (`docker compose up`, na raiz do repositório). Você não instala Postgres, Redis nem a Evolution na máquina. Os comandos `docker compose` deste guia rodam na raiz; os de Python (`pip`, `pytest`, `uvicorn`), em `backend/`.

## 2. Estrutura de pastas

```
HortiReg/
├── docker-compose.yml      # sobe Postgres, Redis, Evolution API, a API e o painel (:8081)
├── .env.example            # modelo das variáveis (copie para .env)
├── frontend/               # painel React
└── backend/
    ├── Dockerfile              # imagem da sua API (Python 3.12)
    ├── requirements.txt        # dependências Python
    ├── docker/
    │   └── init-db.sh          # cria o banco "evolution" na 1ª execução
    ├── app/
    │   ├── main.py             # cria o FastAPI, registra as rotas
    │   ├── config.py           # lê variáveis de ambiente
    │   ├── database.py         # conexão async com o Postgres
    │   ├── models/             # tabelas (Cliente, Produto, Pedido, ItemPedido)
    │   ├── schemas/pedido.py   # formato JSON que a LLM deve devolver
    │   ├── routers/
    │   │   ├── webhook.py      # recebe mensagens do WhatsApp (fluxo de confirmação)
    │   │   └── pedidos.py      # lista pedidos e relatório de separação
    │   └── services/
    │       ├── llm.py          # chamada ao Gemini (texto/áudio → itens)
    │       └── whatsapp.py     # envia mensagens / baixa áudio na Evolution API
    └── tests/test_health.py
```

Regra de ouro: **routers** só recebem/respondem requisições; a lógica "de verdade" (LLM, WhatsApp, rotas) fica em **services**.

## 3. Pré-requisitos

| Item | Como obter |
|---|---|
| Docker Desktop | https://www.docker.com/products/docker-desktop (no Windows, habilite o **WSL 2** quando pedir) |
| Git | https://git-scm.com |
| VS Code | já tem |
| Chave do Gemini | https://aistudio.google.com/apikey (gratuita para testes) |
| Um chip/número **secundário** de WhatsApp | ⚠️ não use seu número principal (veja "Avisos") |

Confira no terminal:
```bash
docker --version
docker compose version
```

## 4. Passo a passo

### 4.1 Configurar variáveis
Na raiz do repositório:
```bash
cp .env.example .env        # Windows PowerShell: copy .env.example .env
```
Abra o `.env` e preencha:
- `POSTGRES_PASSWORD`: qualquer senha.
- `EVOLUTION_API_KEY`: string longa aleatória (é a "senha" da Evolution).
- `GEMINI_API_KEY`: a chave do AI Studio.
- `ADMIN_NUMBERS`: seu número com DDI e DDD, ex.: `5583999999999`.

### 4.2 Subir tudo
```bash
docker compose up -d --build
docker compose ps            # todos devem estar "running"/"healthy"
docker compose logs -f api   # logs da sua API (Ctrl+C para sair)
```
Teste: abra http://localhost:8000/docs (documentação interativa) e http://localhost:8000/health. O painel fica em http://localhost:8081 (crie o admin com `docker compose exec api python -m app.seed`).

> Na primeira vez o download das imagens demora alguns minutos.

### 4.3 Conectar o WhatsApp (Evolution API)

1. Abra o painel: http://localhost:8080/manager e informe a `EVOLUTION_API_KEY` quando pedir.
2. Crie uma instância chamada **sgv** (mesmo nome de `EVOLUTION_INSTANCE`), integração **WHATSAPP-BAILEYS**.
3. Clique em conectar e escaneie o QR Code com o WhatsApp do número secundário (Aparelhos conectados → Conectar aparelho).

Alternativa por linha de comando:
```bash
curl -X POST http://localhost:8080/instance/create \
  -H "apikey: SUA_EVOLUTION_API_KEY" -H "Content-Type: application/json" \
  -d '{"instanceName":"sgv","qrcode":true,"integration":"WHATSAPP-BAILEYS"}'
```

O webhook já está configurado globalmente no `docker-compose.yml` (`WEBHOOK_GLOBAL_URL=http://api:8000/webhook/whatsapp`). Dentro do Docker os containers se enxergam pelo **nome do serviço** (`api`, `postgres`, `evolution-api`), por isso não é `localhost`.

### 4.4 Testar o fluxo completo

1. De **outro** número, mande para o número conectado: *"quero 2 quilos de tomate e 3 maços de coentro"* (ou um áudio).
2. O bot responde com o resumo e pede **SIM/NÃO**.
3. Responda **SIM**.
4. Veja os dados: http://localhost:8000/pedidos e http://localhost:8000/pedidos/separacao (totais somados dos pedidos confirmados).

Se algo falhar: `docker compose logs -f api evolution-api`.

## 5. Comandos do dia a dia

```bash
docker compose up -d              # sobe tudo
docker compose down               # para tudo (mantém os dados)
docker compose down -v            # para e APAGA os dados (banco, sessão do WhatsApp)
docker compose restart api        # reinicia só a API
docker compose logs -f api        # logs
docker compose exec postgres psql -U sgv -d sgv   # abre o banco (\dt lista tabelas, \q sai)
docker compose up -d --build api  # depois de mudar requirements.txt
```
Editou código em `backend/app/`? O `--reload` já recarrega sozinho (volume montado).

## 6. Rodar sem Docker (opcional, para debugar no VS Code)

Em `backend/` (copie o `.env` da raiz para `backend/.env`):
```bash
python -m venv .venv
.venv\Scripts\activate            # Linux/Mac: source .venv/bin/activate
pip install -r requirements.txt
docker compose up -d postgres redis evolution-api
```
Defina `DATABASE_URL=postgresql+asyncpg://sgv:SUASENHA@localhost:5433/sgv` e `EVOLUTION_URL=http://localhost:8080` no `.env`, e como o webhook global aponta para `http://api:8000`, troque para `http://host.docker.internal:8000/webhook/whatsapp` no compose. Depois:
```bash
uvicorn app.main:app --reload
pytest
```

## 7. Avisos importantes

- **Evolution API/Baileys não é oficial**: o WhatsApp pode banir o número. Use chip secundário nos testes; para produção avalie a **WhatsApp Cloud API** oficial da Meta.
- Nunca suba o `.env` para o Git (já está no `.gitignore`).
- Verifique na documentação da Evolution (https://doc.evolution-api.com) se os nomes de variáveis/endpoints mudaram. A imagem foi fixada em `atendai/evolution-api:v2.1.1`; o fluxo de download de áudio (`/chat/getBase64FromMediaMessage`) e o formato do webhook podem variar entre versões.
- As tabelas são criadas automaticamente na inicialização (`create_all`). Para evoluir o banco com segurança, adote **Alembic** (migrações).
- O código ainda **não** usa `ADMIN_NUMBERS` (modo admin) nem calcula rotas: são os próximos módulos.

## 8. Próximos passos (roadmap)

1. **Catálogo e admin**: endpoints CRUD de `Produto` + comandos de admin pelo WhatsApp (`ADMIN_NUMBERS`), casando `ItemPedido.nome` com `Produto` e calculando valor estimado.
2. **Endereço do cliente**: pedir e salvar o endereço na primeira compra.
3. **Seleção de pedidos para entrega** (status `CONFIRMADO` → carregado no veículo).
4. **Rotas**: geocodificar endereços (Google Geocoding API) e resolver o TSP com `ortools`; gerar o link `https://www.google.com/maps/dir/...`.
5. **Painel React** consumindo esta API (CORS + autenticação).
6. **Alembic**, testes dos serviços e deploy (VPS com Docker Compose).

## 9. Para estudar

- FastAPI: https://fastapi.tiangolo.com/pt/
- SQLAlchemy 2.0 async: https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html
- Docker Compose: https://docs.docker.com/compose/
- Evolution API v2: https://doc.evolution-api.com
- Gemini (saída estruturada e áudio): https://ai.google.dev/gemini-api/docs
