# Homologação local: deploy com rollback (SCRUM-51 / DA-DISP-I2-02)

Homologação roda na máquina do DevOps/QA com Docker Compose (decisão de 25/11/2026: não há servidor da equipe).
Sobe Postgres, API e painel com imagens marcadas pela versão. Evolution e Gemini não entram: o objetivo é validar deploy, healthcheck e rollback.

| Comando | O que faz |
|---|---|
| `deploy/deploy.sh [VERSAO]` | Constrói as imagens, troca API e painel e espera o `/health` com a nova versão. Se não responder em 30 s (`ESPERA_HEALTH`), volta para a versão anterior e sai com código 1 |
| `FALHA_INJETADA=1 deploy/deploy.sh VERSAO` | Sobe a versão com banco inacessível (simula migração quebrada) para testar o rollback |
| `deploy/ensaio-rollback.sh` | Ensaio do CT-52: deploy normal + deploy com falha. Aprova se ≤ 60 s fora do ar e rollback ≤ 2 min |

- Portas: API em `127.0.0.1:8001` (`/health` devolve `versao`), painel em `127.0.0.1:8091`.
- Segredos: `deploy/homologacao.env` é gerado na primeira execução a partir do `.example` (não versionado). A senha do admin fica nesse arquivo; para criar a conta: `VERSAO=$(cat deploy/.versao-atual) docker compose -f deploy/docker-compose.homologacao.yml --env-file deploy/homologacao.env exec api python -m app.seed`.
- Medição: um monitor consulta o `/health` a cada 0,5 s durante o deploy. Cada execução vira uma linha em `deploy/registro-deploys.csv` (data, versão, anterior, falha injetada, resultado, segundos fora do ar, segundos até o rollback).
- CI: `.github/workflows/deploy-homologacao.yml` roda o ensaio em PR e push na `develop`/`main` e publica o registro como artefato.
- Derrubar: `VERSAO=x docker compose -f deploy/docker-compose.homologacao.yml --env-file deploy/homologacao.env down` (com `-v` apaga o banco).

Limitação: o ambiente não é acessível pela equipe nem monitorado fora do deploy (Q-09 continua sem medição).
