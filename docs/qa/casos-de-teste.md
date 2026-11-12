# Casos de teste e rastreabilidade

QA: Rafael (Release 2). Fonte dos IDs: Plano de Teste v1.1, seção 8. Atualizado em 12/11/2026 (regressão na `develop` `d1d8760`: 75 testes, cobertura 93,19%, Cypress verde).

Cada caso aponta para a US (issue do Jira), para o cenário automatizado que o verifica e para a última execução. O cenário passando no CI é a evidência do critério de aceite. Os arquivos de teste ficam em:

- API e bot: `backend/tests/features/*.feature`, com os passos em `backend/tests/test_*.py`.
- Painel: `frontend/cypress/e2e/*.feature`.

**Status:** Especificado: `.feature` escrito pelo QA com `@wip` (não roda no CI), aguardando os passos · Passou (CI) · Passou (local): ainda não está na `develop` · Falhou: tem bug aberto · Bloqueado · Pendente: a US ainda não foi feita · Manual.

## Release 1 (Sprint 1)

| CT | US / issue | Cenário automatizado | Status | Evidência |
|---|---|---|---|---|
| CT-01 | US-01 / SCRUM-25 | Job `backend` do `ci.yml` (PR com testes passando) | Passou (CI) | Runs verdes na `main` (2/2) |
| CT-02 | US-01 / SCRUM-25 | Jobs `security` (bandit, pip-audit, npm audit) e `backend` | Passou (CI) | O pipeline barrou a branch da US-06 (BUG-05 / SCRUM-75) |
| CT-03 | US-02 / SCRUM-26 | `login.feature` "Login do administrador com credenciais válidas"; Cypress `login.feature` "Login com credenciais válidas" | Passou (CI) | Regressão de 11/11 |
| CT-04 | US-02 / SCRUM-26 | Sem cenário: comando de administração por WhatsApp só chega com a US-18 | Pendente | Escopo da R3 |
| CT-05 | US-02 / SCRUM-26 | `login.feature` "Bloqueio após 5 senhas incorretas seguidas" e "Login com senha incorreta não revela se o login existe" | Passou (CI) | Regressão de 11/11 |
| CT-06 | US-03 / SCRUM-27 | `produtos.feature` "Cadastrar produto no catálogo"; Cypress "Cadastrar produto e alterar o preço" | Passou (CI) | Regressão de 11/11 |
| CT-07 | US-03 / SCRUM-27 | `produtos.feature` "Não permite produto com nome repetido", "Não permite preço negativo", "Não permite nome vazio" | Passou (CI) | Regressão de 11/11 |
| CT-08 | US-04 / SCRUM-28 | `produtos.feature` "Alterar o preço de um produto" | Passou (CI) | Regressão de 11/11 |
| CT-09 | US-04 / SCRUM-28 | `produtos.feature` "Pedido já feito mantém o preço antigo", "Inativar produto o tira dos novos pedidos"; Cypress "Inativar produto" | Passou (CI) | O produto é inativado, nunca excluído |
| CT-10 | US-05 / SCRUM-29 | `pedido.feature` "Pedido por texto com itens do catálogo" | Passou (CI) | Regressão de 11/11 |
| CT-11 | US-05 / SCRUM-29 | `pedido.feature` "Mensagem sem nenhum item do catálogo" | Passou (CI) | Regressão de 11/11 |
| CT-12 | US-05 / SCRUM-29 | `pedido.feature` "Mensagem tentando alterar as regras do sistema" | Passou (CI) | Regressão de 11/11 |
| CT-61 | US-05 / BUG-01 (SCRUM-71) | `pedido.feature` "IA devolve quantidade negativa ou zero" | Passou (CI) | PR #16; [run 43144352377](https://github.com/Rafaelszc/HortiReg/actions/runs/43144352377) |

## Release 2 (Sprints 2 e 3)

| CT | US / issue | Cenário automatizado | Status | Evidência |
|---|---|---|---|---|
| CT-13 | US-06 / SCRUM-30 | `pedido_audio.feature` "Pedido por áudio com nomes regionais" | Passou (CI) | PR #18 (BUG-05 / SCRUM-75 corrigido); [run 43144352377](https://github.com/Rafaelszc/HortiReg/actions/runs/43144352377). Homologação com nota de voz real pendente (sem ambiente) |
| CT-14a a CT-14g | US-06 / SCRUM-30 | `pedido_audio.feature`: 7 cenários `@excecao` (áudio longo, formato, ininteligível, arquivo grande, falha no download, IA fora do ar, tempo esgotado) | Passou (CI) | PR #18; [run 43144352377](https://github.com/Rafaelszc/HortiReg/actions/runs/43144352377) |
| CT-15, CT-16 | US-07 / SCRUM-31 | `pedido_itens_ambiguos.feature` (`@wip`) | Especificado | Cenários prontos; faltam os passos e a implementação |
| CT-17 | US-08 / SCRUM-32 | `pedido_confirmacao.feature` "Cliente confirma o pedido" (`1` e `confirmar`) | Passou (CI) | PR #13; [run 43144352377](https://github.com/Rafaelszc/HortiReg/actions/runs/43144352377) |
| CT-18 | US-08 / SCRUM-32 | `pedido_confirmacao.feature` "Resposta ambígua à confirmação" | Passou (CI) | PR #13; corrige o BUG-02 (SCRUM-72); [run 43144352377](https://github.com/Rafaelszc/HortiReg/actions/runs/43144352377) |
| CT-19 | US-08 / SCRUM-32 | `pedido_confirmacao.feature` "Confirmação vinda de outro número" | Passou (CI) | PR #13; o log não traz o telefone; [run 43144352377](https://github.com/Rafaelszc/HortiReg/actions/runs/43144352377) |
| CT-19b | US-08 / SCRUM-32 | `pedido_confirmacao.feature` "Cliente cancela ou pede correção" | Passou (CI) | PR #13; [run 43144352377](https://github.com/Rafaelszc/HortiReg/actions/runs/43144352377) |
| CT-20, CT-20b, CT-21 | US-09 / SCRUM-33 | `pedido_correcao_cancelamento.feature` (`@wip`) | Especificado | Sprint 3 |
| CT-22 | US-10 / SCRUM-34 | `pedido_expiracao.feature` "Pedido expira sem confirmação" | Passou (CI) | PR #14; [run 43144352377](https://github.com/Rafaelszc/HortiReg/actions/runs/43144352377) |
| CT-23 | US-10 / SCRUM-34 | `pedido_expiracao.feature` "Confirmação depois da expiração" | Passou (CI) | PR #14; [run 43144352377](https://github.com/Rafaelszc/HortiReg/actions/runs/43144352377) |
| CT-23b | US-10 / SCRUM-34 | `pedido_expiracao.feature` "Pedido dentro do prazo não expira" | Passou (CI) | PR #14; [run 43144352377](https://github.com/Rafaelszc/HortiReg/actions/runs/43144352377) |
| CT-24, CT-25, CT-25b | US-11 / SCRUM-35 | `pedido_endereco.feature` (`@wip`); o CT-25b verifica a LGPD (endereço fora dos logs) | Especificado | Sprint 3 |
| CT-26, CT-27 | US-12 / SCRUM-36 | Cypress `pedidos_do_dia.feature` (`@wip`) | Especificado | Sprint 3; existe uma implementação antiga em `backup/SCRUM-36-pedidos-do-dia` |

## Releases 3 e 4 (planejados)

CT-28 a CT-47 (US-13 a US-22) estão Pendentes. Os nomes dos cenários estão no Plano de Teste v1.1.

## Drivers arquiteturais e segurança

| CT | Driver / issue | Verificação | Status | Evidência |
|---|---|---|---|---|
| CT-48 | DA-CONF-I1-01 / SCRUM-47 | Script com os 50 áudios de referência | Pendente | O conjunto de referência ainda não existe |
| CT-49 | DA-DISP-I1-02 / SCRUM-48 | k6 no pico | Pendente | R3 |
| CT-50 | DA-USAB-I1-03 / SCRUM-49 | Teste de usabilidade | Manual, pendente | — |
| CT-51 | DA-CONF-I2-01 / SCRUM-50, RK-02 / SCRUM-57 | `pedido.feature` "Webhook reenviado não gera pedido duplicado" e `test_duplicidade_carga.py` (1.000 mensagens, 20% reenviadas) | Passou (CI) | 0 duplicados; PR #15; [run 43144352377](https://github.com/Rafaelszc/HortiReg/actions/runs/43144352377) |
| CT-52 | DA-DISP-I2-02 / SCRUM-51 | Deploy com falha injetada | Pendente | Não existe ambiente de homologação |
| CT-53 | DA-USAB-I2-03 / SCRUM-52 | Cronometrar a troca de preço no painel | Manual, pendente | Medir junto com o Q-11 |
| CT-54 | DA-CONF-I3-01 / SCRUM-53 | Falha simulada da IA | Falhou | BUG-03 (SCRUM-73, aberto): no pedido por texto, o cliente fica sem resposta. Sprint 3 com a SCRUM-53 |
| CT-55 | DA-DISP-I3-02 / SCRUM-54 | Queda da sessão do WhatsApp | Pendente | R3 |
| CT-56 | DA-USAB-I3-03 / SCRUM-55 | Mensagens de erro | Parcial | Áudio coberto (`pedido_audio.feature`, PR #18); falta o caso de texto (BUG-03 / SCRUM-73) |
| CT-57 | Segurança / US-05 | `webhook_seguranca.feature`: sem token, token incorreto, token na URL, token no cabeçalho, sem token configurado (dev) | Passou (CI) | BUG-04 (SCRUM-74) corrigido no PR #19; [run 43144352377](https://github.com/Rafaelszc/HortiReg/actions/runs/43144352377) |
| CT-58 | Segurança / US-05 | Injeção de comando ou SQL tratada como texto | Parcial | Injeção no prompt coberta pelo CT-12; SQL só por ORM parametrizado, sem cenário próprio |
| CT-59 | Segurança / US-02 | `test_auth_unidade.py::test_pedidos_exigem_admin`, `produtos.feature` "Catálogo exige autenticação" | Passou (CI) | Regressão de 11/11 |
| CT-60 | Segurança / US-01 | gitleaks e pip-audit no CI | Passou (CI) | O gitleaks detectou o BUG-05 (SCRUM-75) |
