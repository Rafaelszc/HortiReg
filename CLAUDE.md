# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Projeto

HortiReg / SGV-WA: pedidos de hortifrúti via WhatsApp. Cliente manda texto ou áudio → Evolution API → webhook FastAPI → Gemini extrai itens (JSON) → bot pede SIM/NÃO → feirante vê pedidos e lista de separação no painel React.

Trabalho de Gerência de Software (UEPB), Scrum. Branches `feature/SCRUM-<n>-<slug>` saem de `develop`; PR para `develop`/`main` com 1 revisão mínima. US e critérios de aceite em Gherkin (pt), referenciados como `US-xx` / `CT-xx`.

PRs devem ser mesclados com **merge commit** (não squash/rebase) para manter commits e autores na `develop`.

## Layout

- `backend/` — API FastAPI (Python 3.12). README próprio com setup Docker e Evolution.
- `frontend/` — painel React 19 + Vite + TypeScript, E2E Cypress + Cucumber. `Dockerfile` multi-stage → nginx (`nginx.conf` faz proxy de `/auth` e `/pedidos` para `api:8000`; nova rota da API usada pelo painel precisa entrar aqui e no `vite.config.ts`).
- `docker-compose.yml` + `.env.example` na raiz — postgres, redis, evolution-api (:8080), api (:8000, `--reload` com `./backend/app` montado), frontend (:8081).
- `.github/workflows/ci.yml` — gitleaks, bandit, pip-audit, npm audit, ruff, pytest, Cypress.

## Comandos

Stack inteira (raiz):

```bash
cp .env.example .env                         # JWT_SECRET é obrigatório (sem default)
docker compose up -d --build
docker compose exec api python -m app.seed   # cria tabelas + admin do painel (ADMIN_LOGIN/ADMIN_PASSWORD)
```

API (rodar em `backend/`; `Settings` lê `backend/.env`, copiar o da raiz):

```bash
pip install -r requirements-dev.txt
ruff check .
pytest                                       # -m smoke | -m regressao
pytest tests/test_pedido.py -k "catálogo"    # um teste
pytest --cov=app --cov-fail-under=80         # CI exige 80% de cobertura
```

Testes da API precisam de Postgres real em `DATABASE_URL` (CI: `postgresql+asyncpg://test:test@localhost:5432/hortireg_test`) e de `JWT_SECRET`, `ADMIN_LOGIN`, `ADMIN_PASSWORD` no ambiente.

Painel (rodar em `frontend/`):

```bash
npm ci
npm run dev        # http://127.0.0.1:5173, proxy /auth e /pedidos → :8000
npm run build      # tsc --noEmit + vite build (é o type-check)
ADMIN_LOGIN=... ADMIN_PASSWORD=... TAGS='@smoke' npx cypress run   # precisa API + painel no ar
```

## Arquitetura da API

- `app/main.py`: lifespan roda `Base.metadata.create_all` (sem Alembic ainda). Mudou modelo → tabela existente não é alterada.
- `app/config.py`: `Settings` (pydantic-settings) lê `.env`; objeto global `settings`.
- `app/database.py`: engine async (asyncpg), `SessionLocal`, `get_session` como dependência.
- Regra: **routers** só recebem/respondem; lógica em **services** (`llm.py` Gemini, `whatsapp.py` Evolution, `catalogo.py` casa itens com `Produto` e calcula preço, `security.py` hash argon2 + JWT + bloqueio por tentativas).
- `routers/webhook.py`: `POST /webhook/whatsapp` responde 200 na hora e processa em `BackgroundTasks`. Ignora `fromMe` e grupos. Texto em `SIM`/`NAO` confirma/cancela o pedido pendente; senão chama `llm.extrair_pedido` e cria `Pedido` com status `AGUARDANDO_CONFIRMACAO`.
- `routers/pedidos.py`: todo o router protegido por `Depends(get_current_admin)`; `/pedidos` (filtro dia/status) e `/pedidos/separacao`.
- `routers/auth.py`: `POST /auth/login` → `access_token` Bearer.
- Status de pedido: `AGUARDANDO_CONFIRMACAO | CONFIRMADO | CANCELADO | ENTREGUE` (espelhado em `frontend/src/api.ts`).

## Testes

- `tests/conftest.py`: Postgres real; schema recriado por sessão e `TRUNCATE ... RESTART IDENTITY CASCADE` antes de cada teste. Usa engine própria com `NullPool` e helper `rodar(fn)` (loop novo por chamada) para preparar dados fora do `TestClient`.
- Gemini e WhatsApp nunca chamados de verdade: fixtures `llm_fake` (`responder(("tomate", 2, "kg"), ...)`) e `whatsapp_fake` (lista de mensagens enviadas) via monkeypatch nos módulos `app.services.*`. Chame os serviços como `llm.extrair_pedido(...)` (atributo do módulo), senão o monkeypatch não pega.
- Outras fixtures: `client`, `admin`, `token` (header Bearer), `catalogo`, `relogio` (controla `security.agora`); helper `mensagem(texto)` monta evento Evolution.
- BDD: `.feature` em `tests/features/` (`# language: pt`), steps com pytest-bdd em `tests/test_*.py`. Tags `@smoke`/`@regressao` viram markers.
- `pytest-bdd 9` quebra com `pytest >= 9.1`: manter o pin.
- Cypress: `.feature` + steps `.ts` em `frontend/cypress/e2e/`. CI roda `@smoke and not @wip` em push e `(@smoke or @regressao) and not @wip` em PR.

## Convenções

- Código, nomes, mensagens e commits em português. Commits Conventional (`feat(pedidos): ...`, `ci: ...`, `test(auth): ...`).
- ruff: line-length 120, regras `E,F,B,UP`; `B008` e `UP042` ignorados de propósito (`Depends()` default, `StatusPedido(str, Enum)`).
- Segredos: gitleaks no CI. Nada de segredo fixo em `ci.yml` (`JWT_SECRET` é gerado com `openssl rand`). `.env` nunca versionado.
- Vite/Cypress usam `127.0.0.1` explícito (`localhost` pode virar `::1` e quebrar o CI).
