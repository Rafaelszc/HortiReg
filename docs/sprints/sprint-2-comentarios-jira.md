# Sprint 2: textos prontos para colar no Jira

Rascunho de 11/11/2026. Nada disto foi enviado ao Jira. Cole cada bloco na issue indicada (ajuste o que não estiver correto) e apague este arquivo se não quiser versioná-lo.

## SCRUM-30 · US-06 Pedido por áudio

**Campos a corrigir**
- Story points: o campo está em 0 e a descrição diz 8. Definir o valor acordado na Planning (a estimativa original no campo era 5) e alinhar o texto.
- Cabeçalho da descrição: "Papel de revisão: PO". O PO é o próprio responsável pela US; indicar outro revisor (Rafael, QA) para o PR e o aceite testemunhado pelo SM.
- DoR: marcar as duas caixas depois de confirmar com o PO o limite de 60 s e os formatos abaixo.

**Comentário**

> Implementação da US-06 na branch `feature/SCRUM-30-pedido-audio` (PR para a `develop` pendente).
> **Regras implementadas:** áudio acima de 60 s (`AUDIO_MAX_SEGUNDOS`) é recusado antes do download; formatos aceitos: ogg (nota de voz do WhatsApp, inclusive codecs=opus), mp3, aac e wav; arquivo acima de 5 MB (`AUDIO_MAX_BYTES`) é recusado mesmo sem duração; falha de download, erro da IA ou espera acima de 45 s (`AUDIO_TIMEOUT_SEGUNDOS`) resultam em mensagem ao cliente, nunca em silêncio; áudio sem itens reconhecidos devolve mensagem própria. Em todos os casos de exceção nenhum pedido é criado.
> **Decisão pedida ao PO:** confirmar os 60 s e a lista de formatos (m4a/mp4 ficaram de fora porque o Gemini não os lista).
> **Testes:** `pedido_audio.feature` (@US-06 @R2): 1 cenário de sucesso e 7 de exceção (CT-13 e CT-14a a CT-14g); 59 testes passando, cobertura 92%, ruff e bandit limpos.
> **Pendente para a DoD:** homologação manual com nota de voz real; revisão do PR; validação do QA; aceite do PO.
> **Limitações conhecidas:** se a IA falha, o pedido não é criado e o cliente precisa reenviar (fila e retentativa: SCRUM-53); o prompt do Gemini foi alterado e a reavaliação no conjunto de 50 áudios depende do SCRUM-47.

## SCRUM-56 · RK-01 Substituição

> Atualização Sprint 2: o prompt do Gemini agora manda devolver lista vazia para áudio ininteligível e nunca inventar produtos, e a confirmação do cliente (SIM/NÃO) continua como controle de detecção. **Ainda aberto:** itens sem correspondência no catálogo continuam entrando no pedido como "preço a confirmar" (`catalogo.montar_itens`); a pergunta ao cliente em itens ambíguos é a US-07 (SCRUM-31). A meta de ≥ 90% no conjunto de 50 áudios só pode ser medida quando o SCRUM-47 existir. Sugestão: manter status "Risco" e revisar P/S na Retrospectiva.

## SCRUM-58 · RK-03 Sem resposta quando a IA falha

> Atualização Sprint 2: mitigação **parcial** para o fluxo de áudio. Falha de download, erro da IA ou espera acima de 45 s agora são registrados em log e o cliente recebe mensagem pedindo para reenviar (antes: silêncio). **Não atendido:** a mensagem é marcada como processada e o pedido não é criado; não há fila nem retentativa, então a meta "0 mensagens perdidas" depende do SCRUM-53 (Sprint 3).

## SCRUM-59 · RK-04 Capacidade no pico

> Atualização Sprint 2: o áudio é processado em segundo plano, um por mensagem, sem limite de concorrência e sem fila. O timeout de 45 s evita conexões presas, mas não protege a cota da IA. Providência (fila assíncrona com limite de concorrência e teste k6) continua na Sprint 5. Observação: o webhook ainda não exigia autenticação, e cada áudio forjado custa uma chamada à IA (ver item de token do webhook).

## SCRUM-64 · RK-09 Sem mensagem compreensível em erro

> Atualização Sprint 2: o fluxo de áudio ganhou mensagens próprias para áudio longo, formato não suportado, ininteligível e falha técnica, todas em linguagem simples, com exemplo de pedido e sugestão de enviar em texto, e 7 cenários `@excecao` automatizados. Falta consolidar as mensagens do bot no catálogo previsto no SCRUM-55 (hoje são constantes em `routers/webhook.py`) e fazer a sessão com usuários.

## Novo item sugerido · Autenticação do webhook (segurança)

**Tipo:** Story ou Task · **Labels:** `seguranca`, `R2` · **Ligado a:** DoD item 23, CT-57, RK-04, US-05/US-06

> **Problema:** `POST /webhook/whatsapp` aceita qualquer evento. Com o pedido por áudio, um evento forjado faz a API baixar arquivo e chamar o Gemini (custo e cota).
> **Entrega:** token configurável (`WEBHOOK_TOKEN`), enviado pela Evolution na URL (`?token=`) ou no cabeçalho `X-Webhook-Token`; resposta 401 sem token válido; vazio = aberto (desenvolvimento).
> **Critérios (Gherkin):** `webhook_seguranca.feature` (@seguranca): sem token → 401; token incorreto → 401; token correto na URL → 200; token correto no cabeçalho → 200; sem token configurado → 200.
> **Estado:** implementado na branch `feature/webhook-token` (a partir da `develop`), 38 testes passando. Para ativar: definir `WEBHOOK_TOKEN` no `.env` e recriar `evolution-api` e `api`.

## Revisão de riscos (DoD da Sprint, item 18)

Todos os RK-01 a RK-09 continuam com status "Risco". Na Retrospectiva: atualizar probabilidade e severidade dos RK-01, 03, 04 e 09 com os comentários acima, e marcar o RK-02 (idempotência, SCRUM-50) como mitigado, já que o webhook ignora mensagens repetidas desde a Sprint 1.
