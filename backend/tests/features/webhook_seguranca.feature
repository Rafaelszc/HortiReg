# language: pt
@US-05 @R2 @seguranca
Funcionalidade: Autenticação do webhook (CT-57)

  Contexto:
    Dado um catálogo ativo com tomate e banana
    E que a IA extrai "2 kg de tomate"

  @smoke @regressao
  Cenário: Evento sem token é rejeitado quando o webhook exige token
    Dado que o webhook exige o token "segredo-do-teste"
    Quando a Evolution envia um pedido sem token
    Então o webhook responde 401
    E nenhum pedido é criado

  @regressao
  Cenário: Evento com token incorreto é rejeitado
    Dado que o webhook exige o token "segredo-do-teste"
    Quando a Evolution envia um pedido com o token "outro-segredo" na URL
    Então o webhook responde 401
    E nenhum pedido é criado

  @smoke @regressao
  Cenário: Evento com o token correto na URL é aceito
    Dado que o webhook exige o token "segredo-do-teste"
    Quando a Evolution envia um pedido com o token "segredo-do-teste" na URL
    Então o webhook responde 200
    E um pedido é criado

  @regressao
  Cenário: Evento com o token correto no cabeçalho é aceito
    Dado que o webhook exige o token "segredo-do-teste"
    Quando a Evolution envia um pedido com o token "segredo-do-teste" no cabeçalho
    Então o webhook responde 200
    E um pedido é criado

  @regressao
  Cenário: Sem token configurado o webhook continua aberto (desenvolvimento local)
    Quando a Evolution envia um pedido sem token
    Então o webhook responde 200
    E um pedido é criado
