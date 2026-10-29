import { Marca } from "./Marca";

type Props = {
  token: string;
  login: string;
  onSair: () => void;
  onExpirada: () => void;
};

export default function Painel({ login, onSair }: Props) {
  return (
    <div className="painel">
      <header className="topo">
        <div className="topo-conteudo">
          <Marca />
          <div className="topo-usuario">
            <span className="avatar" aria-hidden="true">
              {login.slice(0, 1).toUpperCase()}
            </span>
            <span data-cy="boas-vindas" className="topo-nome">
              Olá, {login}
            </span>
            <button type="button" className="botao botao-fantasma" onClick={onSair}>
              Sair
            </button>
          </div>
        </div>
      </header>
      <main className="conteudo">
        <div className="estado">
          <h2>Bem-vindo ao painel</h2>
          <p>Os pedidos do dia chegam aqui em breve.</p>
        </div>
      </main>
    </div>
  );
}
