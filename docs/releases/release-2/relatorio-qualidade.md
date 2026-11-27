# Relatório de qualidade · Release 2

QA: Rafael. **Situação: fechado para a Review da Sprint 3 (atualizado em 25/11/2026: `develop` `cc394bf`, PRs #13 a #26 mesclados; regressão final na seção 1). US-12 (PR #29) e SCRUM-51 (PR #30) entregues com CI verde, aguardando revisão.**

Este relatório traz também os resultados da R1, que não tinham sido medidos (feedback da R1). Base: Plano de Qualidade v1.1 e Plano de Teste v1.1. Casos e evidências: [`docs/qa/casos-de-teste.md`](../../qa/casos-de-teste.md).

## 1. Ciclo de regressão

| Data | Alvo | Comando | Resultado |
|---|---|---|---|
| 11/11 | `develop` (`3973c75`, release 1.0.0) | `pytest --cov=app --cov-fail-under=80` | 33/33 passaram, cobertura 91% |
| 11/11 | `feature/SCRUM-30-pedido-audio` (US-06) | idem | 59/59 local, cobertura 92%; **CI vermelho** (gitleaks, BUG-05) |
| 11/11 | `feature/webhook-token` | idem | 38/38 local, cobertura 91% |
| 11/11 | Integrado: `develop` + PRs #13, #14, #15 e #16 | `pytest -m regressao` / `-m smoke` / suíte completa | 43/43 · 11/11 · 44/44, cobertura 91,7%; `ruff` limpo |
| **12/11** | **`develop` integrada (`d1d8760`, PRs #13 a #21)** | **CI completo ([run 43144352377](https://github.com/Rafaelszc/HortiReg/actions/runs/43144352377))** | **75/75 passaram, cobertura 93,19%; `ruff` limpo; Cypress: todos os specs passaram; gitleaks, bandit, pip-audit e npm audit sem achados** |
| 12/11 | `develop` (`1d3ded2`, após PRs #22 a #25) | CI de push ([run 43205652714](https://github.com/Rafaelszc/HortiReg/actions/runs/43205652714)) | 77/77, cobertura 93,32%; Cypress `@smoke` verde; ruff e segurança limpos |
| 25/11 | PR #26 (SCRUM-53, fila com retentativa), antes do merge | CI de PR ([run 45539392921](https://github.com/Rafaelszc/HortiReg/actions/runs/45539392921)) | 84/84, cobertura 93,27%; Cypress `@smoke or @regressao` verde (4/4); gitleaks, bandit, pip-audit e npm audit sem achados |
| 25/11 | PR #29 (US-12, pedidos do dia) | CI de PR ([run 45689476387](https://github.com/Rafaelszc/HortiReg/actions/runs/45689476387)) | Suíte completa e Cypress `@regressao` verdes; local: 89 passed, cobertura 93,47%, Cypress 6/6 |
| 25/11 | PR #30 (SCRUM-51, deploy e rollback) | CI de PR ([run 45691331013](https://github.com/Rafaelszc/HortiReg/actions/runs/45691331013)) e ensaio ([run 45691331085](https://github.com/Rafaelszc/HortiReg/actions/runs/45691331085)) | Suíte verde (cobertura 93,28%); ensaio aprovado: 1,5 s fora do ar, rollback 32,4 s |
| **25/11** | **Regressão final da R2: `develop` `cc394bf` (com o #26) + docs, PR #27** | **CI de PR completo ([run 45684180353](https://github.com/Rafaelszc/HortiReg/actions/runs/45684180353)): `pytest --cov=app --cov-fail-under=80`, Cypress `(@smoke or @regressao) and not @wip`** | **84/84 passaram, cobertura 93,27%; Cypress 4/4; ruff, gitleaks, bandit, pip-audit e npm audit sem achados. Cobertura por arquivo: [`cobertura-regressao-final.txt`](cobertura-regressao-final.txt)** |

Ambiente: Postgres 16 descartável (`hortireg_test`), com Gemini e WhatsApp simulados (fixtures `llm_fake` e `whatsapp_fake`).

Não executado:
- Teste com WhatsApp real: a homologação local (PR #30) não inclui Evolution nem Gemini.
- Cypress local só nos PRs #29 e #30 (6/6); a regressão final do painel rodou no CI.

## 2. Bugs encontrados × corrigidos

Todos os bugs vieram do teste exploratório do QA em 11/11, com o reproduzível guardado como evidência. Severidade segue o Plano de Teste §11: bug de segurança tem no mínimo severidade Alta. Todos registrados no Jira (tipo Bug) em 12/11.

| ID | Jira | Bug | Severidade | US / CT | Situação |
|---|---|---|---|---|---|
| BUG-01 | SCRUM-71 | A IA devolve quantidade negativa e o resumo sai com "Valor estimado: R$ -13,00" | Alta | US-05 / CT-61 | Corrigido no PR #16 |
| BUG-02 | SCRUM-72 | Resposta diferente de SIM/NÃO com pedido pendente cria outro pedido; o primeiro fica órfão em AGUARDANDO_CONFIRMACAO | Média | US-08 / CT-18 | Corrigido no PR #13 |
| BUG-03 | SCRUM-73 | Se a IA falha num pedido por texto, o cliente não recebe resposta nenhuma e nada fica registrado | Média | DA-CONF-I3-01 / CT-54 | Corrigido: aviso ao cliente no PR #23 (12/11); gravação e retentativa no PR #26 (25/11). Retestado na regressão final |
| BUG-04 | SCRUM-74 | `POST /webhook/whatsapp` aceita evento forjado sem token (HTTP 200) e permite confirmar ou cancelar pedido de outro número | Alta | US-05 / CT-57 | Corrigido no PR #19 |
| BUG-05 | SCRUM-75 | O CI da branch da US-06 falha no gitleaks (`generic-api-key` em `backend/README.md:164`) e no ruff (`F401`) | Alta | US-06 / CT-13 | Corrigido no PR #18 (commit `54815d9`) |
| BUG-06 | SCRUM-76 | Reserva de 120 s da fila pode reprocessar a mensagem e duplicar o pedido | Baixa | DA-CONF-I3-01 / CT-54 | **Aberto** (backlog); achado na revisão do PR #26 |

**Total: 6 encontrados, 5 corrigidos e mesclados, 1 aberto (BUG-06, Baixa). Passos e evidências: [`docs/qa/Bugs_Sprint1_HortiReg.txt`](../../qa/Bugs_Sprint1_HortiReg.txt).**

BUG-06 (SCRUM-76): processamento acima de 120 s, ou queda do processo depois de criar o pedido, faz o laço reprocessar a mensagem e pode duplicar o pedido. Severidade: Baixa (timeouts da IA: 30 s no texto, 45 s no áudio).

Observação: versões antigas de `docs/qa/Bugs_Sprint1_HortiReg.txt` usavam os IDs BUG-01, BUG-02 e BUG-04 para defeitos sem evidência no código nem no histórico do Git (não há `CORSMiddleware`; o schema de produto usa `ge=0`, não `gt=0`). O arquivo foi reescrito em 25/11 com os IDs da tabela acima.

## 3. Métricas do plano de qualidade

N/M = não medido, com o motivo na observação.

| ID | Item | Meta | R1 | R2 (25/11, S3) | Observação |
|---|---|---|---|---|---|
| Q-01 | Cobertura de testes | ≥ 70% (proposta v1.1: ≥ 80%) | 91% | 93,27% (regressão final) | Atinge a meta; relatório salvo em `cobertura-regressao-final.txt` |
| Q-02 | Bugs críticos e altos abertos | 0 no fechamento | N/M (não existia o tipo Bug) | **0** | Atinge; único aberto é o BUG-06 (Baixa) |
| Q-03 | US com Gherkin de sucesso e exceção | 100% | 100% (US-01 a US-05) | 100% (US-06 a US-12) | Conferido nas issues |
| Q-04 | PRs integrados com ≥ 1 revisão | 100% | **0% (0 de 12)** | **57% com aprovação (8 de 14)** | Aprovados: #18, #19, #20, #22 a #26. Só com comentário: #13 a #17. Sem revisão: #21. Desde a proteção de `main` e `develop` (12/11), 100% dos PRs mesclados foram aprovados (#22 a #26) |
| Q-05 | CI verde na branch principal | ≥ 90% | `main` 100% (2/2); `develop` 71% (5/7) | `develop` 100% (5/5 concluídos) | Outros 3 runs foram cancelados por concorrência (substituídos pelo merge seguinte), não falharam |
| Q-06 | Precisão da extração da IA | ≥ 90% | N/M | N/M | Falta o conjunto de 50 áudios (SCRUM-47) |
| Q-07 | Pedidos duplicados em 1.000 mensagens | 0 | 0 (teste com 1 reenvio) | **0 (1.000 mensagens, 200 reenvios)** | PR #15 |
| Q-08 | Mensagens preservadas com a IA fora do ar | 100%; reprocessadas em ≤ 5 min | N/M | **100%** | `fila_retentativa.feature` "Falha de 30 minutos sem perder nenhuma mensagem" (3 clientes, reprocessadas em até 5 min), na regressão final (run 45684180353). Teste com IA simulada; falha real só em homologação |
| Q-09 | Disponibilidade de 05h a 18h | ≥ 95% em homologação | N/A | N/M | Sem homologação |
| Q-10 | Downtime por deploy e rollback | ≤ 60 s e ≤ 2 min | N/A | **Deploy: 2,5 s (local) / 1,5 s (CI). Rollback: 41,8 s / 32,4 s** | Homologação local (`deploy/`), PR #30; registro em `deploys-homologacao.csv`. Vale após o merge |
| Q-11 | Usabilidade | ver plano | N/M | N/M | Sessão com 5 a 10 pessoas pendente |
| Q-12 | Fluxos de exceção com mensagem tratada | 100% | 3 de 3 (US-05) | Áudio 7 de 7; texto 2 de 2 (IA fora do ar e IA lenta) | `pedido_audio.feature` (PR #18); `pedido.feature` `@excecao` (PR #23); fila: 2 cenários `@excecao` no PR #26 |
| Q-13 | Vulnerabilidades altas e críticas em dependências | 0 | 0 | 0 | pip-audit e npm audit no CI |
| Q-14 | Lint, bandit e segredos | 0 | 0 | 0 na `develop` | BUG-05 corrigido antes do merge |
| Q-15 | Previsibilidade da sprint | ≤ 20% | 0% (21 de 21 SP) | S2: 11% (16 de 18 SP); S3: N/M | Fonte: `docs/sm/sprints/sprint-*/metricas.txt` (SM). Sprint 3 sem métricas registradas |

### Conformidade com a frequência do plano

Confere se cada métrica foi medida na frequência da coluna "Frequência" do Plano de Qualidade v1.1.

| ID | Frequência no plano | Medido | Atende? | Ação |
|---|---|---|---|---|
| Q-01 | A cada push (CI) | Todo push no CI; relatório da regressão final salvo em `docs/releases/release-2/cobertura-regressao-final.txt` | Sim | Salvar o relatório a cada fechamento de release |
| Q-02 | Fim de cada sprint | S2 (12/11); S3 em 25/11 | Sim | Fechar na Review de 26/11 |
| Q-03 | Planning | Conferido pelo QA em 12/11, não na Planning | Parcial | Sem ata da Planning da Sprint 3 (`docs/sm/sprints/sprint-3/` não existe). PO e SM registrar |
| Q-04 | Fim de cada sprint | S2 e S3 | Sim | — |
| Q-05 | Fim de cada sprint | S2 e S3 | Sim | — |
| Q-06 | A cada release e a cada mudança de prompt | Nunca | **Não** | Prompt mudou na US-06 sem reavaliação; depende da SCRUM-47 |
| Q-07 | A cada push (CI) | `test_duplicidade_carga.py` roda em todo push | Sim | — |
| Q-08 | A cada release | R2 na regressão final | Sim | — |
| Q-09 | Semanal e por release | Nunca | **Não** | Homologação local só mede durante o deploy; sem monitor contínuo nem servidor acessível |
| Q-10 | A cada deploy (a partir da R2) | Todo deploy registra tempo fora do ar e rollback; ensaio em todo PR e push (workflow `deploy-homologacao.yml`) | Sim (após o merge do #30) | — |
| Q-11 | Releases 1, 2 e 4 | Nunca (R1 e R2) | **Não** | Sessão de usabilidade pendente (IMP-11) |
| Q-12 | A cada sprint | S1, S2 e S3 | Sim | — |
| Q-13 | A cada push e semanal | pip-audit e npm audit em todo push; Dependabot semanal (pip, npm, Actions) criado em 25/11 | Sim (após o merge do `.github/dependabot.yml`) | — |
| Q-14 | A cada push (CI) | ruff, bandit e gitleaks em todo push | Sim | — |
| Q-15 | Fim de cada sprint | S1 e S2 | Parcial | Falta a Sprint 3 (SM) |

Resumo: 10 atendem, 2 parciais (Q-03 e Q-15, do SM) e 3 não atendem (Q-06, Q-09, Q-11). As 3 que não atendem dependem de recurso externo (golden set, homologação, participantes). Registrar a justificativa na aba "Revisões" do plano ou ajustar a frequência na Retrospectiva.

### Execução dos casos (Plano de Teste §13)

| Métrica | Sprint 1 | Sprint 2 |
|---|---|---|
| Casos planejados para a sprint | 12 (CT-01 a CT-12) + CT-51, CT-59, CT-60 | 16 (CT-13 a CT-19b, CT-22 a CT-23b, CT-61) |
| Automatizados | 14 | 16 |
| Executados | 14 | 16 (+ CT-57, segurança) |
| Passaram / Falharam | 14 / 0 (CT-04 fora do escopo) | 16 / 0 (+ CT-57 passou) |
| Aprovação | 100% | 100% |
| Bugs abertos (crítico ou alto) | — | 0 |
| Drivers verificados (de 9) | 1 (DA-CONF-I2-01) | 1 (DA-CONF-I2-01, agora com 1.000 mensagens); DA-CONF-I3-01 reprovado (BUG-03) |

Sprint 3 (até 25/11):

| Métrica | Sprint 3 |
|---|---|
| Casos planejados | CT-15/16 (US-07), CT-20/20b/21 (US-09), CT-24/25/25b (US-11), CT-26/27 (US-12), CT-52 (SCRUM-51), CT-54 (SCRUM-53) |
| Automatizados e passando | CT-54 (7 cenários, PR #26); CT-56 texto (2 cenários, PR #23); CT-26/27 (3 cenários API + 2 Cypress, PR #29); CT-52 (ensaio, PR #30) |
| Não executados | CT-15/16, CT-20 a CT-21, CT-24 a CT-25b: `.feature` `@wip`, sem implementação das US-07, US-09 e US-11 |
| Drivers verificados | DA-CONF-I3-01 aprovado (PR #26); DA-USAB-I3-03 texto aprovado (PR #23); DA-DISP-I2-02 aprovado na homologação local (PR #30) |

## 4. Verificação da DoD por item entregue

Critérios da DoD de US: PR revisado · critérios validados pelo QA · testes passando · CI verde · homologação (se exigida) · docs · aceite do PO. Verificado pelo QA em 12/11.

| Item | PR revisado | Validado pelo QA | Testes | CI verde | Homologação | Docs | Aceite do PO | Veredito |
|---|---|---|---|---|---|---|---|---|
| US-01 (SCRUM-25) | Não (PR #2) | Sim | Sim | Sim | N/A | Sim | Não registrado | Done sem DoD completa |
| US-02 (SCRUM-26) | Não (PR #3) | Sim (CT-04 fora do escopo) | Sim | Sim | N/A | Sim | Não registrado | Done sem DoD completa |
| US-03 e US-04 (SCRUM-27 e 28) | Não (PR #9) | Sim | Sim | Sim | N/A | Sim | Não registrado | Done sem DoD completa |
| US-05 (SCRUM-29) | Não (PR #4) | Sim (BUG-01 e BUG-04 corrigidos na R2) | Sim | Sim | N/A | Sim | Não registrado | Done sem DoD completa |
| DA-CONF-I2-01 (SCRUM-50) | Não (PR #10) | Sim | Sim | Sim | N/A | Sim | Não registrado | Done sem DoD completa |
| DA-USAB-I2-03 (SCRUM-52) | Não (PR #9) | Não medido (CT-53) | Sim | Sim | N/A | Sim | Não registrado | Falta a medição |
| US-06 (SCRUM-30) | Sim (PR #18, aprovado) | Sim (CT-13, CT-14a a 14g) | Sim | Sim | Pendente (nota de voz real, sem ambiente) | Sim | Pendente (PO é o autor: aceite testemunhado pelo SM) | **Aguarda homologação e aceite** |
| US-08 (SCRUM-32) | Parcial (PR #13: revisão só comentada, sem aprovação) | Sim (CT-17 a CT-19b) | Sim | Sim | Pendente | Sim | Pendente | **Aguarda aceite** |
| US-10 (SCRUM-34) | Parcial (PR #14: revisão só comentada) | Sim (CT-22 a CT-23b) | Sim | Sim | Pendente | Sim | Pendente | **Aguarda aceite** |
| RK-02 (SCRUM-57) | Parcial (PR #15: revisão só comentada) | Sim (CT-51) | Sim | Sim | N/A | Sim | Pendente | **Aguarda aceite**; risco mitigado |
| RK-03 parcial (SCRUM-58) | Sim (PR #23, aprovado) | Sim (CT-56 texto) | Sim | Sim (run 43205652714) | N/A | Sim | Pendente | **Aguarda aceite** |
| DA-CONF-I3-01 (SCRUM-53) | Sim (PR #26, aprovado) | Sim (CT-54, 7 cenários) | Sim | Sim (run 45684180353) | N/A | Sim (`.env.example`, registro de riscos) | Pendente | **Aguarda aceite** |
| US-12 (SCRUM-36) | Pendente (PR #29) | Sim (CT-26, CT-27) | Sim | Sim (run 45689476387) | Pendente (homologação local disponível) | Sim | Pendente | **Aguarda revisão, merge e aceite** |
| DA-DISP-I2-02 (SCRUM-51) | Pendente (PR #30) | Sim (CT-52) | Sim | Sim (runs 45691331013 e 45691331085) | Sim (homologação local) | Sim (`deploy/README.md`) | Pendente | **Aguarda revisão, merge e aceite** |
| US-07, US-09, US-11 | Sem PR | Não (cenários `@wip`) | Não | — | — | — | — | **Não entregues**; voltam ao backlog |

Atenção: o checklist de DoD na descrição do PR #13 marca "Homologação com número real" e "Aceite do PO" como feitos. Não há ambiente de homologação nem aceite registrado na issue; vale o que está nesta tabela.

### DoD da Sprint 2: itens verificados pelo QA

Valores para a coluna "Sprint 2" da planilha `Definition_of_Done_HortiReg` (aba "DoD da Sprint").

| Nº | Critério | Sprint 2 | Evidência e observação |
|---|---|---|---|
| 2 | US concluídas atendem à DoD de US | Parcial | Código, testes e CI ok; faltam aceite do PO e homologação (seção 4) |
| 7 | Bugs da sprint registrados com evidência e severidade | Sim | SCRUM-71 a SCRUM-75 no Jira, com passos, esperado/obtido e PR |
| 8 | Nenhum bug crítico ou alto aberto sem plano | Sim | 0 alto aberto; BUG-03 (Média) com plano na SCRUM-53 |
| 9 | Regressão dos itens afetados executada | Sim | Seção 1 (12/11, `develop` integrada) |
| 21 | Gherkin da US automatizado e passando no CI | Sim | US-06, US-08, US-10 e RK-02 no run 43144352377 |
| 22 | Mensagens do bot revisadas (sem silêncio) | Não | BUG-03 |

### DoD da Sprint 3: itens verificados pelo QA (25/11, parcial)

| Nº | Critério | Sprint 3 | Evidência e observação |
|---|---|---|---|
| 2 | US concluídas atendem à DoD de US | Não | US-12 e SCRUM-51 com CI verde aguardam revisão e aceite; SCRUM-53 mesclado, aguarda aceite do PO |
| 7 | Bugs da sprint registrados com evidência e severidade | Sim | BUG-06 (SCRUM-76) com passos, causa e severidade |
| 8 | Nenhum bug crítico ou alto aberto sem plano | Sim | 0 alto aberto |
| 9 | Regressão dos itens afetados executada | Sim | Regressão final de 25/11, run 45684180353 (seção 1) |
| 21 | Gherkin da US automatizado e passando no CI | Sim | `fila_retentativa.feature` no run 45684180353 |
| 22 | Mensagens do bot revisadas (sem silêncio) | Sim | Texto: PR #23; fila: aviso "em processamento" e aviso final (PR #26) |

## 5. Ações para fechar a R2

1. ~~Proteger `main` e `develop`~~ (feito em 12/11). Falta: bypass só para emergência, merge só por merge commit e revisão com "Approve" (comentário não conta). Responsável: DevOps.
2. ~~Abrir os PRs da US-06 e do token e corrigir o BUG-05~~ (feito: PRs #18 e #19 mesclados).
3. Registrar o aceite do PO nas issues (US-06 com o SM como testemunha) e preencher a planilha de DoD com os valores da seção 4. Responsáveis: PO e QA.
4. ~~Aprovar e mesclar o PR #26, fechar o BUG-03 e confirmar o Q-08~~ (feito em 25/11). Issue da reserva aberta (SCRUM-76). Falta: mudar o BUG-03 (SCRUM-73) para Done no Jira. Responsáveis: Julio e QA.
5. Homologar US-06, US-08 e US-10 com número real quando o ambiente existir (SCRUM-51). Responsável: DevOps.
6. ~~Confirmar ou retirar os bugs de `docs/qa/Bugs_Sprint1_HortiReg.txt`~~ (feito em 25/11: reescrito com os IDs válidos).
7. ~~Antes da Review da Sprint 3: regressão completa na `develop` integrada~~ (feito em 25/11, run 45684180353).
8. Registrar a ata da Planning da Sprint 3 e as métricas da Sprint 3 (Q-03 e Q-15). Responsável: SM.
9. Revisar e mesclar os PRs #29 (US-12) e #30 (SCRUM-51); depois rodar `deploy/deploy.sh` na `develop` para registrar o primeiro deploy da R2. Responsável: QA e revisor.
10. Mesclar o `.github/dependabot.yml` (Q-13 semanal) e acompanhar os PRs que ele abrir. Responsável: DevOps.
