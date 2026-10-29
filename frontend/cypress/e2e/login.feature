# language: pt
Funcionalidade: Login do administrador (US-02)

  @smoke @regressao
  Cenário: Login com credenciais válidas
    Dado que estou na tela de login
    Quando informo o login e a senha corretos
    Então vejo o painel

  @regressao
  Cenário: Login com senha incorreta
    Dado que estou na tela de login
    Quando informo uma senha incorreta
    Então vejo a mensagem "Login ou senha inválidos."
