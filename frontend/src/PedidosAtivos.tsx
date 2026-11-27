import { useCallback, useEffect, useMemo, useState } from "react";
import { ApiError, listarPedidos, type ItemPedido, type Pedido, type StatusPedido } from "./api";

type Props = {
  token: string;
  onExpirada: () => void;
};

const BRL = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" });

const ROTULO_STATUS: Record<StatusPedido, string> = {
  AGUARDANDO_CONFIRMACAO: "Aguardando confirmação",
  CONFIRMADO: "Confirmado",
  CANCELADO: "Cancelado",
  ENTREGUE: "Entregue",
  EXPIRADO: "Expirado",
};

function totalPedido(itens: ItemPedido[]): number {
  return itens.reduce((acc, i) => acc + (i.preco_unitario !== null ? i.quantidade * i.preco_unitario : 0), 0);
}

function formatarHora(iso: string | null): string {
  if (!iso) return "";
  const data = new Date(iso);
  if (Number.isNaN(data.getTime())) return "";
  return data.toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" });
}

function formatarQtd(qtd: number): string {
  return Number.isInteger(qtd) ? String(qtd) : qtd.toLocaleString("pt-BR");
}

export default function PedidosAtivos({ token, onExpirada }: Props) {
  const [pedidos, setPedidos] = useState<Pedido[]>([]);
  const [carregando, setCarregando] = useState(true);
  const [erro, setErro] = useState<string | null>(null);
  const [atualizadoEm, setAtualizadoEm] = useState<string>("");

  const carregar = useCallback(async () => {
    setCarregando(true);
    setErro(null);
    try {
      const dados = await listarPedidos(token);
      setPedidos(dados);
      setAtualizadoEm(new Date().toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" }));
    } catch (e) {
      if (e instanceof ApiError && e.status === 401) {
        onExpirada();
        return;
      }
      setErro(e instanceof Error ? e.message : "Não foi possível carregar os pedidos.");
    } finally {
      setCarregando(false);
    }
  }, [token, onExpirada]);

  useEffect(() => {
    void carregar();
  }, [carregar]);

  const ativos = useMemo(
    () => pedidos.filter((p) => p.status === "AGUARDANDO_CONFIRMACAO" || p.status === "CONFIRMADO"),
    [pedidos],
  );

  const confirmados = useMemo(() => ativos.filter((p) => p.status === "CONFIRMADO").length, [ativos]);
  const aguardando = useMemo(() => ativos.filter((p) => p.status === "AGUARDANDO_CONFIRMACAO").length, [ativos]);
  const valorEstimado = useMemo(() => ativos.reduce((acc, p) => acc + totalPedido(p.itens), 0), [ativos]);

  return (
    <section data-cy="pedidos-ativos" style={{ marginBottom: "48px" }}>
      <div className="cabecalho">
        <div>
          <p className="sobrelinha">Operação em andamento</p>
          <h1>Pedidos ativos</h1>
        </div>
        <button
          type="button"
          className="botao botao-secundario"
          onClick={() => void carregar()}
          disabled={carregando}
        >
          {carregando ? "Atualizando..." : "Atualizar"}
        </button>
      </div>

      {erro && (
        <div className="nota nota-erro" role="alert">
          <p>{erro}</p>
        </div>
      )}

      <dl className="resumo" data-cy="resumo-pedidos-ativos">
        <div className="metrica metrica-destaque">
          <dt>Pedidos ativos</dt>
          <dd data-cy="total-ativos">{ativos.length}</dd>
        </div>
        <div className="metrica">
          <dt>Confirmados</dt>
          <dd data-cy="total-confirmados">{confirmados}</dd>
        </div>
        <div className="metrica">
          <dt>Aguardando confirmação</dt>
          <dd data-cy="total-aguardando">{aguardando}</dd>
        </div>
        <div className="metrica">
          <dt>Valor estimado</dt>
          <dd data-cy="valor-estimado">{BRL.format(valorEstimado)}</dd>
        </div>
      </dl>

      <div className="lista-cabecalho">
        <h2>Resumo dos pedidos em aberto</h2>
        {atualizadoEm && <span className="atualizado">Atualizado às {atualizadoEm}</span>}
      </div>

      {carregando && pedidos.length === 0 ? (
        <div className="estado">
          <div className="spinner" aria-hidden="true" />
          <p>Carregando pedidos ativos...</p>
        </div>
      ) : ativos.length === 0 ? (
        <div className="estado">
          <h2>Nenhum pedido ativo no momento</h2>
          <p>Novos pedidos confirmados ou aguardando confirmação aparecerão aqui automaticamente ao atualizar.</p>
        </div>
      ) : (
        <ul className="lista">
          {ativos.map((p) => {
            const total = totalPedido(p.itens);
            const resumoItens = p.itens.map((i) => `${formatarQtd(i.quantidade)} ${i.unidade} ${i.nome}`).join(", ");
            return (
              <li key={p.id} className="pedido" data-cy="pedido-ativo">
                <details>
                  <summary>
                    <span className="pedido-id">#{p.id}</span>
                    <div className="pedido-info">
                      <span className="pedido-cliente">{p.cliente}</span>
                      <span className="pedido-itens">{resumoItens || "Sem itens"}</span>
                    </div>
                    <div className="pedido-meta">
                      <span className={`selo selo-${p.status.toLowerCase()}`}>{ROTULO_STATUS[p.status]}</span>
                      {p.criado_em && <span className="pedido-hora">{formatarHora(p.criado_em)}</span>}
                    </div>
                    <span className="pedido-total">{total > 0 ? BRL.format(total) : "A confirmar"}</span>
                    <span className="pedido-seta" aria-hidden="true">
                      ▸
                    </span>
                  </summary>
                  {p.observacao && <p className="pedido-obs">Obs.: {p.observacao}</p>}
                  <table className="itens">
                    <thead>
                      <tr>
                        <th>Item</th>
                        <th className="num">Qtd</th>
                        <th className="num">Subtotal</th>
                      </tr>
                    </thead>
                    <tbody>
                      {p.itens.map((i, idx) => (
                        <tr key={`${p.id}-${idx}`}>
                          <td>{i.nome}</td>
                          <td className="num">
                            {formatarQtd(i.quantidade)} {i.unidade}
                          </td>
                          <td className="num">
                            {i.preco_unitario !== null ? BRL.format(i.quantidade * i.preco_unitario) : "A confirmar"}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </details>
              </li>
            );
          })}
        </ul>
      )}
    </section>
  );
}
