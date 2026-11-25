import { useEffect, useState } from "react";
import { ApiError, listarPedidosDoDia, type PedidoDoDia } from "./api";

type Props = { token: string; onExpirada: () => void };

const brl = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" });
const num = new Intl.NumberFormat("pt-BR", { maximumFractionDigits: 3 });
const hora = new Intl.DateTimeFormat("pt-BR", { hour: "2-digit", minute: "2-digit" });

const STATUS: Record<string, string> = {
  AGUARDANDO_CONFIRMACAO: "Aguardando",
  CONFIRMADO: "Confirmado",
  CANCELADO: "Cancelado",
  ENTREGUE: "Entregue",
  EXPIRADO: "Expirado",
};

export default function PedidosDoDia({ token, onExpirada }: Props) {
  const [pedidos, setPedidos] = useState<PedidoDoDia[] | null>(null);
  const [erro, setErro] = useState("");

  useEffect(() => {
    listarPedidosDoDia(token)
      .then(setPedidos)
      .catch((e: unknown) => {
        if (e instanceof ApiError && e.status === 401) onExpirada();
        else setErro((e as Error).message);
      });
  }, [token, onExpirada]);

  const total = pedidos?.reduce((s, p) => s + p.valor, 0) ?? 0;

  return (
    <section aria-labelledby="titulo-pedidos">
      <div className="cabecalho">
        <h1 id="titulo-pedidos">Pedidos do dia</h1>
        {pedidos && pedidos.length > 0 && (
          <p className="subtitulo" data-cy="resumo-dia">
            {pedidos.length} {pedidos.length === 1 ? "pedido confirmado" : "pedidos confirmados"} · {brl.format(total)}
          </p>
        )}
      </div>

      {erro && (
        <div className="nota nota-erro" role="alert">
          <p>{erro}</p>
        </div>
      )}

      {pedidos === null && !erro && <p className="dica">Carregando…</p>}

      {pedidos?.length === 0 && (
        <p className="estado" data-cy="sem-pedidos">
          Nenhum pedido confirmado hoje
        </p>
      )}

      {pedidos && pedidos.length > 0 && (
        <ul className="lista">
          {pedidos.map((p) => (
            <li key={p.id} className="pedido" data-cy="pedido-dia">
              <div className="pedido-info">
                <p className="pedido-cliente" data-cy="pedido-cliente">
                  {p.cliente} <span className="pedido-id">#{p.id}</span>
                </p>
                <p className="pedido-itens" data-cy="pedido-itens">
                  {p.itens.map((i) => `${num.format(i.quantidade)} ${i.unidade} de ${i.nome}`).join(", ")}
                </p>
                <p className="pedido-obs" data-cy="pedido-endereco">
                  {p.endereco ?? "Endereço não informado"}
                </p>
              </div>
              <div className="pedido-meta">
                <span className={`selo selo-${p.status === "AGUARDANDO_CONFIRMACAO" ? "aguardando" : p.status.toLowerCase()}`} data-cy="pedido-status">
                  {STATUS[p.status] ?? p.status}
                </span>
                <span className="pedido-total" data-cy="pedido-valor">
                  {brl.format(p.valor)}
                </span>
                <span className="pedido-hora">{hora.format(new Date(p.criado_em))}</span>
              </div>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
