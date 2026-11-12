# language: pt
# Escrito pelo QA a partir dos critérios da SCRUM-31. Tirar o @wip quando os passos existirem.
@wip @US-07 @R2
Funcionalidade: Itens ambíguos ou inexistentes (US-07)

  # CT-15
  @smoke @regressao
  Cenário: Item ambíguo
    Dado que o catálogo tem "tomate salada" e "tomate cereja"
    E que a IA extrai "2 kg de tomate"
    Quando o cliente envia "quero 2 kg de tomate"
    Então o cliente recebe a pergunta com as opções "tomate salada" e "tomate cereja"
    E nenhum item de tomate entra no pedido antes da resposta

  # CT-16
  @regressao @excecao
  Esquema do Cenário: Item inexistente ou inativo
    Dado um catálogo ativo com tomate e banana
    E que a IA extrai "1 kg de <item>"
    Quando o cliente envia "quero 1 kg de <item>"
    Então o item "<item>" não entra no pedido
    E o cliente é avisado de que "<item>" não está disponível

    Exemplos:
      | item      |
      | caju      |
      | macaxeira |
