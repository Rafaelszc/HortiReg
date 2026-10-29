## Papéis e responsabilidades (Release 1)

| Papel                  | Responsável   | Responsabilidades                                                                                                                                                                                                                                                                                                         |
| ---------------------- | ------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **PO (Product Owner)** | Nidlan        | Mantém e prioriza o Product Backlog; escreve e valida as US e os critérios de aceite em Gherkin; define a meta de cada release; fornece as amostras de áudio e texto do conjunto de referência da IA; aceita ou rejeita cada US na Sprint Review; valida os drivers arquiteturais.                                        |
| **SM (Scrum Master)**  | Rafael        | Facilita Planning, Daily, Review e Retrospectiva; remove impedimentos; mantém a Definition of Done e o board atualizados; acompanha velocity, burndown e a planilha de riscos; registra os papéis da próxima release neste README.                                                                                        |
| **QA (Qualidade)**     | Júlio         | Conduz o Plano de Qualidade e o Plano de Teste; escreve os `.feature` e automatiza os cenários (Cypress e pytest-bdd); executa testes exploratórios e de usabilidade; verifica os 9 drivers arquiteturais; registra bugs com severidade e evidências; valida as US antes do aceite do PO.                                 |
| **DevOps**             | Rafael        | Mantém o pipeline de CI/CD (GitHub Actions), o ambiente local (Docker Compose) e o de homologação; executa testes, cobertura, análise estática e auditoria de dependências no pipeline; cuida de segredos (tokens do WhatsApp e das APIs de IA fora do repositório), monitoramento de disponibilidade, deploy e rollback. |
| **Desenvolvimento**    | Toda a equipe | Implementa as US, escreve testes unitários e de integração, revisa pull requests (mínimo de 1 revisão antes do merge) e corrige os bugs.                                                                                                                                                                                  |

## Execução local

- **API (FastAPI + WhatsApp + Gemini):** ver [`sgv-wa/sgv-wa/README.md`](sgv-wa/sgv-wa/README.md). Depois de `docker compose up -d`, crie o admin do painel com `docker compose exec api python -m app.seed`.
- **Painel (React):**

```bash
cd frontend
npm ci
npm run dev                     # http://127.0.0.1:5173 (proxy para a API em :8000)
```

- **Testes da API** (Postgres de teste; Gemini e Evolution são mockados):

```bash
cd sgv-wa/sgv-wa
pip install -r requirements-dev.txt
pytest                          # -m smoke | -m regressao
```

- **E2E do painel:** com API e painel rodando, `cd frontend && ADMIN_LOGIN=... ADMIN_PASSWORD=... TAGS='@smoke' npx cypress run`.

