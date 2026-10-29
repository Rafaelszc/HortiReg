export function Folha({ size = 28 }: { size?: number }) {
  return (
    <svg width={size} height={size} viewBox="0 0 32 32" aria-hidden="true">
      <rect width="32" height="32" rx="9" fill="var(--marca-fundo)" />
      <path
        d="M9 21c0-7 5-12 14-12 0 9-5 14-12 14"
        fill="none"
        stroke="var(--sol)"
        strokeWidth="2.4"
        strokeLinecap="round"
      />
      <path d="M9 23l7-7" stroke="var(--sol)" strokeWidth="2.4" strokeLinecap="round" />
    </svg>
  );
}

export function Marca() {
  return (
    <span className="marca">
      <Folha />
      <span>HortiReg</span>
    </span>
  );
}
