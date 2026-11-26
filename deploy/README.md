# Homologação local: deploy com rollback (SCRUM-51 / DA-DISP-I2-02)

Homologação roda na máquina do DevOps/QA com Docker Compose (decisão de 25/11/2026: não há servidor da equipe).
Sobe Postgres, API e painel com imagens marcadas pela versão. Evolution e Gemini não entram: o objetivo é validar deploy, healthcheck e rollback.

| Comando | O que faz |
|---|---|
| `deploy/deploy.sh [VERSAO]` | Constrói as imagens, troca API e painel e espera o `/health` com a nova versão e o painel respondendo, estáveis por 3 s (`ESTAVEL`) sem reinício de container. Se não ficar saudável em 30 s (`ESPERA_HEALTH`), volta para a versão anterior e sai com código 1 (2 se o rollback falhar). Toda execução após a primeira vai para o registro |
| `FALHA_INJETADA=1\|api\|painel deploy/deploy.sh VERSAO` | Sobe a versão com falha para testar o rollback: `1` banco inacessível (simula migração quebrada), `api` comando inexistente na API, `painel` painel que encerra na partida |
| `deploy/ensaio-rollback.sh` | Ensaio do CT-52: deploy normal + as três falhas. Aprova se cada deploy ficar ≤ 60 s fora do ar (também os com falha), cada rollback ≤ 2 min e a versão anterior continuar no ar |

- O ensaio usa o mesmo projeto Compose (`hortireg-homolog`): se a homologação estiver no ar, ela é trocada pela versão do ensaio.
- Portas: API em `127.0.0.1:8001` (`/health` devolve `versao`), painel em `127.0.0.1:8091`.
- Segredos: `deploy/homologacao.env` é gerado na primeira execução a partir do `.example` (não versionado). A senha do admin fica nesse arquivo; para criar a conta: `VERSAO=$(cat deploy/.versao-atual) docker compose -f deploy/docker-compose.homologacao.yml --env-file deploy/homologacao.env exec api python -m app.seed`.
- Medição: um monitor consulta o `/health` e o painel a cada 0,5 s durante o deploy (fora do ar = qualquer um sem resposta). Cada execução vira uma linha em `deploy/registro-deploys.csv` (data, versão, anterior, falha injetada, resultado, segundos fora do ar, segundos até o rollback).
- CI: `.github/workflows/deploy-homologacao.yml` roda o ensaio em PR e push na `develop`/`main` e publica o registro como artefato.
- Derrubar: `VERSAO=x docker compose -f deploy/docker-compose.homologacao.yml --env-file deploy/homologacao.env down` (com `-v` apaga o banco).

Limitação: o ambiente não é acessível pela equipe nem monitorado fora do deploy (Q-09 continua sem medição).
