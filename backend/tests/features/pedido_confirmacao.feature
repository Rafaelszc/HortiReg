# language: pt
@US-08 @R2
Funcionalidade: Confirmação do pedido pelo cliente (US-08)

  Contexto:
    Dado um catálogo ativo com tomate e banana
    E que a IA extrai "2 kg de tomate"
    E o cliente envia "quero 2 kg de tomate"

  # CT-17
  @smoke @regressao
  Esquema do Cenário: Cliente confirma o pedido
    Quando o cliente envia "<resposta>"
    Então o pedido fica confirmado
    E o cliente recebe a confirmação com o número do pedido

    Exemplos:
      | resposta  |
      | 1         |
      | confirmar |

  # CT-18
  @regressao @excecao
  Cenário: Resposta ambígua à confirmação
    Quando o cliente envia "talvez"
    Então o pedido continua aguardando confirmação
    E o sistema repete as opções 1, 2 e 3
    E nenhum pedido novo é criado

  # CT-19
  @regressao @excecao @seguranca
  Cenário: Confirmação vinda de outro número
    Quando outro número envia "confirmar"
    Então o pedido continua aguardando confirmação
    E a tentativa é registrada em log sem o telefone

  # CT-19b
  @regressao
  Esquema do Cenário: Cliente cancela ou pede correção
    Quando o cliente envia "<resposta>"
    Então o pedido fica cancelado
    E o cliente recebe "<mensagem>"

    Exemplos:
      | resposta | mensagem                |
      | 3        | cancelado.              |
      | 2        | Envie o pedido completo |
