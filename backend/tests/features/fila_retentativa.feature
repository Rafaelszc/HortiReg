# language: pt
@US-05 @US-06 @R2 @confiabilidade
Funcionalidade: Falha da IA sem perda de pedidos (RK-03 / DA-CONF-I3-01)
  Como feirante
  Quero que nenhum pedido se perca quando a IA estiver fora do ar
  Para não voltar ao WhatsApp manual

  Contexto:
    Dado um catálogo ativo com tomate e banana
    E que a IA extrai "2 kg de tomate"

  @smoke
  Cenário: Mensagem é gravada e o cliente é avisado quando a IA está fora do ar
    Dado que a IA está fora do ar
    Quando o cliente envia "quero 2 kg de tomate"
    Então a mensagem fica gravada aguardando nova tentativa
    E o cliente é avisado uma vez que o pedido está em processamento
    E nenhum pedido é criado

  @smoke
  Cenário: Pedido é criado quando a IA volta
    Dado que a IA está fora do ar
    E o cliente envia "quero 2 kg de tomate"
    Quando a IA volta e a fila é reprocessada
    Então um pedido é criado aguardando confirmação
    E o cliente recebe o resumo do pedido
    E a mensagem fica como processada

  @regressao
  Cenário: Falha de 30 minutos sem perder nenhuma mensagem
    Dado que a IA está fora do ar
    E 3 clientes enviam pedidos durante a falha
    Quando passam 30 minutos com a IA fora do ar
    E a IA volta
    Então todas as mensagens são processadas em até 5 minutos
    E 3 pedidos são criados aguardando confirmação
    E cada cliente recebeu um único aviso de processamento

  @regressao @excecao
  Cenário: Reenvio do mesmo evento durante a falha
    Dado que a IA está fora do ar
    Quando o cliente envia "quero 2 kg de tomate" e a Evolution reenvia o mesmo evento
    Então apenas uma mensagem fica gravada
    E o cliente é avisado uma vez que o pedido está em processamento

  @regressao @excecao
  Cenário: Prazo esgotado com a IA ainda fora do ar
    Dado que a IA está fora do ar
    E o cliente envia "quero 2 kg de tomate"
    Quando passam 66 minutos com a IA fora do ar
    Então a mensagem fica marcada como falha
    E o cliente é avisado que o pedido não pôde ser lido
    E nenhum pedido é criado

  @regressao
  Cenário: Áudio é baixado de novo na retentativa
    Dado que o download do áudio falha
    E o cliente envia um áudio de 10 segundos
    Quando o download volta e a fila é reprocessada
    Então um pedido é criado aguardando confirmação
    E o áudio foi baixado 2 vezes

  @regressao
  Cenário: A ordem de chegada do cliente é preservada
    Dado que a IA está fora do ar
    E o cliente envia "quero 2 kg de tomate"
    E o cliente envia "1"
    Quando a IA volta e a fila é reprocessada
    Então o pedido fica confirmado
