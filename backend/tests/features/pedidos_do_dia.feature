# language: pt
@US-12 @R2
Funcionalidade: Pedidos confirmados do dia (US-12, API do painel)

  # CT-26
  @smoke @regressao
  Cenário: Lista só os pedidos confirmados de hoje
    Dado que o administrador está autenticado
    E que há um pedido confirmado hoje de "Maria" com "2 kg de tomate" no endereço "Rua das Flores, 120"
    E que há um pedido confirmado ontem e um pedido aguardando confirmação hoje
    Quando consulta os pedidos do dia
    Então recebe 1 pedido de "Maria" no endereço "Rua das Flores, 120" com valor 13.00 e status "CONFIRMADO"

  # CT-27
  @regressao @excecao
  Cenário: Dia sem pedidos confirmados
    Dado que o administrador está autenticado
    E que não há pedidos confirmados hoje
    Quando consulta os pedidos do dia
    Então recebe uma lista vazia

  @regressao @seguranca
  Cenário: Pedidos do dia exigem autenticação
    Quando consulta os pedidos do dia sem sessão
    Então a resposta é 401
