# Como contribuir

Fluxo de trabalho do HortiReg. Vale para código, testes e documentação. Acordos da equipe em [`docs/acordos-de-trabalho.md`](docs/acordos-de-trabalho.md).

## Branches

| Branch | Uso | Sai de | Volta para |
|---|---|---|---|
| `main` | Versão entregue em cada release (tag `vX.Y.Z`) | — | — |
| `develop` | Integração da sprint | `main` | `main` (PR de release) |
| `feature/SCRUM-<n>-<slug>` | US ou driver arquitetural | `develop` | `develop` |
| `fix/<slug>` | Correção de bug (cita `BUG-xx` e a issue) | `develop` | `develop` |
| `docs/<slug>` | Só documentação | `develop` | `develop` |
| `chore/<slug>`, `ci/<slug>` | Configuração, dependências, pipeline | `develop` | `develop` |
| `hotfix/<slug>` | Correção urgente na versão entregue | `main` | `main` e `develop` |

`<n>` é o número da issue no Jira (`SCRUM-32`). `<slug>` curto, minúsculo, com hífen.

`main` e `develop` são protegidas por ruleset: sem push direto, sem force push, sem exclusão, PR com 1 aprovação e checks do CI obrigatórios.

## Passo a passo

1. Mover o card no Jira para **In Progress** e criar a branch a partir da `develop` atualizada:
   ```sh
   git switch develop && git pull
   git switch -c feature/SCRUM-32-confirmacao
   ```
2. Commitar em português, no padrão Conventional Commits:
   ```
   feat(pedidos): confirma pedido com 1, 2 ou 3
   fix(webhook): rejeita evento sem token
   test(auth): cenário de bloqueio por tentativas
   docs(qa): atualiza casos de teste da Sprint 2
   ci: adiciona pip-audit
   ```
3. Rodar localmente antes do push (detalhes no [README](README.md#execução-local)):
   ```sh
   cd backend && ruff check . && pytest --cov=app --cov-fail-under=80
   cd frontend && npm run build
   ```
4. Abrir PR para a `develop` usando o modelo [`.github/pull_request_template.md`](.github/pull_request_template.md). Título no padrão do commit, com a chave do Jira (`feat(pedidos): ... (US-08, SCRUM-32)`).
5. Mover o card para **In Review** e pedir revisão a outra pessoa.
6. Merge só com **1 aprovação ("Approve")** e CI verde. Comentário sem aprovação não conta.
7. Merge por **merge commit** (não usar squash nem rebase), para manter commits e autores na `develop`.
8. Card vai para **Done** só quando a US atende à DoD: QA validou os critérios e o PO registrou o aceite na issue.

## Revisão

- Ninguém aprova o próprio PR nem aceita a própria US. Quem acumula papéis (PO e DevOps) tem o aceite testemunhado pelo SM.
- Prazo da primeira resposta do revisor: 1 dia útil.
- O revisor confere: critérios de aceite cobertos por teste, CI verde, ausência de segredos, docs atualizados.

## CI

`.github/workflows/ci.yml` roda em todo push e PR: gitleaks, bandit, pip-audit, npm audit, ruff, pytest (cobertura ≥ 80%) e Cypress. Push roda `@smoke`; PR roda `@smoke or @regressao` (sempre sem `@wip`).

Falha no CI bloqueia o merge. Quem abriu o PR corrige; falha do pipeline em si é com o DevOps.

## Issues e bugs

- US, bug e PR usam os modelos em [`.github/`](.github/). No Jira, preencher a versão (Fix Version) da release.
- Bug: passos para reproduzir, esperado × obtido, severidade (Plano de Teste §11) e evidência. Registrado no Jira com o tipo **Bug** (`BUG-xx`).

## Segredos

Nunca versionar `.env`, tokens ou senhas. Exemplos em `.env.example` só com placeholders. O gitleaks bloqueia o PR se encontrar segredo.
