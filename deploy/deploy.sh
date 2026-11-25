#!/usr/bin/env bash
# Deploy na homologação com healthcheck e rollback automático (SCRUM-51 / DA-DISP-I2-02 / Q-10).
#
# Uso: deploy/deploy.sh [VERSAO]          VERSAO padrão: commit atual (git rev-parse --short HEAD)
#      FALHA_INJETADA=1 deploy/deploy.sh   sobe a versão com banco inacessível (simula migração quebrada)
#
# 1. Constrói as imagens hortireg-api:VERSAO e hortireg-painel:VERSAO (a versão atual continua no ar).
# 2. Troca os containers da API e do painel e espera o /health responder com a nova versão.
# 3. Se não responder em ESPERA_HEALTH segundos, volta para a versão anterior e sai com código 1.
# Um monitor consulta o /health a cada 0,5 s durante o deploy e mede o tempo fora do ar.
# Cada execução vira uma linha em deploy/registro-deploys.csv.
set -euo pipefail
cd "$(dirname "$0")"

VERSAO="${1:-$(git rev-parse --short HEAD)}"
ESPERA_HEALTH="${ESPERA_HEALTH:-30}"
PORTA="${HOMOLOG_API_PORTA:-8001}"
URL="http://127.0.0.1:${PORTA}/health"
ESTADO=.versao-atual
REGISTRO=registro-deploys.csv
MONITOR=$(mktemp)

if [[ ! -f homologacao.env ]]; then
  sed -e "s/^POSTGRES_PASSWORD=.*/POSTGRES_PASSWORD=$(openssl rand -hex 16)/" \
      -e "s/^JWT_SECRET=.*/JWT_SECRET=$(openssl rand -hex 32)/" \
      -e "s/^WEBHOOK_TOKEN=.*/WEBHOOK_TOKEN=$(openssl rand -hex 24)/" \
      -e "s/^ADMIN_PASSWORD=.*/ADMIN_PASSWORD=$(openssl rand -hex 12)/" \
      homologacao.env.example > homologacao.env
  echo "homologacao.env criado com segredos novos (ADMIN_PASSWORD está no arquivo)."
fi
set -a; source homologacao.env; set +a

agora() { date +%s.%N; }
versao_no_ar() { curl -fsS --max-time 2 "$URL" 2>/dev/null | sed -n 's/.*"versao":"\([^"]*\)".*/\1/p'; }

# Espera o /health responder com a versão $1; devolve 0 se respondeu dentro do prazo.
esperar() {
  local limite=$(( $(date +%s) + ESPERA_HEALTH ))
  while (( $(date +%s) < limite )); do
    [[ "$(versao_no_ar)" == "$1" ]] && return 0
    sleep 0.5
  done
  return 1
}

subir() {  # subir VERSAO [extra env...]
  local v="$1"; shift
  env VERSAO="$v" "$@" docker compose -f docker-compose.homologacao.yml --env-file homologacao.env \
    up -d --no-deps --force-recreate api frontend >/dev/null 2>&1
}

monitorar() {
  while true; do
    if curl -fsS --max-time 1 -o /dev/null "$URL" 2>/dev/null; then echo "$(agora) 1"; else echo "$(agora) 0"; fi
    sleep 0.5
  done >> "$MONITOR"
}

# Maior intervalo contínuo sem resposta do /health, em segundos.
indisponibilidade() {
  awk '$2==0 && !ini {ini=$1} $2==1 && ini {d=$1-ini; if (d>max) max=d; ini=0}
       END {if (ini) {d=fim-ini; if (d>max) max=d}; printf "%.1f", max+0}' fim="$(agora)" "$MONITOR"
}

ANTERIOR="$(cat "$ESTADO" 2>/dev/null || true)"
echo "Construindo imagens da versão $VERSAO..."
docker build -q -t "hortireg-api:$VERSAO" ../backend >/dev/null
docker build -q -t "hortireg-painel:$VERSAO" ../frontend >/dev/null

VERSAO="$VERSAO" docker compose -f docker-compose.homologacao.yml --env-file homologacao.env up -d --wait postgres >/dev/null
if [[ -z "$ANTERIOR" ]]; then  # primeira subida: não há versão anterior nem tempo fora do ar a medir
  subir "$VERSAO"
  esperar "$VERSAO" || { echo "Primeira subida falhou"; exit 1; }
  echo "$VERSAO" > "$ESTADO"
  echo "Primeira subida: versão $VERSAO no ar."
  exit 0
fi

monitorar & PID_MONITOR=$!
trap 'kill $PID_MONITOR 2>/dev/null || true; rm -f "$MONITOR"' EXIT
sleep 1

inicio=$(agora)
if [[ "${FALHA_INJETADA:-0}" == 1 ]]; then
  subir "$VERSAO" API_DATABASE_URL="postgresql+asyncpg://falha:falha@banco-inexistente:5432/falha"
else
  subir "$VERSAO"
fi

if esperar "$VERSAO"; then
  resultado=ok; rollback_s=""
  echo "$VERSAO" > "$ESTADO"
else
  [[ -n "$ANTERIOR" ]] || { echo "Deploy falhou e não há versão anterior para voltar"; exit 1; }
  echo "Healthcheck da versão $VERSAO falhou; voltando para $ANTERIOR..."
  subir "$ANTERIOR"
  esperar "$ANTERIOR" || { echo "ROLLBACK FALHOU: verificar a homologação manualmente"; exit 2; }
  resultado=rollback
  rollback_s=$(awk -v a="$inicio" -v b="$(agora)" 'BEGIN {printf "%.1f", b-a}')
fi
sleep 1
fora=$(indisponibilidade)

[[ -f "$REGISTRO" ]] || echo "data,versao,anterior,falha_injetada,resultado,indisponibilidade_s,rollback_s" > "$REGISTRO"
echo "$(date -Iseconds),$VERSAO,${ANTERIOR:--},${FALHA_INJETADA:-0},$resultado,$fora,${rollback_s:--}" >> "$REGISTRO"
echo "Resultado: $resultado | versão no ar: $(versao_no_ar) | fora do ar: ${fora} s${rollback_s:+ | rollback em ${rollback_s} s}"
[[ "$resultado" == ok ]]
