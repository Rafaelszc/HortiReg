# language: pt
@US-06 @R2
Funcionalidade: Pedido por áudio (US-06)

  Contexto:
    Dado um catálogo ativo com tomate e macaxeira

  @smoke @regressao
  Cenário: Pedido por áudio com nomes regionais
    Dado que a IA extrai "1 kg de tomate" e "2 kg de macaxeira"
    Quando o cliente envia um áudio de 30 segundos
    Então um pedido é criado aguardando confirmação com 2 itens
    E o cliente recebe o resumo com valor estimado de "R$ 16,50"
    E o áudio foi enviado à IA como "audio/ogg"

  @regressao @excecao
  Cenário: Áudio acima de 60 segundos
    Quando o cliente envia um áudio de 61 segundos
    Então nenhum pedido é criado
    E o áudio não é baixado nem enviado à IA
    E o cliente é orientado a reenviar em áudio mais curto ou em texto

  @regressao @excecao
  Cenário: Áudio em formato não suportado
    Quando o cliente envia um áudio no formato "audio/amr"
    Então nenhum pedido é criado
    E o áudio não é baixado nem enviado à IA
    E o cliente é orientado a reenviar em áudio mais curto ou em texto

  @regressao @excecao
  Cenário: Áudio ininteligível
    Dado que a IA não extrai nenhum item
    Quando o cliente envia um áudio de 10 segundos
    Então nenhum pedido é criado
    E o cliente é orientado a reenviar em áudio mais curto ou em texto

  @regressao @excecao
  Cenário: Arquivo de áudio grande demais mesmo sem duração informada
    Dado que o arquivo baixado tem 6 megabytes
    Quando o cliente envia um áudio sem duração informada
    Então nenhum pedido é criado
    E a IA não é chamada
    E o cliente é orientado a reenviar em áudio mais curto ou em texto

  @regressao @excecao
  Cenário: Falha ao baixar o áudio
    Dado que o download do áudio falha
    Quando o cliente envia um áudio de 10 segundos
    Então nenhum pedido é criado
    E o cliente é orientado a reenviar em áudio mais curto ou em texto

  @regressao @excecao
  Cenário: IA fora do ar
    Dado que a IA está fora do ar
    Quando o cliente envia um áudio de 10 segundos
    Então nenhum pedido é criado
    E o cliente é orientado a reenviar em áudio mais curto ou em texto

  @regressao @excecao
  Cenário: IA demora mais que o limite de espera
    Dado que a IA demora mais que o limite de espera
    Quando o cliente envia um áudio de 10 segundos
    Então nenhum pedido é criado
    E o cliente é orientado a reenviar em áudio mais curto ou em texto
