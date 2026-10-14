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
  "1.022+0.00016*on"
  "1.060-0.00020*on"
  "1.030+0.00014*on"
  "1.065-0.00022*on"
  "1.025+0.00017*on"
  "1.060-0.00020*on"
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

# Stage-2 motion test: one illustration per three-second shot. Code behaves like a camera,
# not an illustrator. The short white exposures hide the hard edge between stills without
# introducing the generic glitch language explicitly banned by the art bible.
for i in $(seq 0 5); do
  ffmpeg -y -hide_banner -loglevel error \
    -framerate 30 -loop 1 -t 3 -i "${imgs[$i]}" \
    -vf "scale=2048:1152:flags=lanczos,zoompan=z='${zooms[$i]}':x='${xs[$i]}':y='${ys[$i]}':d=1:s=1920x1080:fps=30,fade=t=in:st=0:d=0.10:color=white,fade=t=out:st=2.90:d=0.10:color=white,noise=alls=0.8:allf=t" \
    -r 30 -an -c:v libx264 -preset veryfast -crf 18 -pix_fmt yuv420p "$SCENES/$i.mp4"
done

cat > "$SCENES/list.txt" <<EOF
file '$SCENES/0.mp4'
file '$SCENES/1.mp4'
file '$SCENES/2.mp4'
file '$SCENES/3.mp4'
file '$SCENES/4.mp4'
file '$SCENES/5.mp4'
EOF

ffmpeg -y -hide_banner -loglevel error -f concat -safe 0 -i "$SCENES/list.txt" -c copy "$OUT_DIR/picture.mp4"

# Temporary original tonal bed for the motion test. Final music is deliberately undecided.
ffmpeg -y -hide_banner -loglevel error \
  -i "$OUT_DIR/picture.mp4" \
  -f lavfi -t 18 -i "aevalsrc=0.026*sin(2*PI*220*t)+0.020*sin(2*PI*277.18*t)+0.016*sin(2*PI*329.63*t)+0.010*sin(2*PI*523.25*t)*exp(-7*mod(t\,2.25))+0.007*sin(2*PI*659.25*t)*exp(-8*mod(t+0.7\,4.5)):s=48000" \
  -filter_complex "[0:v]subtitles='$HERE/hero.ass':fontsdir=/usr/share/fonts,eq=saturation=1.015:contrast=1.005[v];[1:a]highpass=f=55,lowpass=f=8000,afade=t=in:st=0:d=0.9,afade=t=out:st=16.4:d=1.6,volume=0.65[a]" \
  -map '[v]' -map '[a]' -c:v libx264 -preset medium -crf 18 -pix_fmt yuv420p \
  -c:a aac -b:a 192k -movflags +faststart -shortest "$OUT_DIR/gpt_hero_sequence_v1.mp4"

# Decode the entire deliverable. A zero exit status is the gate.
ffmpeg -v error -i "$OUT_DIR/gpt_hero_sequence_v1.mp4" -f null -
ffprobe -v error -show_entries format=duration,size -of json "$OUT_DIR/gpt_hero_sequence_v1.mp4"
