#!/usr/bin/env bash
set -euo pipefail

V50_ROOT=${V50_ROOT:-/home/hlsystem/bazi/qiazhi/v50}
ENV_FILE=${1:-$V50_ROOT/.env.v50.production}
TTS_BASE_URL=${V50_TTS_BASE_URL:-http://192.168.0.7:7860}
TTS_SPEAKER=${V50_ABU_TTS_SPEAKER:-Eric}
NARRATION_DIR=${V50_NARRATION_MEDIA_DIR:-$V50_ROOT/.runtime/narration}

test -f "$ENV_FILE"

upsert_env() {
  local key=$1
  local value=$2
  if grep -q "^${key}=" "$ENV_FILE"; then
    sed -i "s|^${key}=.*|${key}=${value}|" "$ENV_FILE"
  else
    printf '%s=%s\n' "$key" "$value" >> "$ENV_FILE"
  fi
}

upsert_env V50_TTS_BASE_URL "$TTS_BASE_URL"
upsert_env V50_ABU_TTS_SPEAKER "$TTS_SPEAKER"
upsert_env V50_TTS_TIMEOUT_SECONDS 180
upsert_env V50_NARRATION_MEDIA_DIR "$NARRATION_DIR"
upsert_env V50_NARRATION_OPUS_ENABLED 1
upsert_env V50_FFMPEG_BINARY /usr/bin/ffmpeg

mkdir -p "$NARRATION_DIR"
chmod 700 "$NARRATION_DIR"
chmod 600 "$ENV_FILE"

curl -fsS --connect-timeout 5 --max-time 15 "$TTS_BASE_URL/health" >/dev/null
printf 'Qwen TTS configured: %s, speaker=%s, media=%s\n' "$TTS_BASE_URL" "$TTS_SPEAKER" "$NARRATION_DIR"
