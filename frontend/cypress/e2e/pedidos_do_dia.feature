# language: pt
# Escrito pelo QA a partir dos critérios da SCRUM-36. Tirar o @wip quando os passos existirem.
@wip @US-12 @R2
Funcionalidade: Pedidos confirmados do dia no painel (US-12)

  # CT-26
  @smoke @regressao
  Cenário: Lista de pedidos confirmados do dia
    Dado que o administrador está autenticado
    E que há um pedido confirmado hoje de "Maria" com "2 kg de tomate" no endereço "Rua das Flores, 120"
    E que há um pedido confirmado ontem e um pedido aguardando confirmação hoje
    Quando abre "Pedidos do dia"
    Então vê 1 pedido com cliente, itens, endereço, valor e status

  # CT-27
  @regressao @excecao
  Cenário: Dia sem pedidos confirmados
    Dado que o administrador está autenticado
    E que não há pedidos confirmados hoje
    Quando abre "Pedidos do dia"
    Então vê a mensagem "Nenhum pedido confirmado hoje"
