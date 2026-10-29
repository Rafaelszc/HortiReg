from datetime import timedelta

from pytest_bdd import given, parsers, scenarios, then, when

from tests.conftest import LOGIN, SENHA

scenarios("features/login.feature")


@given("que o administrador está cadastrado", target_fixture="ctx")
def _cadastrado(admin, client, relogio):
    return {"client": client, "relogio": relogio}


def _login(client, senha, login=LOGIN):
    return client.post("/auth/login", json={"login": login, "senha": senha})


@when("informa login e senha corretos")
def _ok(ctx):
    ctx["resp"] = _login(ctx["client"], SENHA)


@then("recebe uma sessão autenticada")
def _sessao(ctx):
    assert ctx["resp"].status_code == 200
    ctx["token"] = ctx["resp"].json()["access_token"]


@then("consegue consultar seus dados com a sessão")
def _me(ctx):
    r = ctx["client"].get("/auth/me", headers={"Authorization": f"Bearer {ctx['token']}"})
    assert r.status_code == 200
    assert r.json() == {"login": LOGIN}


@when("informa uma senha incorreta")
def _errada(ctx):
    ctx["resp"] = _login(ctx["client"], "errada")


@then("o acesso é negado com mensagem genérica")
def _generica(ctx):
    assert ctx["resp"].status_code == 401
    assert ctx["resp"].json()["detail"] == "Login ou senha inválidos."


@then("o mesmo ocorre para um login inexistente")
def _inexistente(ctx):
    r = _login(ctx["client"], "qualquer", login="ninguem")
    assert r.status_code == 401
    assert r.json() == ctx["resp"].json()


@when(parsers.parse("erra a senha {n:d} vezes seguidas"))
def _erra_n(ctx, n):
    for _ in range(n):
        assert _login(ctx["client"], "errada").status_code == 401


@then("um novo login, mesmo correto, é bloqueado")
def _bloqueado(ctx):
    assert _login(ctx["client"], SENHA).status_code == 423


@then("após 15 minutos o login correto volta a funcionar")
def _desbloqueia(ctx):
    ctx["relogio"]["agora"] += timedelta(minutes=15, seconds=1)
    assert _login(ctx["client"], SENHA).status_code == 200
