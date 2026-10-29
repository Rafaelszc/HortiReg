# language: pt
Funcionalidade: Acesso seguro do administrador (US-02)

  @smoke @regressao
  Cenário: Login do administrador com credenciais válidas
    Dado que o administrador está cadastrado
    Quando informa login e senha corretos
    Então recebe uma sessão autenticada
    E consegue consultar seus dados com a sessão

  @regressao
  Cenário: Login com senha incorreta não revela se o login existe
    Dado que o administrador está cadastrado
    Quando informa uma senha incorreta
    Então o acesso é negado com mensagem genérica
    E o mesmo ocorre para um login inexistente

  @smoke @regressao
  Cenário: Bloqueio após 5 senhas incorretas seguidas
    Dado que o administrador está cadastrado
    Quando erra a senha 5 vezes seguidas
    Então um novo login, mesmo correto, é bloqueado
    E após 15 minutos o login correto volta a funcionar
