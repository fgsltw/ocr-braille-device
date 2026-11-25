#!/usr/bin/env bash
# .scad 값을 바꾼 뒤 STL을 다시 만든다. 저장소 루트에서: bash hardware/export_stl.sh
set -euo pipefail
cd "$(dirname "$0")"

OPENSCAD="${OPENSCAD:-openscad}"
if ! command -v "$OPENSCAD" >/dev/null 2>&1; then
  for p in "/c/Program Files/OpenSCAD/openscad.com" "/Applications/OpenSCAD.app/Contents/MacOS/OpenSCAD"; do
    [ -x "$p" ] && OPENSCAD="$p" && break
  done
fi

mkdir -p stl
for part in base lid pin pin_set lever_a lever_b lever_set servo_mount mount_set fit_test; do
  echo "braille_cell: $part"
  "$OPENSCAD" -o "stl/cell_${part}.stl" -D "part=\"$part\"" braille_cell.scad
done
# 업체 주문용: 조금 가는 핀 (뚜껑 구멍은 그대로라 여유가 0.1/0.2mm 커진다)
for d in 2.9 2.8; do
  echo "braille_cell: pin d=$d"
  "$OPENSCAD" -o "stl/cell_pin_d${d}.stl" -D 'part="pin"' -D "pin_d=$d" braille_cell.scad
done
for part in stand_base column arm; do
  echo "camera_stand: $part"
  "$OPENSCAD" -o "stl/stand_${part#stand_}.stl" -D "part=\"$part\"" camera_stand.scad
done
echo "완료: hardware/stl/"
