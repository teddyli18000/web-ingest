#!/usr/bin/env bash
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(cd "$HERE/.." && pwd)"
ASSETS="$ROOT/assets/styleframes"
OUT_DIR="$ROOT/out/hero"
SCENES="$OUT_DIR/scenes"
mkdir -p "$SCENES"

imgs=(
  "$ASSETS/a_new_conversation_a_brighter_tomorrow.png"
  "$ASSETS/dreams_across_the_desk.png"
  "$ASSETS/dreamy_cosmos_of_creative_possibilities.png"
  "$ASSETS/a_wider_world_deeper_conversations.png"
  "$ASSETS/golden_hour_comfort_at_the_desk.png"
  "$ASSETS/reaching_toward_sunrise_together.png"
)
for p in "${imgs[@]}"; do
  [[ -f "$p" ]] || { echo "missing style frame: $p" >&2; exit 2; }
done

zooms=(
  "1.022+0.00015*on"
  "1.060-0.00018*on"
  "1.030+0.00013*on"
  "1.065-0.00020*on"
  "1.025+0.00015*on"
  "1.060-0.00018*on"
)
xs=(
  "(iw-iw/zoom)/2+10*sin(on/38)"
  "(iw-iw/zoom)/2-9*sin(on/44)"
  "(iw-iw/zoom)/2+12*sin(on/52)"
  "(iw-iw/zoom)/2-10*sin(on/48)"
  "(iw-iw/zoom)/2+8*sin(on/56)"
  "(iw-iw/zoom)/2-7*sin(on/60)"
)
ys=(
  "(ih-ih/zoom)/2+5*cos(on/50)"
  "(ih-ih/zoom)/2+7*sin(on/58)"
  "(ih-ih/zoom)/2-6*cos(on/63)"
  "(ih-ih/zoom)/2-5*sin(on/67)"
  "(ih-ih/zoom)/2+5*cos(on/55)"
  "(ih-ih/zoom)/2-8*cos(on/70)"
)

# Code is the camera. It never redraws or deforms the illustrated character.
for i in $(seq 0 5); do
  ffmpeg -y -hide_banner -loglevel error \
    -framerate 30 -loop 1 -t 3.2 -i "${imgs[$i]}" \
    -vf "scale=2048:1152:flags=lanczos,zoompan=z='${zooms[$i]}':x='${xs[$i]}':y='${ys[$i]}':d=1:s=1920x1080:fps=30,noise=alls=0.65:allf=t" \
    -r 30 -an -c:v libx264 -preset veryfast -crf 18 -pix_fmt yuv420p "$SCENES/$i.mp4"
done

# Short, motivated photographic transitions. No generic glitch language.
ffmpeg -y -hide_banner -loglevel error \
  -i "$SCENES/0.mp4" -i "$SCENES/1.mp4" -i "$SCENES/2.mp4" \
  -i "$SCENES/3.mp4" -i "$SCENES/4.mp4" -i "$SCENES/5.mp4" \
  -filter_complex "[0:v][1:v]xfade=transition=fade:duration=0.24:offset=2.96[x1];[x1][2:v]xfade=transition=smoothleft:duration=0.24:offset=5.92[x2];[x2][3:v]xfade=transition=fade:duration=0.24:offset=8.88[x3];[x3][4:v]xfade=transition=smoothup:duration=0.24:offset=11.84[x4];[x4][5:v]xfade=transition=fade:duration=0.24:offset=14.80[picture]" \
  -map '[picture]' -an -c:v libx264 -preset veryfast -crf 18 -pix_fmt yuv420p "$OUT_DIR/picture.mp4"

# Temporary original tonal bed for motion review only; final music is deliberately not locked yet.
ffmpeg -y -hide_banner -loglevel error \
  -i "$OUT_DIR/picture.mp4" \
  -f lavfi -t 18 -i "aevalsrc=0.026*sin(2*PI*220*t)+0.020*sin(2*PI*277.18*t)+0.016*sin(2*PI*329.63*t)+0.010*sin(2*PI*523.25*t)*exp(-7*mod(t\,2.25))+0.007*sin(2*PI*659.25*t)*exp(-8*mod(t+0.7\,4.5)):s=48000" \
  -filter_complex "[0:v]subtitles='$HERE/hero.ass':fontsdir=/usr/share/fonts,eq=saturation=1.015:contrast=1.005[v];[1:a]highpass=f=55,lowpass=f=8000,afade=t=in:st=0:d=0.9,afade=t=out:st=16.5:d=1.5,volume=0.65[a]" \
  -map '[v]' -map '[a]' -c:v libx264 -preset medium -crf 18 -pix_fmt yuv420p \
  -c:a aac -b:a 192k -movflags +faststart -shortest "$OUT_DIR/gpt_hero_sequence.mp4"

# Full decode is the minimum technical gate.
ffmpeg -v error -i "$OUT_DIR/gpt_hero_sequence.mp4" -f null -
ffprobe -v error -show_entries format=duration,size -of json "$OUT_DIR/gpt_hero_sequence.mp4"
