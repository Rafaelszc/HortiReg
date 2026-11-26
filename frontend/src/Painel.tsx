import { useState } from "react";
import { Marca } from "./Marca";
import PedidosDoDia from "./PedidosDoDia";
import Produtos from "./Produtos";

type Props = {
  token: string;
  login: string;
  onSair: () => void;
  onExpirada: () => void;
};

type Aba = "produtos" | "pedidos";

export default function Painel({ token, login, onSair, onExpirada }: Props) {
  const [aba, setAba] = useState<Aba>("produtos");

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
        <nav className="segmentado" aria-label="Seções do painel">
          <button type="button" aria-pressed={aba === "produtos"} onClick={() => setAba("produtos")}>
            Produtos
          </button>
          <button type="button" aria-pressed={aba === "pedidos"} onClick={() => setAba("pedidos")}>
            Pedidos do dia
          </button>
        </nav>
        {aba === "produtos" ? (
          <Produtos token={token} onExpirada={onExpirada} />
        ) : (
          <PedidosDoDia token={token} onExpirada={onExpirada} />
        )}
      </main>
    </div>
  );
}
