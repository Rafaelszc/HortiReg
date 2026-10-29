const brl = new Intl.NumberFormat("pt-BR", { style: "currency", currency: "BRL" });
const num = new Intl.NumberFormat("pt-BR", { maximumFractionDigits: 3 });
const hora = new Intl.DateTimeFormat("pt-BR", { hour: "2-digit", minute: "2-digit" });
const diaLongo = new Intl.DateTimeFormat("pt-BR", {
  weekday: "long",
  day: "numeric",
  month: "long",
});

export const moeda = (v: string | number) => brl.format(Number(v));
export const quantidade = (v: string | number) => num.format(Number(v));
export const horario = (iso: string) => hora.format(new Date(iso));

/** "2026-10-29" → "quinta-feira, 29 de outubro" (sem deslocar o fuso). */
export function dataPorExtenso(dia: string) {
  const [a, m, d] = dia.split("-").map(Number);
  return diaLongo.format(new Date(a, m - 1, d));
}

export function hojeISO() {
  const d = new Date();
  const p = (n: number) => String(n).padStart(2, "0");
  return `${d.getFullYear()}-${p(d.getMonth() + 1)}-${p(d.getDate())}`;
}

/** 5583999990000 ou +5583999990000 → (83) 99999-0000; outros formatos ficam como vieram. */
export function telefone(t: string) {
  const n = t.replace(/\D/g, "").replace(/^55(?=\d{10,11}$)/, "");
  if (n.length === 11) return `(${n.slice(0, 2)}) ${n.slice(2, 7)}-${n.slice(7)}`;
  if (n.length === 10) return `(${n.slice(0, 2)}) ${n.slice(2, 6)}-${n.slice(6)}`;
  return t;
}

/** "2", "caixa", "banana" → "2 caixas de banana"; siglas (kg, g, l) não flexionam. */
export function descreverItem(qtd: string | number, unidade: string, produto: string) {
  const plural = Number(qtd) > 1 && unidade.length > 2 && !unidade.endsWith("s");
  return `${quantidade(qtd)} ${plural ? `${unidade}s` : unidade} de ${produto}`;
}
