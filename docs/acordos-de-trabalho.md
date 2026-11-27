# Acordos de trabalho da equipe

> **Proposta de 11/11/2026, a validar pela equipe** na Planning ou na Retrospectiva. Depois de aprovada, registre a data e os nomes em "Aprovação" e registre mudanças futuras no histórico da DoD (planilha `Definition_of_Done_HortiReg`, aba "Acordo da equipe").

## Papéis (Release 2)

Os papéis vigentes ficam no [README.md](../README.md#papéis-e-responsabilidades-release-2). Quem acumula papéis (Julio é PO e DevOps) **não aceita nem revisa o próprio trabalho**: o aceite do PO de uma US feita por ele é testemunhado pelo SM, e o PR é revisado por outra pessoa.

## Cerimônias (detalhe e modelo em [`docs/sprints/_modelo-ata.md`](sprints/_modelo-ata.md))

| Cerimônia | Timebox | Quando | Registro |
|---|---|---|---|
| Sprint Planning | 2 h | 1º dia útil da sprint | Ata em `docs/sprints/` |
| Daily | 15 min | Diária, horário fixo combinado pela equipe: `[definir]` | Impedimentos e mudanças de escopo na ata |
| Sprint Review | 1 h | Último dia da sprint | Ata + aceite de cada US nas issues |
| Retrospectiva | 1 h 30 | Logo após a Review | Ata com ações, responsáveis e prazos |

## Trabalho e Jira

1. **Branches** `feature/SCRUM-<n>-<slug>` saem da `develop`. Commits Conventional, em português.
2. **PR** para a `develop` com **1 revisão mínima** de outra pessoa; merge por **merge commit**. Prazo para a primeira resposta do revisor: 1 dia útil.
3. **Estimativa:** o campo de story points só muda com reestimativa justificada em comentário na issue. Zerar ou editar pontos para "mostrar progresso" distorce burndown e velocity: o progresso é a issue ir para Done.
4. **Escopo da sprint:** adicionar ou retirar um item depois da Planning exige comentário na issue (data, motivo, quem decidiu) e linha na tabela de mudanças de escopo da ata. Retirar uma US no último dia só com registro de impedimento.
5. **Impedimentos:** registrar no mesmo dia (label `impedimento` na issue + tabela da ata), com responsável pela remoção. O SM acompanha e cobra a resolução.
6. **Status da issue:** "In Progress" só com trabalho em andamento (branch ou commit); "Ready" só quando atende à DoR; "Done" só quando atende à DoD.
7. **Equilíbrio:** na Planning, nenhum integrante deve ficar com mais de 40% dos pontos comprometidos, nem com menos de 25% (a menos que haja justificativa registrada). A divisão realizada é conferida na Retrospectiva.
8. **Riscos:** revisar a planilha de riscos em toda Planning e Retrospectiva (probabilidade, severidade, providências). Riscos com providência na sprint ganham comentário na issue ao serem tratados.
9. **Segredos:** nunca no repositório (`.env` fora do Git). Testes só rodam contra banco de teste separado (`hortireg_test`), nunca contra o `sgv` de desenvolvimento.
10. **Documentação:** quem muda comportamento atualiza o README e o plano de testes (casos novos, arquivo e status) no mesmo PR ou na mesma sprint.

## Aprovação

| Nome | Papel | Data | De acordo |
|---|---|---|---|
| Julio | PO e DevOps | | |
| Nidlan | SM | | |
| Rafael | QA | | |
