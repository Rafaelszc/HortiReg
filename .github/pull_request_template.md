## O que muda

<!-- Uma ou duas frases. -->

## Rastreabilidade

- Jira: SCRUM-
- US / CT / BUG: <!-- ex.: US-08, CT-21, BUG-01 -->

## Como testar

<!-- Comandos ou passos. Ex.: `pytest -k "confirmação"`, cenário Cypress, fluxo no WhatsApp. -->

## Checklist (DoD)

- [ ] Branch `feature/SCRUM-<n>-<slug>` (ou `fix/`, `docs/`) saindo de `develop`
- [ ] Critérios de aceite (Gherkin) cobertos por teste
- [ ] CI verde (gitleaks, bandit, pip-audit, npm audit, ruff, pytest ≥ 80% cobertura, Cypress)
- [ ] Sem segredo no código, nos docs ou no `.env.example`
- [ ] README/docs atualizados, se mudou setup, rota ou comportamento
- [ ] Rota nova usada pelo painel incluída em `frontend/nginx.conf` e `frontend/vite.config.ts`
- [ ] Card do Jira em In Review
- [ ] Pelo menos 1 revisão aprovada antes do merge (merge commit, não squash)
