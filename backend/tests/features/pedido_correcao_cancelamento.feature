# language: pt
# Escrito pelo QA a partir dos critérios da SCRUM-33. Tirar o @wip quando os passos existirem.
@wip @US-09 @R2
Funcionalidade: Corrigir ou cancelar pedido (US-09)

  Contexto:
    Dado um catálogo ativo com tomate e banana

  # CT-20
  @smoke @regressao
  Esquema do Cenário: Cliente remove um item de um pedido ainda não separado
    Dado que o cliente tem um pedido "<status>" com "2 kg de tomate" e "1 caixa de banana"
    Quando o cliente envia "tirar a banana"
    Então o pedido fica só com tomate
    E o cliente recebe o resumo atualizado

    Exemplos:
      | status                 |
      | AGUARDANDO_CONFIRMACAO |
      | CONFIRMADO             |

  # CT-20b
  @regressao
  Cenário: Cliente cancela um pedido confirmado
    Dado que o cliente tem um pedido "CONFIRMADO" com "2 kg de tomate"
    Quando o cliente envia "cancelar"
    Então o pedido fica cancelado
    E o cliente recebe a confirmação do cancelamento

  # CT-21
  @regressao @excecao
  Cenário: Remoção de item que não está no pedido
    Dado que o cliente tem um pedido "CONFIRMADO" com "2 kg de tomate"
    Quando o cliente envia "tirar a banana"
    Então o cliente é avisado de que banana não está no pedido
    E o pedido permanece como estava
