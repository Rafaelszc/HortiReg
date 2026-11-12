# Relatório de qualidade · Release 2

QA: Rafael. **Situação: parcial, ao fim da Sprint 2 (atualizado em 12/11/2026, após o merge dos PRs #13 a #21).** Será fechado na Review da Sprint 3 (26/11/2026), com a regressão final antes da apresentação.

Este relatório traz também os resultados da R1, que não tinham sido medidos (feedback da R1). Base: Plano de Qualidade v1.1 e Plano de Teste v1.1. Casos e evidências: [`docs/qa/casos-de-teste.md`](../../qa/casos-de-teste.md).

## 1. Ciclo de regressão

| Data | Alvo | Comando | Resultado |
|---|---|---|---|
| 11/11 | `develop` (`3973c75`, release 1.0.0) | `pytest --cov=app --cov-fail-under=80` | 33/33 passaram, cobertura 91% |
| 11/11 | `feature/SCRUM-30-pedido-audio` (US-06) | idem | 59/59 local, cobertura 92%; **CI vermelho** (gitleaks, BUG-05) |
| 11/11 | `feature/webhook-token` | idem | 38/38 local, cobertura 91% |
| 11/11 | Integrado: `develop` + PRs #13, #14, #15 e #16 | `pytest -m regressao` / `-m smoke` / suíte completa | 43/43 · 11/11 · 44/44, cobertura 91,7%; `ruff` limpo |
| **12/11** | **`develop` integrada (`d1d8760`, PRs #13 a #21)** | **CI completo ([run 43144352377](https://github.com/Rafaelszc/HortiReg/actions/runs/43144352377))** | **75/75 passaram, cobertura 93,19%; `ruff` limpo; Cypress: todos os specs passaram; gitleaks, bandit, pip-audit e npm audit sem achados** |

Ambiente: Postgres 16 descartável (`hortireg_test`), com Gemini e WhatsApp simulados (fixtures `llm_fake` e `whatsapp_fake`).

Não executado:
- Teste com WhatsApp real (homologação), porque o ambiente ainda não existe.
- Cypress local; os cenários do painel rodam no CI.

## 2. Bugs encontrados × corrigidos

Todos os bugs vieram do teste exploratório do QA em 11/11, com o reproduzível guardado como evidência. Severidade segue o Plano de Teste §11: bug de segurança tem no mínimo severidade Alta. Todos registrados no Jira (tipo Bug) em 12/11.

| ID | Jira | Bug | Severidade | US / CT | Situação |
|---|---|---|---|---|---|
| BUG-01 | SCRUM-71 | A IA devolve quantidade negativa e o resumo sai com "Valor estimado: R$ -13,00" | Alta | US-05 / CT-61 | Corrigido no PR #16 |
| BUG-02 | SCRUM-72 | Resposta diferente de SIM/NÃO com pedido pendente cria outro pedido; o primeiro fica órfão em AGUARDANDO_CONFIRMACAO | Média | US-08 / CT-18 | Corrigido no PR #13 |
| BUG-03 | SCRUM-73 | Se a IA falha num pedido por texto, o cliente não recebe resposta nenhuma e nada fica registrado | Média | DA-CONF-I3-01 / CT-54 | **Aberto**; tratar com a SCRUM-53 (Sprint 3) |
| BUG-04 | SCRUM-74 | `POST /webhook/whatsapp` aceita evento forjado sem token (HTTP 200) e permite confirmar ou cancelar pedido de outro número | Alta | US-05 / CT-57 | Corrigido no PR #19 |
| BUG-05 | SCRUM-75 | O CI da branch da US-06 falha no gitleaks (`generic-api-key` em `backend/README.md:164`) e no ruff (`F401`) | Alta | US-06 / CT-13 | Corrigido no PR #18 (commit `54815d9`) |

**Total: 5 encontrados, 4 corrigidos e mesclados, 1 aberto (severidade Média).**

Observação: `docs/qa/Bugs_Sprint1_HortiReg.txt` usa os IDs BUG-01 e BUG-02 para dois defeitos da R1 (CORS e preço ≤ 0) que não têm evidência no código nem no histórico do Git (não há `CORSMiddleware`; o schema de produto usa `ge=0`, não `gt=0`). Esses itens não entram neste relatório até o QA da R1 confirmar. Os IDs válidos são os da tabela acima.

## 3. Métricas do plano de qualidade

N/M = não medido, com o motivo na observação.

| ID | Item | Meta | R1 | R2 (parcial, S2) | Observação |
|---|---|---|---|---|---|
| Q-01 | Cobertura de testes | ≥ 70% (proposta v1.1: ≥ 80%) | 91% | 93,19% | Atinge a meta |
| Q-02 | Bugs críticos e altos abertos | 0 no fechamento | N/M (não existia o tipo Bug) | **0** | Atinge; único aberto é o BUG-03 (Média) |
| Q-03 | US com Gherkin de sucesso e exceção | 100% | 100% (US-01 a US-05) | 100% (US-06 a US-12) | Conferido nas issues |
| Q-04 | PRs integrados com ≥ 1 revisão | 100% | **0% (0 de 12)** | **33% com aprovação (3 de 9)** | Aprovados: #18, #19, #20. Só com comentário: #13 a #17. Sem revisão: #21. Proteção de `main` e `develop` ativada em 12/11, com bypass ativo |
| Q-05 | CI verde na branch principal | ≥ 90% | `main` 100% (2/2); `develop` 71% (5/7) | `develop` 100% (4/4 concluídos) | Outros 3 runs foram cancelados por concorrência (substituídos pelo merge seguinte), não falharam |
| Q-06 | Precisão da extração da IA | ≥ 90% | N/M | N/M | Falta o conjunto de 50 áudios (SCRUM-47) |
| Q-07 | Pedidos duplicados em 1.000 mensagens | 0 | 0 (teste com 1 reenvio) | **0 (1.000 mensagens, 200 reenvios)** | PR #15 |
| Q-08 | Mensagens preservadas com a IA fora do ar | 100% | N/M | **0% no texto** (BUG-03) | Fila e retentativa: SCRUM-53 |
| Q-09 | Disponibilidade de 05h a 18h | ≥ 95% em homologação | N/A | N/M | Sem homologação |
| Q-10 | Downtime por deploy e rollback | ≤ 60 s e ≤ 2 min | N/A | N/M | SCRUM-51 sem ambiente |
| Q-11 | Usabilidade | ver plano | N/M | N/M | Sessão com 5 a 10 pessoas pendente |
| Q-12 | Fluxos de exceção com mensagem tratada | 100% | 3 de 3 (US-05) | Parcial: áudio 7 de 7; texto falha (BUG-03) | `pedido_audio.feature` no PR #18 |
| Q-13 | Vulnerabilidades altas e críticas em dependências | 0 | 0 | 0 | pip-audit e npm audit no CI |
| Q-14 | Lint, bandit e segredos | 0 | 0 | 0 na `develop` | BUG-05 corrigido antes do merge |
| Q-15 | Previsibilidade da sprint | ≤ 20% | — | — | Responsabilidade do SM |

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

## 5. Ações para fechar a R2

1. ~~Proteger `main` e `develop`~~ (feito em 12/11). Falta: bypass só para emergência, merge só por merge commit e revisão com "Approve" (comentário não conta). Responsável: DevOps.
2. ~~Abrir os PRs da US-06 e do token e corrigir o BUG-05~~ (feito: PRs #18 e #19 mesclados).
3. Registrar o aceite do PO nas issues (US-06 com o SM como testemunha) e preencher a planilha de DoD com os valores da seção 4. Responsáveis: PO e QA.
4. Fechar o BUG-03 junto com a SCRUM-53 e medir o Q-08. Responsáveis: Julio e QA.
5. Homologar US-06, US-08 e US-10 com número real quando o ambiente existir (SCRUM-51). Responsável: DevOps.
6. Confirmar ou retirar os bugs de `docs/qa/Bugs_Sprint1_HortiReg.txt`. Responsáveis: Julio (QA da R1) e Nidlan.
7. Antes da Review da Sprint 3: regressão completa (`pytest` e Cypress `@regressao`) na `develop` integrada, registrada aqui. Responsável: QA.
