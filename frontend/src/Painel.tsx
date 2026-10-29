import { useCallback, useEffect, useMemo, useState } from "react";
import { ApiError, listarPedidos, type Pedido, type Status } from "./api";
import {
  dataPorExtenso,
  descreverItem,
  hojeISO,
  horario,
  moeda,
  quantidade,
  telefone,
} from "./formato";
import { IconeAlerta } from "./Login";
import { Marca } from "./Marca";

type Props = {
  token: string;
  login: string;
  onSair: () => void;
  onExpirada: () => void;
};

type Estado =
  | { tipo: "carregando" }
  | { tipo: "erro"; msg: string }
  | { tipo: "ok"; pedidos: Pedido[]; em: Date };

export default function Painel({ token, login, onSair, onExpirada }: Props) {
  const [dia, setDia] = useState(hojeISO);
  const [soConfirmados, setSoConfirmados] = useState(true);
  const [estado, setEstado] = useState<Estado>({ tipo: "carregando" });
  const [atualizando, setAtualizando] = useState(false);

  const carregar = useCallback(
    async (silencioso = false) => {
      if (silencioso) setAtualizando(true);
      else setEstado({ tipo: "carregando" });
      try {
        const pedidos = await listarPedidos(token, dia, soConfirmados ? "CONFIRMADO" : undefined);
        setEstado({ tipo: "ok", pedidos, em: new Date() });
      } catch (err) {
        if (err instanceof ApiError && err.status === 401) return onExpirada();
        setEstado({ tipo: "erro", msg: (err as Error).message });
      } finally {
        setAtualizando(false);
      }
    },
    [token, dia, soConfirmados, onExpirada],
  );

  useEffect(() => {
    carregar();
  }, [carregar]);

  // Mantém o dia atual em dia: recarrega a cada minuto e ao voltar para a aba.
  useEffect(() => {
    if (dia !== hojeISO()) return;
    const tick = () => document.visibilityState === "visible" && carregar(true);
    const id = window.setInterval(tick, 60_000);
    document.addEventListener("visibilitychange", tick);
    return () => {
      window.clearInterval(id);
      document.removeEventListener("visibilitychange", tick);
    };
  }, [dia, carregar]);

  const ehHoje = dia === hojeISO();

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
        <section className="cabecalho">
          <div>
            <p className="sobrelinha">{ehHoje ? "Hoje" : "Histórico"}</p>
            <h1>{primeiraMaiuscula(dataPorExtenso(dia))}</h1>
          </div>
          <div className="filtros">
            <div className="segmentado" role="group" aria-label="Quais pedidos mostrar">
              <button type="button" aria-pressed={soConfirmados} onClick={() => setSoConfirmados(true)}>
                Confirmados
              </button>
              <button type="button" aria-pressed={!soConfirmados} onClick={() => setSoConfirmados(false)}>
                Todos
              </button>
            </div>
            <label className="campo-data">
              <span className="sr-only">Dia</span>
              <input
                type="date"
                value={dia}
                max={hojeISO()}
                onChange={(e) => e.target.value && setDia(e.target.value)}
              />
            </label>
            {!ehHoje && (
              <button type="button" className="botao botao-secundario" onClick={() => setDia(hojeISO())}>
                Hoje
              </button>
            )}
            <button
              type="button"
              className="botao botao-secundario"
              onClick={() => carregar(true)}
              disabled={estado.tipo === "carregando" || atualizando}
              aria-label="Atualizar pedidos"
            >
              <IconeAtualizar girando={atualizando} />
              <span className="so-desktop">Atualizar</span>
            </button>
          </div>
        </section>

        {estado.tipo === "carregando" && <Esqueleto />}
        {estado.tipo === "erro" && (
          <div className="estado estado-erro" role="alert">
            <IconeAlerta />
            <p>{estado.msg}</p>
            <button type="button" className="botao botao-secundario" onClick={() => carregar()}>
              Tentar de novo
            </button>
          </div>
        )}
        {estado.tipo === "ok" && <Resumo pedidos={estado.pedidos} />}
        {estado.tipo === "ok" &&
          (estado.pedidos.length === 0 ? (
            <Vazio hoje={ehHoje} soConfirmados={soConfirmados} />
          ) : (
            <section aria-labelledby="titulo-lista">
              <div className="lista-cabecalho">
                <h2 id="titulo-lista">Pedidos</h2>
                <span className="atualizado">Atualizado às {horario(estado.em.toISOString())}</span>
              </div>
              <ul className="lista">
                {estado.pedidos.map((p) => (
                  <CartaoPedido key={p.id} pedido={p} />
                ))}
              </ul>
            </section>
          ))}
      </main>
    </div>
  );
}

function Resumo({ pedidos }: { pedidos: Pedido[] }) {
  const r = useMemo(() => {
    // Cancelados aparecem na lista, mas não contam no resumo.
    const validos = pedidos.filter((p) => p.status !== "CANCELADO");
    const total = validos.reduce((s, p) => s + p.total_estimado, 0);
    const clientes = new Set(validos.map((p) => p.cliente.telefone)).size;
    return { qtd: validos.length, total, clientes, ticket: validos.length ? total / validos.length : 0 };
  }, [pedidos]);

  return (
    <dl className="resumo">
      <div className="metrica metrica-destaque">
        <dt>Faturamento estimado</dt>
        <dd>{moeda(r.total)}</dd>
      </div>
      <div className="metrica">
        <dt>Pedidos</dt>
        <dd>{r.qtd}</dd>
      </div>
      <div className="metrica">
        <dt>Clientes</dt>
        <dd>{r.clientes}</dd>
      </div>
      <div className="metrica">
        <dt>Ticket médio</dt>
        <dd>{moeda(r.ticket)}</dd>
      </div>
    </dl>
  );
}

const ROTULO_STATUS: Record<Status, string> = {
  AGUARDANDO_CONFIRMACAO: "Aguardando",
  CONFIRMADO: "Confirmado",
  CANCELADO: "Cancelado",
  ENTREGUE: "Entregue",
};

function CartaoPedido({ pedido: p }: { pedido: Pedido }) {
  const resumoItens = p.itens.map((i) => descreverItem(i.quantidade, i.unidade, i.nome));
  const semPreco = p.itens.some((i) => i.preco_unitario === null);
  return (
    <li className="pedido">
      <details>
        <summary>
          <span className="pedido-id">#{p.id}</span>
          <span className="pedido-info">
            <span className="pedido-cliente">
              {p.cliente.nome ? `${p.cliente.nome} · ` : ""}
              {telefone(p.cliente.telefone)}
            </span>
            <span className="pedido-itens">{resumoItens.join(" · ")}</span>
          </span>
          <span className="pedido-meta">
            <span className={`selo selo-${p.status.toLowerCase()}`}>{ROTULO_STATUS[p.status]}</span>
            <span className="pedido-hora">{horario(p.criado_em)}</span>
          </span>
          <span className="pedido-total" title={semPreco ? "Há itens com preço a confirmar" : undefined}>
            {moeda(p.total_estimado)}
            {semPreco && <span aria-hidden="true">*</span>}
          </span>
          <IconeSeta />
        </summary>
        <table className="itens">
          <thead>
            <tr>
              <th scope="col">Produto</th>
              <th scope="col" className="num">
                Qtd.
              </th>
              <th scope="col" className="num">
                Preço
              </th>
              <th scope="col" className="num">
                Subtotal
              </th>
            </tr>
          </thead>
          <tbody>
            {p.itens.map((i, n) => (
              <tr key={n}>
                <td>{i.nome}</td>
                <td className="num">
                  {quantidade(i.quantidade)} {i.unidade}
                </td>
                <td className="num">{i.preco_unitario === null ? "a confirmar" : moeda(i.preco_unitario)}</td>
                <td className="num">{i.subtotal === null ? "—" : moeda(i.subtotal)}</td>
              </tr>
            ))}
          </tbody>
          <tfoot>
            <tr>
              <th scope="row" colSpan={3}>
                {semPreco ? "Total estimado (sem itens a confirmar)" : "Total estimado"}
              </th>
              <td className="num">{moeda(p.total_estimado)}</td>
            </tr>
          </tfoot>
        </table>
        {p.observacao && <p className="pedido-obs">Obs.: {p.observacao}</p>}
      </details>
    </li>
  );
}

function Esqueleto() {
  return (
    <div role="status" aria-label="Carregando pedidos">
      <div className="resumo">
        {[0, 1, 2, 3].map((i) => (
          <div key={i} className="metrica esqueleto" />
        ))}
      </div>
      <ul className="lista">
        {[0, 1, 2].map((i) => (
          <li key={i} className="pedido esqueleto esqueleto-linha" />
        ))}
      </ul>
    </div>
  );
}

function Vazio({ hoje, soConfirmados }: { hoje: boolean; soConfirmados: boolean }) {
  return (
    <div className="estado">
      <svg width="56" height="56" viewBox="0 0 56 56" aria-hidden="true" className="estado-icone">
        <path d="M10 22h36l-4 22H14L10 22Z" fill="none" stroke="currentColor" strokeWidth="2" />
        <path d="M20 22c0-6 3.5-10 8-10s8 4 8 10" fill="none" stroke="currentColor" strokeWidth="2" />
      </svg>
      <h2>
        {soConfirmados
          ? hoje
            ? "Nenhum pedido confirmado ainda hoje"
            : "Nenhum pedido confirmado neste dia"
          : hoje
            ? "Nenhum pedido ainda hoje"
            : "Nenhum pedido neste dia"}
      </h2>
      <p>
        {hoje
          ? "Os pedidos confirmados pelos clientes no WhatsApp aparecem aqui automaticamente."
          : "Escolha outra data para ver o histórico."}
      </p>
    </div>
  );
}

function IconeAtualizar({ girando }: { girando: boolean }) {
  return (
    <svg
      width="18"
      height="18"
      viewBox="0 0 24 24"
      aria-hidden="true"
      className={girando ? "girando" : undefined}
    >
      <path
        d="M20 11a8 8 0 1 0-2.3 5.7M20 4v7h-7"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.9"
        strokeLinecap="round"
        strokeLinejoin="round"
      />
    </svg>
  );
}

function IconeSeta() {
  return (
    <svg width="18" height="18" viewBox="0 0 24 24" aria-hidden="true" className="pedido-seta">
      <path d="m9 6 6 6-6 6" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" />
    </svg>
  );
}

const primeiraMaiuscula = (s: string) => s.charAt(0).toUpperCase() + s.slice(1);
