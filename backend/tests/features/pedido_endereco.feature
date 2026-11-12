# language: pt
# Escrito pelo QA a partir dos critérios da SCRUM-35. Tirar o @wip quando os passos existirem.
@wip @US-11 @R2
Funcionalidade: Endereço de entrega do cliente (US-11)

  # CT-24
  @smoke @regressao
  Cenário: Cliente informa endereço completo
    Dado um cliente sem endereço salvo
    Quando o cliente envia "Rua das Flores, 120, Catolé, Campina Grande"
    Então o endereço é salvo e mostrado ao cliente para confirmação
    E o próximo pedido do cliente já usa esse endereço

  # CT-25
  @regressao @excecao
  Esquema do Cenário: Endereço sem rua ou sem número
    Dado um cliente sem endereço salvo
    Quando o cliente envia "<endereco>"
    Então o cliente recebe o pedido de "<falta>"
    E o pedido não pode ser confirmado sem endereço completo

    Exemplos:
      | endereco                              | falta  |
      | Rua das Flores, Catolé, Campina Grande | número |
      | 120, Catolé, Campina Grande            | rua    |

  # CT-25b (LGPD, contexto da US-11)
  @regressao @seguranca
  Cenário: Endereço não aparece nos logs
    Dado um cliente sem endereço salvo
    Quando o cliente envia "Rua das Flores, 120, Catolé, Campina Grande"
    Então nenhum log da API contém "Rua das Flores"
