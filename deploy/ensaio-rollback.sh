#!/usr/bin/env bash
# Ensaio do DA-DISP-I2-02 (CT-52 / Q-10): deploy normal e deploy com falha injetada na homologação.
# Aprova se o deploy normal ficar ≤ 60 s fora do ar e o rollback terminar em ≤ 2 min com a versão anterior no ar.
set -euo pipefail
cd "$(dirname "$0")"
BASE="$(git rev-parse --short HEAD)"

./deploy.sh "$BASE-a"                                  # garante uma versão no ar
./deploy.sh "$BASE-b"                                  # deploy normal (troca de versão)
FALHA_INJETADA=1 ./deploy.sh "$BASE-falha" && { echo "REPROVADO: deploy com falha não fez rollback"; exit 1; }

normal=$(grep ",$BASE-b,$BASE-a,0,ok," registro-deploys.csv | tail -1 | cut -d, -f6)
rollback=$(grep ",$BASE-falha,$BASE-b,1,rollback," registro-deploys.csv | tail -1 | cut -d, -f7)
no_ar=$(curl -fsS "http://127.0.0.1:${HOMOLOG_API_PORTA:-8001}/health" | sed -n 's/.*"versao":"\([^"]*\)".*/\1/p')

echo "Deploy normal: ${normal} s fora do ar (meta ≤ 60 s)"
echo "Rollback: ${rollback} s (meta ≤ 120 s); versão no ar: ${no_ar}"
awk -v n="$normal" -v r="$rollback" 'BEGIN {exit !(n <= 60 && r <= 120)}' && [[ "$no_ar" == "$BASE-b" ]] \
  && echo "APROVADO" || { echo "REPROVADO"; exit 1; }
