import { useCallback, useEffect, useState } from "react";
import { expiracao, me } from "./api";
import Login from "./Login";
import Painel from "./Painel";

const CHAVE = "hortireg.token";

function lerToken() {
  try {
    return sessionStorage.getItem(CHAVE);
  } catch {
    return null;
  }
}

function gravarToken(t: string | null) {
  try {
    if (t) sessionStorage.setItem(CHAVE, t);
    else sessionStorage.removeItem(CHAVE);
  } catch {
    /* armazenamento indisponível: sessão vale só nesta aba */
  }
}

type Sessao = { token: string; login: string };

export default function App() {
  const [sessao, setSessao] = useState<Sessao | null>(null);
  const [restaurando, setRestaurando] = useState(() => lerToken() !== null);
  const [aviso, setAviso] = useState("");

  const sair = useCallback((motivo = "") => {
    gravarToken(null);
    setSessao(null);
    setAviso(motivo);
  }, []);

  // Restaura a sessão da aba, se o token ainda for aceito.
  useEffect(() => {
    const t = lerToken();
    if (!t) return;
    me(t)
      .then((u) => setSessao({ token: t, login: u.login }))
      .catch(() => gravarToken(null))
      .finally(() => setRestaurando(false));
  }, []);

  // Encerra a sessão quando o token expira.
  useEffect(() => {
    if (!sessao) return;
    const exp = expiracao(sessao.token);
    if (!exp) return;
    const id = window.setTimeout(
      () => sair("Sua sessão expirou. Entre novamente."),
      Math.max(0, exp - Date.now()),
    );
    return () => window.clearTimeout(id);
  }, [sessao, sair]);

  if (restaurando) {
    return (
      <div className="carregando-tela" role="status">
        <span className="spinner" aria-hidden="true" />
        <span className="sr-only">Carregando…</span>
      </div>
    );
  }

  if (!sessao) {
    return (
      <Login
        aviso={aviso}
        onEntrar={(token, login) => {
          gravarToken(token);
          setAviso("");
          setSessao({ token, login });
        }}
      />
    );
  }

  return (
    <Painel
      token={sessao.token}
      login={sessao.login}
      onSair={() => sair()}
      onExpirada={() => sair("Sua sessão expirou. Entre novamente.")}
    />
  );
}
