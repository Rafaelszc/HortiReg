export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
  }
}

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

/** Momento (ms) em que o JWT expira, ou null se ilegível. */
export function expiracao(token: string): number | null {
  try {
    const payload = JSON.parse(atob(token.split(".")[1].replace(/-/g, "+").replace(/_/g, "/")));
    return typeof payload.exp === "number" ? payload.exp * 1000 : null;
  } catch {
    return null;
  }
}

export type Produto = { id: number; nome: string; unidade: string; preco: number; ativo: boolean };

export function listarProdutos(token: string) {
  return pedir<Produto[]>("/produtos", {}, token);
}

export function criarProduto(token: string, dados: { nome: string; unidade: string; preco: number }) {
  return pedir<Produto>("/produtos", { method: "POST", body: JSON.stringify(dados) }, token);
}

export function atualizarProduto(token: string, id: number, dados: { preco?: number; ativo?: boolean }) {
  return pedir<Produto>(`/produtos/${id}`, { method: "PATCH", body: JSON.stringify(dados) }, token);
}
