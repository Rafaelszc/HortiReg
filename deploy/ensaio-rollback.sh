#!/usr/bin/env bash
# Ensaio do DA-DISP-I2-02 (CT-52 / Q-10): deploy normal e deploys com falha injetada na homologação.
# Falhas: banco inacessível (1), API que não inicia (api) e painel que cai na partida (painel).
# Aprova se cada deploy ficar ≤ 60 s fora do ar, cada rollback terminar em ≤ 2 min e a versão anterior
# continuar no ar (a meta de queda do driver vale também para o deploy com falha).
set -euo pipefail
cd "$(dirname "$0")"
BASE="$(git rev-parse --short HEAD)"
API="http://127.0.0.1:${HOMOLOG_API_PORTA:-8001}/health"
PAINEL="http://127.0.0.1:${HOMOLOG_PAINEL_PORTA:-8091}/"
reprovado=0

./deploy.sh "$BASE-a"                                  # garante uma versão no ar
./deploy.sh "$BASE-b"                                  # deploy normal (troca de versão)
normal=$(grep ",$BASE-b,$BASE-a,0,ok," registro-deploys.csv | tail -1 | cut -d, -f6)
echo "Deploy normal: ${normal} s fora do ar (meta ≤ 60 s)"
awk -v n="$normal" 'BEGIN {exit !(n <= 60)}' || { echo "REPROVADO: deploy normal"; reprovado=1; }

for falha in 1 api painel; do
  if FALHA_INJETADA=$falha ./deploy.sh "$BASE-falha-$falha"; then
    echo "REPROVADO ($falha): deploy com falha foi aprovado"; reprovado=1; continue
  fi
  linha=$(grep ",$BASE-falha-$falha,$BASE-b,$falha,rollback," registro-deploys.csv | tail -1 || true)
  fora=$(cut -d, -f6 <<<"$linha"); rollback=$(cut -d, -f7 <<<"$linha")
  no_ar=$(curl -fsS "$API" | sed -n 's/.*"versao":"\([^"]*\)".*/\1/p')
  echo "Falha $falha: ${fora:-?} s fora do ar (meta ≤ 60 s), rollback em ${rollback:-?} s (meta ≤ 120 s); versão no ar: ${no_ar}"
  [[ -n "$linha" ]] && awk -v f="$fora" -v r="$rollback" 'BEGIN {exit !(f <= 60 && r <= 120)}' \
    && [[ "$no_ar" == "$BASE-b" ]] && curl -fsS -o /dev/null "$PAINEL" \
    || { echo "REPROVADO ($falha)"; reprovado=1; }
done

(( reprovado == 0 )) && echo "APROVADO" || { echo "REPROVADO"; exit 1; }
