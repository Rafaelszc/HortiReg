import { FormEvent, KeyboardEvent, useState } from "react";
import { ApiError, login, me } from "./api";
import { Marca } from "./Marca";

type Props = {
  aviso: string;
  onEntrar: (token: string, login: string) => void;
};

export default function Login({ aviso, onEntrar }: Props) {
  const [erro, setErro] = useState<{ msg: string; bloqueio: boolean } | null>(null);
  const [enviando, setEnviando] = useState(false);
  const [verSenha, setVerSenha] = useState(false);
  const [capsLock, setCapsLock] = useState(false);

  async function entrar(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    if (enviando) return;
    setErro(null);
    setEnviando(true);
    const f = new FormData(e.currentTarget);
    try {
      const token = await login(String(f.get("login")).trim(), String(f.get("senha")));
      const u = await me(token);
      onEntrar(token, u.login);
    } catch (err) {
      const status = err instanceof ApiError ? err.status : 0;
      setErro({ msg: (err as Error).message, bloqueio: status === 423 });
      setEnviando(false);
    }
  }

  const checarCaps = (e: KeyboardEvent<HTMLInputElement>) =>
    setCapsLock(e.getModifierState?.("CapsLock") ?? false);

  return (
    <div className="login">
      <aside className="login-arte" aria-hidden="true">
        <Marca />
        <div className="login-arte-texto">
          <p className="sobrelinha">Painel do feirante</p>
          <h2>Da conversa no WhatsApp à banca separada, sem papel.</h2>
        </div>
        <svg className="login-ramos" viewBox="0 0 400 400" fill="none">
          <path d="M40 380C120 300 160 200 150 60" />
          <path d="M150 140c40-30 90-30 120-10-30 30-80 40-120 10Z" />
          <path d="M146 220c-40-28-92-24-118 0 32 26 82 30 118 0Z" />
          <path d="M120 300c40-20 90-10 116 16-34 22-84 18-116-16Z" />
          <circle cx="300" cy="90" r="34" />
          <circle cx="330" cy="250" r="18" />
        </svg>
      </aside>

      <main className="login-form-area">
        <div className="login-cartao">
          <div className="login-marca-movel">
            <Marca />
          </div>
          <h1>Entrar</h1>
          <p className="subtitulo">Acesse os pedidos e o catálogo da sua banca.</p>

          {aviso && !erro && (
            <p className="nota nota-info" role="status">
              {aviso}
            </p>
          )}

          <form onSubmit={entrar} noValidate={false}>
            <div className="campo">
              <label htmlFor="login">Login</label>
              <input
                id="login"
                name="login"
                autoComplete="username"
                autoCapitalize="none"
                spellCheck={false}
                required
                autoFocus
              />
            </div>

            <div className="campo">
              <label htmlFor="senha">Senha</label>
              <div className="campo-senha">
                <input
                  id="senha"
                  name="senha"
                  type={verSenha ? "text" : "password"}
                  autoComplete="current-password"
                  required
                  onKeyUp={checarCaps}
                  onKeyDown={checarCaps}
                  aria-describedby={capsLock ? "caps" : undefined}
                />
                <button
                  type="button"
                  className="botao-icone"
                  onClick={() => setVerSenha((v) => !v)}
                  aria-pressed={verSenha}
                  aria-label={verSenha ? "Ocultar senha" : "Mostrar senha"}
                >
                  {verSenha ? <IconeOlhoFechado /> : <IconeOlho />}
                </button>
              </div>
              {capsLock && (
                <p id="caps" className="dica">
                  Caps Lock está ativado.
                </p>
              )}
            </div>

            <div aria-live="assertive">
              {erro && (
                <div className={`nota ${erro.bloqueio ? "nota-alerta" : "nota-erro"}`}>
                  <IconeAlerta />
                  <p role="alert" data-cy="erro">
                    {erro.msg}
                  </p>
                </div>
              )}
            </div>

            <button type="submit" className="botao botao-primario" disabled={enviando}>
              {enviando && <span className="spinner spinner-claro" aria-hidden="true" />}
              {enviando ? "Entrando…" : "Entrar"}
            </button>
          </form>

          <p className="rodape-login">
            Por segurança, o acesso é bloqueado por 15 minutos após 5 tentativas erradas.
          </p>
        </div>
      </main>
    </div>
  );
}

function IconeOlho() {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" aria-hidden="true">
      <path
        d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12Z"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.8"
      />
      <circle cx="12" cy="12" r="3" fill="none" stroke="currentColor" strokeWidth="1.8" />
    </svg>
  );
}

function IconeOlhoFechado() {
  return (
    <svg width="20" height="20" viewBox="0 0 24 24" aria-hidden="true">
      <path
        d="M3 3l18 18M10.6 5.1A10 10 0 0 1 12 5c6.5 0 10 7 10 7a17 17 0 0 1-3.2 4.1M6.6 6.6C3.8 8.4 2 12 2 12s3.5 7 10 7a9.6 9.6 0 0 0 5.4-1.6M9.9 9.9a3 3 0 0 0 4.2 4.2"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinecap="round"
      />
    </svg>
  );
}

export function IconeAlerta() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" aria-hidden="true" className="nota-icone">
      <circle cx="12" cy="12" r="9.5" fill="none" stroke="currentColor" strokeWidth="1.8" />
      <path d="M12 7.5v5.5M12 16.4v.1" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
    </svg>
  );
}
