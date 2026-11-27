# HortiReg (SGV-WA)

Sistema de pedidos de hortifrúti pelo WhatsApp. Trabalho de Gerência de Software (UEPB), em Scrum.

## Problema

O feirante recebe pedidos por mensagem de texto e áudio no WhatsApp, cada um num formato. Hoje ele lê e ouve tudo à mão, anota itens e quantidades e monta a lista de separação antes da feira. Isso toma tempo, gera erro (item trocado, quantidade errada, pedido esquecido) e não deixa registro dos pedidos.

## Solução

- O cliente manda o pedido em texto ou áudio no WhatsApp.
- A IA (Gemini) extrai os itens e as quantidades e confere com o catálogo de produtos e preços.
- O bot devolve o resumo com valor estimado e pede a confirmação do cliente.
- O feirante vê, no painel web, os pedidos confirmados do dia e a lista de separação consolidada.

Fluxo técnico: WhatsApp → Evolution API → webhook FastAPI → Gemini → Postgres → painel React.

## Papéis e responsabilidades (Release 2)

| Papel                  | Responsável   | Responsabilidades                                                                                                                                                                                                                                                                                                         |
| ---------------------- | ------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **PO (Product Owner)** | Julio        | Mantém e prioriza o Product Backlog; escreve e valida as US e os critérios de aceite em Gherkin; define a meta de cada release; fornece as amostras de áudio e texto do conjunto de referência da IA; aceita ou rejeita cada US na Sprint Review; valida os drivers arquiteturais.                                        |
| **SM (Scrum Master)**  | Nidlan        | Facilita Planning, Daily, Review e Retrospectiva; remove impedimentos; mantém a Definition of Done e o board atualizados; acompanha velocity, burndown e a planilha de riscos; registra os papéis da próxima release neste README.                                                                                        |
| **QA (Qualidade)**     | Rafael         | Conduz o Plano de Qualidade e o Plano de Teste; escreve os `.feature` e automatiza os cenários (Cypress e pytest-bdd); executa testes exploratórios e de usabilidade; verifica os 9 drivers arquiteturais; registra bugs com severidade e evidências; valida as US antes do aceite do PO.                                 |
| **DevOps**             | Julio        | Mantém o pipeline de CI/CD (GitHub Actions), o ambiente local (Docker Compose) e o de homologação; executa testes, cobertura, análise estática e auditoria de dependências no pipeline; cuida de segredos (tokens do WhatsApp e das APIs de IA fora do repositório), monitoramento de disponibilidade, deploy e rollback. |
| **Desenvolvimento**    | Toda a equipe | Implementa as US, escreve testes unitários e de integração, revisa pull requests (mínimo de 1 revisão antes do merge) e corrige os bugs.                                                                                                                                                                                  |

Julio acumula PO e DevOps: não aceita nem revisa o próprio trabalho. O aceite de US feita por ele é testemunhado pelo SM.

| Release | PO     | SM     | QA     | DevOps |
| ------- | ------ | ------ | ------ | ------ |
| R1      | Nidlan | Rafael | Julio  | Rafael |
| R2      | Julio  | Nidlan | Rafael | Julio  |

## Como contribuir

Fluxo de branches, commits, PR e revisão em [`CONTRIBUTING.md`](CONTRIBUTING.md). Documentação do projeto (atas, planos, relatórios) em [`docs/`](docs/README.md).

## Execução local

Módulos: `backend/` (API FastAPI + WhatsApp + Gemini) e `frontend/` (painel React). O `docker-compose.yml` da raiz builda e sobe tudo:

```bash
cp .env.example .env            # preencha as chaves
docker compose up -d --build    # API :8000, painel :8081, Evolution :8080
docker compose exec api python -m app.seed   # cria o admin do painel
```

- **API:** detalhes em [`backend/README.md`](backend/README.md).
- **Painel em modo dev (React):**

```bash
cd frontend
npm ci
npm run dev                     # http://127.0.0.1:5173 (proxy para a API em :8000)
```

- **Testes da API** (Postgres de teste; Gemini e Evolution são mockados). ⚠️ Os testes **apagam e recriam as tabelas** do banco de `DATABASE_URL`: use um banco só para teste (`hortireg_test`), nunca o `sgv` de desenvolvimento. Passo a passo em [`backend/README.md`](backend/README.md):

```bash
cd backend
pip install -r requirements-dev.txt
# DATABASE_URL (banco de teste), JWT_SECRET, ADMIN_LOGIN e ADMIN_PASSWORD no ambiente
pytest                          # -m smoke | -m regressao | -m excecao
```
- **Pedido por áudio (US-06):** limites e variáveis (`AUDIO_MAX_SEGUNDOS`, `AUDIO_MAX_BYTES`, `AUDIO_TIMEOUT_SEGUNDOS`) em [`backend/README.md`](backend/README.md#pedido-por-áudio-us-06) e no `.env.example`.

- **E2E do painel:** com API e painel rodando, `cd frontend && ADMIN_LOGIN=... ADMIN_PASSWORD=... TAGS='@smoke' npx cypress run`.

