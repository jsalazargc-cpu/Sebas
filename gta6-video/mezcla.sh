#!/usr/bin/env bash
# Deja el audio de un render a -14 LUFS sin picos por encima de -1 dB, y corta a la duración de la voz.
# (loudnorm + limitador antes del AAC: el codificador AAC añade algo de pico, por eso el margen.)
# Uso: ./mezcla.sh entrada.mp4 salida.mp4
set -euo pipefail
IN="$1"; OUT="$2"
DUR=$(ffprobe -v error -show_entries format=duration -of csv=p=0 "$(dirname "$0")/assets/voz.wav")
ffmpeg -hide_banner -loglevel error -y -i "$IN" -t "$DUR" \
  -c:v libx264 -crf 16 -preset slow -pix_fmt yuv420p \
  -af "loudnorm=I=-12.2:TP=-1.5:LRA=11,aresample=48000,alimiter=limit=0.75:attack=1:release=80:level=disabled" \
  -c:a aac -b:a 256k -movflags +faststart "$OUT"
echo "$OUT -> $(ffmpeg -hide_banner -i "$OUT" -af ebur128=peak=true -f null - 2>&1 | grep -E '^\s+(I|Peak):' | xargs)"
