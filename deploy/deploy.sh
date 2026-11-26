#!/usr/bin/env bash
# Deploy na homologação com healthcheck e rollback automático (SCRUM-51 / DA-DISP-I2-02 / Q-10).
#
# Uso: deploy/deploy.sh [VERSAO]          VERSAO padrão: commit atual (git rev-parse --short HEAD)
#      FALHA_INJETADA=1 deploy/deploy.sh   sobe a versão com banco inacessível (simula migração quebrada)
#      FALHA_INJETADA=api|painel ...      API que não inicia (comando inexistente) / painel que cai na partida
#
# 1. Constrói as imagens hortireg-api:VERSAO e hortireg-painel:VERSAO (a versão atual continua no ar).
# 2. Troca os containers da API e do painel e espera o /health com a nova versão E o painel respondendo,
#    estáveis por ESTAVEL segundos sem reinício de container.
# 3. Se não ficar saudável em ESPERA_HEALTH segundos, volta para a versão anterior e sai com código 1.
# Um monitor consulta API e painel a cada 0,5 s durante o deploy e mede o tempo fora do ar (qualquer um caído).
# Cada execução vira uma linha em deploy/registro-deploys.csv.
set -euo pipefail
cd "$(dirname "$0")"

VERSAO="${1:-$(git rev-parse --short HEAD)}"
ESPERA_HEALTH="${ESPERA_HEALTH:-30}"
ESTAVEL="${ESTAVEL:-3}"
PORTA="${HOMOLOG_API_PORTA:-8001}"
URL="http://127.0.0.1:${PORTA}/health"
URL_PAINEL="http://127.0.0.1:${HOMOLOG_PAINEL_PORTA:-8091}/"
ESTADO=.versao-atual
REGISTRO=registro-deploys.csv
MONITOR=$(mktemp)
OVERRIDE=$(mktemp --suffix=.yml)
COMPOSE=(docker compose -f docker-compose.homologacao.yml --env-file homologacao.env)

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
painel_no_ar() { curl -fsS --max-time 1 -o /dev/null "$URL_PAINEL" 2>/dev/null; }
no_ar() { curl -fsS --max-time 1 -o /dev/null "$URL" 2>/dev/null && painel_no_ar; }

# Nenhum container da API/painel reiniciou (crash loop com restart: unless-stopped).
sem_reinicio() {
  local ids; ids=$(VERSAO=x "${COMPOSE[@]}" ps -q api frontend 2>/dev/null)
  [[ $(wc -w <<<"$ids") -eq 2 ]] || return 1
  ! docker inspect -f '{{.RestartCount}} {{.State.Running}}' $ids | grep -qv '^0 true$'
}

# Espera API com a versão $1 e painel no ar, estáveis por ESTAVEL s; devolve 0 se ficou saudável no prazo.
esperar() {
  local limite=$(( $(date +%s) + ESPERA_HEALTH ))
  while (( $(date +%s) < limite )); do
    if [[ "$(versao_no_ar)" == "$1" ]] && painel_no_ar; then
      sleep "$ESTAVEL"
      [[ "$(versao_no_ar)" == "$1" ]] && painel_no_ar && sem_reinicio && return 0
    fi
    sleep 0.5
  done
  return 1
}

# subir VERSAO [extra env...]. Erro do compose (ex.: comando inexistente) não encerra o script:
# quem decide é o esperar, para o rollback acontecer. OVR=arquivo acrescenta um override do compose.
subir() {
  local v="$1"; shift
  env VERSAO="$v" "$@" docker compose -f docker-compose.homologacao.yml ${OVR:+-f "$OVR"} --env-file homologacao.env \
    up -d --no-deps --force-recreate api frontend >/dev/null 2>&1 || true
}

registrar() {  # registrar RESULTADO ROLLBACK_S
  local fora; fora=$(indisponibilidade)
  [[ -f "$REGISTRO" ]] || echo "data,versao,anterior,falha_injetada,resultado,indisponibilidade_s,rollback_s" > "$REGISTRO"
  echo "$(date -Iseconds),$VERSAO,${ANTERIOR:--},${FALHA_INJETADA:-0},$1,$fora,${2:--}" >> "$REGISTRO"
  echo "Resultado: $1 | versão no ar: $(versao_no_ar) | fora do ar: ${fora} s${2:+ | rollback em ${2} s}"
}

monitorar() {
  while true; do
    if no_ar; then echo "$(agora) 1"; else echo "$(agora) 0"; fi
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

VERSAO="$VERSAO" "${COMPOSE[@]}" up -d --wait postgres >/dev/null
if [[ -z "$ANTERIOR" ]]; then  # primeira subida: não há versão anterior nem tempo fora do ar a medir
  subir "$VERSAO"
  esperar "$VERSAO" || { echo "Primeira subida falhou"; rm -f "$MONITOR" "$OVERRIDE"; exit 1; }
  echo "$VERSAO" > "$ESTADO"
  echo "Primeira subida: versão $VERSAO no ar."
  rm -f "$MONITOR" "$OVERRIDE"
  exit 0
fi

monitorar & PID_MONITOR=$!
trap 'kill $PID_MONITOR 2>/dev/null || true; rm -f "$MONITOR" "$OVERRIDE"' EXIT
sleep 1

inicio=$(agora)
case "${FALHA_INJETADA:-0}" in
  0) subir "$VERSAO" ;;
  1)
  subir "$VERSAO" API_DATABASE_URL="postgresql+asyncpg://falha:falha@banco-inexistente:5432/falha" ;;
  api)
    printf 'services:\n  api:\n    command: ["comando-inexistente"]\n' > "$OVERRIDE"
    OVR="$OVERRIDE" subir "$VERSAO" ;;
  painel)
    printf 'services:\n  frontend:\n    command: ["false"]\n' > "$OVERRIDE"
    OVR="$OVERRIDE" subir "$VERSAO" ;;
  *) echo "FALHA_INJETADA inválida: $FALHA_INJETADA (use 0, 1, api ou painel)"; exit 1 ;;
esac

if esperar "$VERSAO"; then
  echo "$VERSAO" > "$ESTADO"
  sleep 1
  registrar ok ""
  exit 0
fi

echo "Healthcheck da versão $VERSAO falhou; voltando para $ANTERIOR..."
subir "$ANTERIOR"
if ! esperar "$ANTERIOR"; then
  registrar rollback_falhou ""
  echo "ROLLBACK FALHOU: verificar a homologação manualmente"
  exit 2
fi
rollback_s=$(awk -v a="$inicio" -v b="$(agora)" 'BEGIN {printf "%.1f", b-a}')
sleep 1
registrar rollback "$rollback_s"
exit 1
