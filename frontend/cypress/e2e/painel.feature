# language: pt
Funcionalidade: Pedidos confirmados do dia no painel (US-12)

  @smoke @regressao
  Cenário: Painel abre nos pedidos confirmados de hoje
    Dado que estou na tela de login
    Quando informo o login e a senha corretos
    Então vejo "Nenhum pedido confirmado ainda hoje"

  @regressao
  Cenário: Alternar para todos os pedidos do dia
    Dado que estou na tela de login
    Quando informo o login e a senha corretos
    E escolho ver "Todos" os pedidos
    Então vejo "Nenhum pedido ainda hoje"
