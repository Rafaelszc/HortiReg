# language: pt
Funcionalidade: Catálogo de produtos do administrador (US-03, US-04)

  @smoke @regressao
  Cenário: Cadastrar produto no catálogo
    Dado que o administrador está autenticado
    Quando cadastra o produto "tomate" em "kg" por 6.50
    Então o produto é criado ativo com preço 6.50
    E ele aparece na lista de produtos

  @regressao
  Cenário: Não permite produto com nome repetido
    Dado que o administrador está autenticado
    E o produto "tomate" em "kg" por 6.50 está cadastrado
    Quando cadastra o produto "Tomate" em "kg" por 7.00
    Então o cadastro é recusado por nome repetido

  @regressao
  Cenário: Não permite preço negativo
    Dado que o administrador está autenticado
    Quando cadastra o produto "alface" em "un" por -1
    Então o cadastro é recusado por dados inválidos

  @regressao
  Cenário: Não permite nome vazio
    Dado que o administrador está autenticado
    Quando cadastra o produto "  " em "un" por 2.00
    Então o cadastro é recusado por dados inválidos

  @smoke @regressao
  Cenário: Alterar o preço de um produto
    Dado que o administrador está autenticado
    E o produto "tomate" em "kg" por 6.50 está cadastrado
    Quando altera o preço do produto para 8.00
    Então o preço do produto passa a ser 8.00

  @regressao
  Cenário: Pedido já feito mantém o preço antigo
    Dado que o administrador está autenticado
    E o produto "tomate" em "kg" por 6.50 está cadastrado
    E existe um pedido de 2 kg de tomate
    Quando altera o preço do produto para 8.00
    Então o pedido existente continua com o preço 6.50

  @smoke @regressao
  Cenário: Inativar produto o tira dos novos pedidos
    Dado que o administrador está autenticado
    E o produto "tomate" em "kg" por 6.50 está cadastrado
    Quando inativa o produto
    Então o produto fica inativo
    E um novo pedido de tomate não usa preço do catálogo

  @regressao
  Cenário: Catálogo exige autenticação
    Quando consulta a lista de produtos sem sessão
    Então o acesso é negado
