# Relatório de qualidade · Release 2

QA: Rafael. **Situação: parcial, ao fim da Sprint 2 (11/11/2026).** Será fechado na Review da Sprint 3 (26/11/2026), com a regressão final antes da apresentação.

Este relatório traz também os resultados da R1, que não tinham sido medidos (feedback da R1). Base: Plano de Qualidade v1.1 e Plano de Teste v1.1. Casos e evidências: [`docs/qa/casos-de-teste.md`](../../qa/casos-de-teste.md).

## 1. Ciclo de regressão

| Data | Alvo | Comando | Resultado |
|---|---|---|---|
| 11/11 | `develop` (`3973c75`, release 1.0.0) | `pytest --cov=app --cov-fail-under=80` | 33/33 passaram, cobertura 91% |
| 11/11 | `feature/SCRUM-30-pedido-audio` (US-06) | idem | 59/59 local, cobertura 92%; **CI vermelho** (gitleaks, BUG-05) |
| 11/11 | `feature/webhook-token` | idem | 38/38 local, cobertura 91% |
| 11/11 | Integrado: `develop` + PRs #13, #14, #15 e #16 | `pytest -m regressao` / `-m smoke` / suíte completa | 43/43 · 11/11 · **44/44**, cobertura 91,7%; `ruff` limpo |
| 11/11 | Painel (Cypress `@smoke or @regressao`) | Job `frontend` do CI nos PRs #13 a #16 | Ver o CI de cada PR |

Ambiente: Postgres 16 descartável (`hortireg_test`), com Gemini e WhatsApp simulados (fixtures `llm_fake` e `whatsapp_fake`).

Não executado:
- Teste com WhatsApp real (homologação), porque o ambiente ainda não existe.
- Cypress local; os cenários do painel rodam no CI.

## 2. Bugs encontrados × corrigidos

Todos os bugs vieram do teste exploratório do QA em 11/11, com o reproduzível guardado como evidência. Severidade segue o Plano de Teste §11: bug de segurança tem no mínimo severidade Alta.

| ID | Bug | Severidade | US / CT | Situação |
|---|---|---|---|---|
| BUG-01 | A IA devolve quantidade negativa e o resumo sai com "Valor estimado: R$ -13,00" | Alta | US-05 / CT-61 | Corrigido no PR #16 |
| BUG-02 | Resposta diferente de SIM/NÃO com pedido pendente cria outro pedido; o primeiro fica órfão em AGUARDANDO_CONFIRMACAO | Média | US-08 / CT-18 | Corrigido no PR #13 |
| BUG-03 | Se a IA falha num pedido por texto, o cliente não recebe resposta nenhuma e nada fica registrado | Média | DA-CONF-I3-01 / CT-54 | Aberto, tratar com a SCRUM-53 (Sprint 3) |
| BUG-04 | `POST /webhook/whatsapp` aceita evento forjado sem token (HTTP 200) e permite confirmar ou cancelar pedido de outro número | Alta | US-05 / CT-57 | Aberto; correção em `feature/webhook-token`, falta abrir o PR |
| BUG-05 | O CI da branch da US-06 falha no gitleaks (`generic-api-key` em `backend/README.md:164`); a US está Done no Jira sem merge | Alta | US-06 / CT-13 | Aberto |

**Total: 5 encontrados, 2 corrigidos (em PR), 3 abertos (2 com severidade Alta).**

## 3. Métricas do plano de qualidade

N/M = não medido, com o motivo na observação.

| ID | Item | Meta | R1 | R2 (parcial, S2) | Observação |
|---|---|---|---|---|---|
| Q-01 | Cobertura de testes | ≥ 70% (proposta v1.1: ≥ 80%) | 91% | 91,7% | Atinge a meta |
| Q-02 | Bugs críticos e altos abertos | 0 no fechamento | N/M (não existia o tipo Bug) | 2 (BUG-04, BUG-05) | Fora da meta; os dois têm plano |
| Q-03 | US com Gherkin de sucesso e exceção | 100% | 100% (US-01 a US-05) | 100% (US-06 a US-12) | Conferido nas issues |
| Q-04 | PRs integrados com ≥ 1 revisão | 100% | **0% (0 de 12)** | 0 integrados até agora | `main` e `develop` sem proteção de branch |
| Q-05 | CI verde na branch principal | ≥ 90% | `main` 100% (2/2); `develop` 71% (5/7) | — | Falhas na `develop` em 27/10 e 29/10 |
| Q-06 | Precisão da extração da IA | ≥ 90% | N/M | N/M | Falta o conjunto de 50 áudios (SCRUM-47) |
| Q-07 | Pedidos duplicados em 1.000 mensagens | 0 | 0 (teste com 1 reenvio) | **0 (1.000 mensagens, 200 reenvios)** | PR #15 |
| Q-08 | Mensagens preservadas com a IA fora do ar | 100% | N/M | **0% no texto** (BUG-03) | Fila e retentativa: SCRUM-53 |
| Q-09 | Disponibilidade de 05h a 18h | ≥ 95% em homologação | N/A | N/M | Sem homologação |
| Q-10 | Downtime por deploy e rollback | ≤ 60 s e ≤ 2 min | N/A | N/M | SCRUM-51 sem ambiente |
| Q-11 | Usabilidade | ver plano | N/M | N/M | Sessão com 5 a 10 pessoas pendente |
| Q-12 | Fluxos de exceção com mensagem tratada | 100% | 3 de 3 (US-05) | Parcial: falha BUG-03 | Áudio coberto na branch da US-06 |
| Q-13 | Vulnerabilidades altas e críticas em dependências | 0 | 0 | 0 | pip-audit e npm audit no CI |
| Q-14 | Lint, bandit e segredos | 0 | 0 | **1** (gitleaks, BUG-05) | Na branch da US-06 |
| Q-15 | Previsibilidade da sprint | ≤ 20% | — | — | Responsabilidade do SM |

### Execução dos casos (Plano de Teste §13)

| Métrica | Sprint 1 | Sprint 2 |
|---|---|---|
| Casos planejados para a sprint | 12 (CT-01 a CT-12) + CT-51, CT-59, CT-60 | 16 (CT-13 a CT-19b, CT-22 a CT-23b, CT-61) |
| Automatizados | 14 | 16 |
| Executados | 14 | 16 |
| Passaram / Falharam | 14 / 0 (CT-04 fora do escopo) | 8 / 0; 8 bloqueados (US-06, BUG-05) |
| Aprovação | 100% | 100% dos executáveis |
| Bugs abertos (crítico ou alto) | — | 2 |
| Drivers verificados (de 9) | 1 (DA-CONF-I2-01) | 1 (DA-CONF-I2-01, agora com 1.000 mensagens); DA-CONF-I3-01 reprovado |

## 4. Verificação da DoD por item entregue

Critérios da DoD de US: PR revisado · critérios validados pelo QA · testes passando · CI verde · homologação (se exigida) · docs · aceite do PO. Verificado pelo QA em 11/11.

| Item | PR revisado | Validado pelo QA | Testes | CI verde | Homologação | Docs | Aceite do PO | Veredito |
|---|---|---|---|---|---|---|---|---|
| US-01 (SCRUM-25) | Não (PR #2) | Sim | Sim | Sim | N/A | Sim | Não registrado | Done sem DoD completa |
| US-02 (SCRUM-26) | Não (PR #3) | Sim (CT-04 fora do escopo) | Sim | Sim | N/A | Sim | Não registrado | Done sem DoD completa |
| US-03 e US-04 (SCRUM-27 e 28) | Não (PR #9) | Sim | Sim | Sim | N/A | Sim | Não registrado | Done sem DoD completa |
| US-05 (SCRUM-29) | Não (PR #4) | Parcial (BUG-01 e BUG-04 abertos na época) | Sim | Sim | N/A | Sim | Não registrado | Done sem DoD completa |
| DA-CONF-I2-01 (SCRUM-50) | Não (PR #10) | Sim | Sim | Sim | N/A | Sim | Não registrado | Done sem DoD completa |
| DA-USAB-I2-03 (SCRUM-52) | Não (PR #9) | Não medido (CT-53) | Sim | Sim | N/A | Sim | Não registrado | Falta a medição |
| **US-06 (SCRUM-30)** | **Sem PR** | Sim, local (59/59) | Sim | **Não** (gitleaks) | Pendente (nota de voz real) | Sim | Não | **Não atende: deve voltar para In Progress** |
| US-08 (SCRUM-32) | Aguardando revisão (PR #13) | Sim (CT-17 a CT-19b) | Sim | Aguardando CI | Pendente | Sim | Pendente | Em revisão |
| US-10 (SCRUM-34) | Aguardando revisão (PR #14) | Sim (CT-22 a CT-23b) | Sim | Aguardando CI | Pendente | Sim | Pendente (prazo de 30 min) | Em revisão |
| RK-02 (SCRUM-57) | Aguardando revisão (PR #15) | Sim (CT-51) | Sim | Aguardando CI | N/A | Sim | Pendente | Em revisão; risco mitigado |

## 5. Ações para fechar a R2

1. Proteger `main` e `develop`, exigindo 1 aprovação e CI verde. Responsável: DevOps.
2. Abrir os PRs da US-06 e do token do webhook e resolver o conflito entre eles. Corrigir o BUG-05 trocando o exemplo do README por um placeholder. Responsável: Julio.
3. Registrar o aceite do PO nas issues e preencher a planilha de DoD com os valores da seção 4. Responsáveis: PO e QA.
4. Fechar o BUG-03 junto com a SCRUM-53 e medir o Q-08. Responsáveis: Julio e QA.
5. Antes da Review da Sprint 3: regressão completa (`pytest` e Cypress `@regressao`) na `develop` integrada, registrada aqui. Responsável: QA.
