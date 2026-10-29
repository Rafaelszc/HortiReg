# language: pt
Funcionalidade: Catálogo de produtos no painel (US-03, US-04)

  @smoke @regressao
  Cenário: Cadastrar produto e alterar o preço
    Dado que estou logado no painel
    Quando cadastro o produto com nome único, unidade "kg" e preço "6.50"
    Então o produto aparece na lista
    Quando altero o preço do produto para "8.00"
    Então o preço do produto é "8.00"

  @regressao
  Cenário: Inativar produto
    Dado que estou logado no painel
    Quando cadastro o produto com nome único, unidade "kg" e preço "3.00"
    E inativo o produto
    Então o produto aparece como inativo
