#!/usr/bin/env bash
# Rehace el vídeo entero: voz -> tiempos -> animación -> render -> mezcla a -14 LUFS.
# Uso:  ./rehacer.sh            (todo)
#       ./rehacer.sh --sin-voz  (no regenera voz ni transcripción: solo animación, render y mezcla)
set -euo pipefail
cd "$(dirname "$0")"

# Igual que "npx hyperframes" (usa el lanzador de las skills si existe)
if [ -f "$HOME/.claude/skills/hyperframes/scripts/plugin-cli.mjs" ]; then
  HF=(node "$HOME/.claude/skills/hyperframes/scripts/plugin-cli.mjs")
else
  HF=(npx hyperframes)
fi
export NODE_NO_WARNINGS=1

if [ "${1:-}" != "--sin-voz" ]; then
  echo "== 1. Voz (Kokoro, em_alex) desde guion_voz.txt"
  "${HF[@]}" tts guion_voz.txt --voice em_alex --lang es -o assets/voz.wav
  echo "== 2. Tiempos de cada palabra (whisper large-v3)"
  "${HF[@]}" transcribe assets/voz.wav --language es --model large-v3 --json > /dev/null
fi

render () { # $1 = salida, $2 = flag del generador
  python3 gen.py $2
  "${HF[@]}" check --json > /dev/null || { echo "check con errores"; exit 1; }
  "${HF[@]}" render -o "$1" --quality delivery --quiet
}

echo "== 3. Render con subtítulos";  render renders/con-subs.mp4 ""
echo "== 4. Render sin subtítulos";  render renders/sin-subs.mp4 "--no-subs"
python3 gen.py   # deja el proyecto otra vez con subtítulos

echo "== 5. Mezcla final a -14 LUFS"
./mezcla.sh renders/con-subs.mp4 video-FINAL.mp4
./mezcla.sh renders/sin-subs.mp4 video-SIN-SUBTITULOS.mp4
echo "Listo: video-FINAL.mp4 y video-SIN-SUBTITULOS.mp4"
