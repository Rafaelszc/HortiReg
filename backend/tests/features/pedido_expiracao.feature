# language: pt
@US-10 @R2
Funcionalidade: Expiração de pedido não confirmado (US-10)

  Contexto:
    Dado um catálogo ativo com tomate e banana
    E que a IA extrai "2 kg de tomate"
    E o cliente envia "quero 2 kg de tomate"

  # CT-22
  @smoke @regressao
  Cenário: Pedido expira sem confirmação
    Dado que o pedido está aguardando confirmação há 31 minutos
    Quando o prazo de expiração é verificado
    Então o pedido fica expirado
    E o cliente recebe "expirou"
    E o pedido não entra na lista de separação

  # CT-23
  @regressao @excecao
  Cenário: Confirmação depois da expiração
    Dado que o pedido está aguardando confirmação há 31 minutos
    Quando o cliente envia "confirmar"
    Então o pedido fica expirado
    E o cliente recebe "Quer refazer?"

  # CT-23b
  @regressao
  Cenário: Pedido dentro do prazo não expira
    Dado que o pedido está aguardando confirmação há 29 minutos
    Quando o prazo de expiração é verificado
    Então o pedido continua aguardando confirmação
