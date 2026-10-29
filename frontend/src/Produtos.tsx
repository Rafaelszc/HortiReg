import { type FormEvent, useCallback, useEffect, useState } from "react";
import { ApiError, atualizarProduto, criarProduto, listarProdutos, type Produto } from "./api";

type Props = { token: string; onExpirada: () => void };

const brl = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" });

export default function Produtos({ token, onExpirada }: Props) {
  const [produtos, setProdutos] = useState<Produto[] | null>(null);
  const [erro, setErro] = useState("");

  const tratar = useCallback(
    (e: unknown) => {
      if (e instanceof ApiError && e.status === 401) onExpirada();
      else setErro((e as Error).message);
    },
    [onExpirada],
  );

  const carregar = useCallback(() => {
    listarProdutos(token).then(setProdutos).catch(tratar);
  }, [token, tratar]);

  useEffect(carregar, [carregar]);

  async function cadastrar(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    const form = e.currentTarget;
    const f = new FormData(form);
    setErro("");
    try {
      await criarProduto(token, {
        nome: String(f.get("nome")),
        unidade: String(f.get("unidade")),
        preco: Number(f.get("preco")),
      });
      form.reset();
      carregar();
    } catch (err) {
      tratar(err);
    }
  }

  async function alterar(id: number, dados: { preco?: number; ativo?: boolean }) {
    setErro("");
    try {
      await atualizarProduto(token, id, dados);
      carregar();
    } catch (err) {
      tratar(err);
    }
  }

  return (
    <section aria-labelledby="titulo-produtos">
      <div className="cabecalho">
        <h1 id="titulo-produtos">Produtos</h1>
      </div>

      <form className="produto-form" onSubmit={cadastrar} data-cy="form-produto">
        <div className="campo">
          <label htmlFor="p-nome">Nome</label>
          <input id="p-nome" name="nome" required maxLength={120} />
        </div>
        <div className="campo">
          <label htmlFor="p-unidade">Unidade</label>
          <input id="p-unidade" name="unidade" defaultValue="kg" required maxLength={20} />
        </div>
        <div className="campo">
          <label htmlFor="p-preco">Preço (R$)</label>
          <input id="p-preco" name="preco" type="number" min="0" step="0.01" required />
        </div>
        <button type="submit" className="botao botao-primario">
          Cadastrar
        </button>
      </form>

      {erro && (
        <div className="nota nota-erro" role="alert" data-cy="erro-produto">
          <p>{erro}</p>
        </div>
      )}

      {produtos === null ? (
        <span className="spinner" role="status" aria-label="Carregando…" />
      ) : produtos.length === 0 ? (
        <div className="estado">
          <h2>Nenhum produto</h2>
          <p>Cadastre o primeiro produto para os pedidos terem preço.</p>
        </div>
      ) : (
        <ul className="lista">
          {produtos.map((p) => (
            <LinhaProduto key={p.id} p={p} onAlterar={alterar} />
          ))}
        </ul>
      )}
    </section>
  );
}

function LinhaProduto({ p, onAlterar }: { p: Produto; onAlterar: (id: number, d: { preco?: number; ativo?: boolean }) => void }) {
  function salvarPreco(e: FormEvent<HTMLFormElement>) {
    e.preventDefault();
    onAlterar(p.id, { preco: Number(new FormData(e.currentTarget).get("preco")) });
  }

  return (
    <li className={`produto${p.ativo ? "" : " produto-inativo"}`} data-cy="produto">
      <span className="produto-nome">
        {p.nome} <small>({p.unidade})</small>
        {!p.ativo && <span className="selo selo-cancelado">Inativo</span>}
      </span>
      {/* key força o campo a refletir o preço salvo */}
      <form key={p.preco} className="produto-preco" onSubmit={salvarPreco}>
        <label className="sr-only" htmlFor={`preco-${p.id}`}>
          Preço de {p.nome}
        </label>
        <input id={`preco-${p.id}`} name="preco" type="number" min="0" step="0.01" defaultValue={p.preco} required />
        <button type="submit" className="botao botao-secundario" aria-label={`Salvar preço de ${p.nome} (atual ${brl.format(p.preco)})`}>
          Salvar
        </button>
      </form>
      <button type="button" className="botao botao-fantasma" onClick={() => onAlterar(p.id, { ativo: !p.ativo })}>
        {p.ativo ? "Inativar" : "Ativar"}
      </button>
    </li>
  );
}
