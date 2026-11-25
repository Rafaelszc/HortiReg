# language: pt
# Critérios da SCRUM-36. A API é simulada (cy.intercept); o filtro do dia e do status é testado no backend
# (backend/tests/features/pedidos_do_dia.feature).
@US-12 @R2
Funcionalidade: Pedidos confirmados do dia no painel (US-12)

  # CT-26
  @smoke @regressao
  Cenário: Lista de pedidos confirmados do dia
    Dado que há um pedido confirmado hoje de "Maria" com "2 kg de tomate" no endereço "Rua das Flores, 120" por 13.00
    E que estou logado no painel
    Quando abro "Pedidos do dia"
    Então vejo 1 pedido com cliente "Maria", itens "2 kg de tomate", endereço "Rua das Flores, 120", valor "R$ 13,00" e status "Confirmado"

  # CT-27
  @regressao @excecao
  Cenário: Dia sem pedidos confirmados
    Dado que não há pedidos confirmados hoje
    E que estou logado no painel
    Quando abro "Pedidos do dia"
    Então vejo o aviso "Nenhum pedido confirmado hoje"
