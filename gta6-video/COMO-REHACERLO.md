# Cómo rehacer el vídeo de GTA 6

Todo sale de tres cosas: el guion, la voz y `gen.py`. Si cambias una frase o la voz, el vídeo se reajusta solo a los nuevos tiempos.

## Requisitos

- Node 22 o superior, Python 3 y ffmpeg.
- `npx hyperframes skills` (una vez), y después `npx hyperframes doctor` para comprobar el entorno.
- La primera transcripción descarga el modelo `large-v3` (unos 3 GB) desde Hugging Face.

## Rehacerlo todo con un comando

```bash
cd gta6-video
./rehacer.sh             # voz + tiempos + animación + 2 renders + mezcla a -14 LUFS
./rehacer.sh --sin-voz   # si solo has tocado la animación (no regenera la voz)
```

Salen `video-FINAL.mp4` (con subtítulos) y `video-SIN-SUBTITULOS.mp4`.

## Paso a paso

| Paso | Comando |
|---|---|
| 1. Voz | `npx hyperframes tts guion_voz.txt --voice em_alex --lang es -o assets/voz.wav` |
| 2. Tiempos de cada palabra | `npx hyperframes transcribe assets/voz.wav --language es --model large-v3` → `assets/transcript.json` |
| 3. Generar la composición | `python3 gen.py` (o `python3 gen.py --no-subs`) |
| 4. Comprobar | `npx hyperframes check` y `npx hyperframes snapshot --at 1,5,10` |
| 5. Ver y editar en el navegador | `npx hyperframes preview` |
| 6. Render | `npx hyperframes render -o renders/con-subs.mp4 --quality delivery` |
| 7. Volumen final | `./mezcla.sh renders/con-subs.mp4 video-FINAL.mp4` (dos pasadas de loudnorm: −14 LUFS, pico −1 dBTP) |

## Archivos

- `guion.txt`: el guion tal cual. Es la referencia para comparar con la transcripción.
- `guion_voz.txt`: lo que lee la voz. Igual que `guion.txt`, pero «Jason» va escrito «Yéison» y «Bonnie y Clyde» va escrito «Boni y Claid», porque la voz en español los leía mal. Si cambias el guion, cámbialo en los dos.
- `gen.py`: el generador. Contiene:
  - `P("palabra", n)`: el momento en que se dice esa palabra por n-ésima vez. Todas las apariciones, movimientos de cámara y efectos van colgados de estos tiempos (diccionario `T`).
  - `S`: dónde está cada escena en el lienzo gigante. `SEGS`: el camino que las une.
  - `cam(...)` y `travel(...)`: los movimientos de cámara (acercar, alejar, viajar con desenfoque).
  - `FIX`: cómo se escriben en pantalla los nombres que la voz pronuncia «a la española».
  - `sfx(...)`: dónde suena cada efecto.
- `world.css`: los estilos (colores, tarjetas, tamaños).
- `compositions/world.html`, `compositions/captions.html` e `index.html`: los genera `gen.py`. No los edites a mano, porque se sobrescriben.
- `assets/`: la voz, `transcript.json`, la música, los efectos y los iconos.
  - Música: «Hip Hop 02» de Mixkit (licencia gratuita de Mixkit).
  - Efectos: Mixkit (licencia gratuita de Mixkit).
  - Iconos: Phosphor (licencia MIT).

## Cambiar algo típico

- **Una frase:** edita `guion.txt` y `guion_voz.txt` y ejecuta `./rehacer.sh`. Si quitas una palabra que usa `P(...)`, `gen.py` te dirá cuál falta.
- **La voz:** cambia `--voice em_alex` en `rehacer.sh` (por ejemplo, `ef_dora` es de mujer).
- **El volumen de la música:** `data-volume="0.11"` en `gen.py` (busca `musica`).
- **Los colores de los subtítulos:** `.cw.key` en `gen.py`. Las palabras resaltadas están en `KEY_GOOD` (verde) y `KEY_BAD` (rojo).
