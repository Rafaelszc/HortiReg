export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
  }
}

export type Status = "AGUARDANDO_CONFIRMACAO" | "CONFIRMADO" | "CANCELADO" | "ENTREGUE";

export type Item = {
  nome: string;
  quantidade: number;
  unidade: string;
  /** null quando o item não casou com o catálogo (preço a confirmar). */
  preco_unitario: number | null;
  subtotal: number | null;
};

export type Pedido = {
  id: number;
  status: Status;
  criado_em: string;
  observacao: string | null;
  cliente: { telefone: string; nome: string | null };
  total_estimado: number;
  itens: Item[];
};

async function pedir<T>(url: string, init: RequestInit = {}, token?: string): Promise<T> {
  const headers = new Headers(init.headers);
  if (token) headers.set("Authorization", `Bearer ${token}`);
  if (init.body) headers.set("Content-Type", "application/json");
  let r: Response;
  try {
    r = await fetch(url, { ...init, headers });
  } catch {
    throw new ApiError(0, "Sem conexão com o servidor. Verifique a internet e tente de novo.");
  }
  const corpo = await r.json().catch(() => ({}));
  if (!r.ok) {
    const detalhe = typeof corpo.detail === "string" ? corpo.detail : "Algo deu errado. Tente de novo.";
    throw new ApiError(r.status, detalhe);
  }
  return corpo as T;
}

export async function login(loginName: string, senha: string): Promise<string> {
  const r = await pedir<{ access_token: string }>("/auth/login", {
    method: "POST",
    body: JSON.stringify({ login: loginName, senha }),
  });
  return r.access_token;
}

export function me(token: string) {
  return pedir<{ login: string }>("/auth/me", {}, token);
}

export function listarPedidos(token: string, dia: string, status?: Status) {
  const q = new URLSearchParams({ dia });
  if (status) q.set("status", status);
  return pedir<Pedido[]>(`/pedidos?${q}`, {}, token);
}

/** Momento (ms) em que o JWT expira, ou null se ilegível. */
export function expiracao(token: string): number | null {
  try {
    const payload = JSON.parse(atob(token.split(".")[1].replace(/-/g, "+").replace(/_/g, "/")));
    return typeof payload.exp === "number" ? payload.exp * 1000 : null;
  } catch {
    return null;
  }
}
