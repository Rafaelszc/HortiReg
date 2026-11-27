# Release notes · HortiReg v2.0.0 (Release 2)

Data: 26/11/2026 · PO e DevOps: Julio · SM: Nidlan · QA: Rafael

## Destaques
Pedido por áudio, confirmação e expiração, endereço de entrega, pedidos do dia no painel,
fila de retentativa para falhas da IA no WhatsApp, deploy com rollback em homologação local
e bot do Telegram.

## Entregas
| Item | Jira | PRs |
|---|---|---|
| US-06 Pedido por áudio | SCRUM-30 | #18, #25 |
| US-08 Confirmação do pedido | SCRUM-32 | #13 |
| US-10 Expiração de pedido não confirmado | SCRUM-34 | #14 |
| US-11 Endereço de entrega | SCRUM-35 | #31 |
| US-12 Pedidos confirmados do dia no painel | SCRUM-36 | #29 |
| Aviso ao cliente em falha da IA no texto (RK-03) | SCRUM-58 | #23 |
| Fila de retentativa sem perda de mensagens | SCRUM-53 | #26 |
| Teste de duplicidade com 1.000 mensagens (RK-02) | SCRUM-57 | #15 |
| Deploy com healthcheck e rollback (homologação local) | SCRUM-51 | #30 |
| Bot do Telegram e pedidos ativos no painel | sem card identificado | #32 |

Também: autenticação do webhook por token (#19), documentação, modelos do GitHub e Dependabot.

## Bugs corrigidos
- BUG-01 (SCRUM-71): quantidade negativa ou zero vinda da IA.
- BUG-02 (SCRUM-72): resposta ambígua criava um segundo pedido.
- BUG-03 (SCRUM-73): falha da IA no texto deixava o cliente sem resposta.
- BUG-04 (SCRUM-74): webhook aceitava evento forjado. A proteção exige WEBHOOK_TOKEN configurado.
- BUG-05 (SCRUM-75): CI falhava no gitleaks e no ruff.

## Problemas conhecidos
### Bot do Telegram
- Confirma pedidos sem pedir ou conferir o endereço de entrega.
- Responder "não" depois da confirmação cancela o pedido.
- Editar um pedido confirmado há mais de 30 minutos pode expirá-lo.
- Os avisos de expiração são enviados pelo WhatsApp; uma falha pode interromper os demais avisos.
- Não usa a fila de retentativa.
- O estado das conversas é perdido quando a API reinicia.
- Configuração obrigatória: defina TELEGRAM_WEBHOOK_SECRET com um valor aleatório em todo ambiente,
  inclusive com polling ou sem usar o bot.
- Trate os logs da API como sensíveis e restrinja o acesso a eles.
- O modelo padrão da IA mudou, também para o WhatsApp (GEMINI_MODEL e GEMINI_FALLBACK_MODEL);
  não há registro de validação com a IA real.

### Demais
- BUG-06 (SCRUM-76), baixa: a reserva de 120 s da fila pode duplicar um pedido.
- Pedidos do dia filtra pela data de criação, não pela de confirmação.
- Trocar o endereço muda também o exibido nos pedidos já confirmados.
- O job do Cypress falhou de forma intermitente com Chrome 158 (causa não confirmada).
- Homologação apenas local; sem registro de teste com WhatsApp e Gemini reais.

## Fora desta release
- US-07 (itens ambíguos) e US-09 (corrigir ou cancelar): cenários ainda marcados como @wip.
- SCRUM-47: não há evidência da medição de precisão da IA (Q-06).

## Qualidade na base da release (d638ac0)
137 testes da API aprovados, cobertura de 85,94%, ruff e Cypress @smoke (3/3) aprovados.
O ensaio de deploy e rollback passou. A regressão completa roda no PR da release.
