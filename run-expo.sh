#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")" && pwd)"
cd "$ROOT"

WEB_PORT="${WEB_PORT:-8080}"
EXPO_PORT="${EXPO_PORT:-8081}"
LAN_IP="${LAN_IP:-}"

kill_port() {
  local port="$1"
  local pids=""
  if command -v fuser >/dev/null 2>&1; then
    fuser -k "${port}/tcp" >/dev/null 2>&1 || true
  fi
  pids="$(lsof -tiTCP:"$port" -sTCP:LISTEN -n -P 2>/dev/null || true)"
  if [ -n "$pids" ]; then
    kill -9 $pids >/dev/null 2>&1 || true
  fi
}

echo "Killing anything on port ${EXPO_PORT}..."
kill_port "$EXPO_PORT"
kill_port 8082
pkill -f "$ROOT/mobile/node_modules/.bin/expo" >/dev/null 2>&1 || true
pkill -f "expo start --" >/dev/null 2>&1 || true
sleep 1
echo "Port ${EXPO_PORT} is free."

if [ -z "$LAN_IP" ]; then
  LAN_IP="$(ip -4 -o addr show scope global | awk '
    /docker|br-|veth|virbr/ { next }
    { gsub(/\/.*/, "", $4); print $4; exit }
  ')"
fi

if [ -z "$LAN_IP" ]; then
  echo "Could not find a Wi-Fi IP. Set LAN_IP=192.168.x.x and run again."
  exit 1
fi

APP_URL="http://${LAN_IP}:${WEB_PORT}"
EXPO_URL="exp://${LAN_IP}:${EXPO_PORT}"
echo "Phone must reach this computer at ${LAN_IP}"
echo "Second Shift: $APP_URL"

if ! curl -fsS "$APP_URL/api/health" >/dev/null; then
  echo "Web app is not reachable at $APP_URL"
  echo "Start it first with: ./run.sh"
  exit 1
fi

printf 'EXPO_PUBLIC_APP_URL=%s\n' "$APP_URL" > "$ROOT/mobile/.env"

watches="$(cat /proc/sys/fs/inotify/max_user_watches)"
instances="$(cat /proc/sys/fs/inotify/max_user_instances)"
watchers_ok=0
if [ "$watches" -ge 200000 ] && [ "$instances" -ge 512 ]; then
  watchers_ok=1
elif sudo -n sysctl -w fs.inotify.max_user_watches=524288 fs.inotify.max_user_instances=1024 >/dev/null 2>&1; then
  watchers_ok=1
fi

cd "$ROOT/mobile"
unset CI || true
export REACT_NATIVE_PACKAGER_HOSTNAME="$LAN_IP"

echo
echo "On the phone: open Expo Go → Scan QR code. Not the normal camera."
echo "Or type: ${EXPO_URL}"
echo

if [ "$watchers_ok" = "1" ]; then
  exec npx expo start --lan --port "$EXPO_PORT"
fi

export CI=true
npx expo start --lan --port "$EXPO_PORT" &
expo_pid=$!
trap 'kill "$expo_pid" 2>/dev/null || true; kill_port "$EXPO_PORT"' EXIT INT TERM

ready=0
for _ in $(seq 1 60); do
  if curl -fsS "http://${LAN_IP}:${EXPO_PORT}" >/dev/null 2>&1; then
    ready=1
    break
  fi
  if ! kill -0 "$expo_pid" 2>/dev/null; then
    echo "Expo exited before it was ready."
    wait "$expo_pid" || true
    exit 1
  fi
  sleep 1
done

if [ "$ready" = "1" ]; then
  echo
  echo "Scan this QR inside Expo Go"
  echo
  node -e "require('qrcode-terminal').generate(process.argv[1])" "$EXPO_URL"
  echo
  echo "$EXPO_URL"
  echo
fi

wait "$expo_pid"
