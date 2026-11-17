"""3D 출력 업체 견적·주문용 파일 묶음을 만든다.

    python hardware/make_order.py

결과: hardware/order/ 에 업로드용 STL(파일 이름에 묶음·수량 표시)과 주문서.md,
그리고 저장소 루트에 order_files.zip (git에는 올리지 않음).
STL을 다시 만들었다면(export_stl.sh) 이 스크립트도 다시 실행한다.
"""
from __future__ import annotations

import shutil
import zipfile
from pathlib import Path

HW = Path(__file__).resolve().parent
STL = HW / "stl"
OUT = HW / "order"
ZIP = HW.parent / "order_files.zip"

STANDARD = "PLA, 레이어 0.2mm, 인필 20%, 벽 3줄"

# (묶음, 원본 STL, 수량, 출력 설정, 메모)
#  A = SG90 치수와 상관없음 → 지금 주문 가능
#  B = SG90 치수에 맞춰야 함 → 서보 도착 후 치수 확인하고 주문 (견적은 지금 받아도 됨)
PARTS = [
    ("A", "cell_lid", 1, STANDARD, "점자 셀 뚜껑. 손가락 닿는 면이 바닥(출력판)에 닿게"),
    ("A", "cell_pin", 8, "PLA, 레이어 0.12~0.16mm, 인필 100%", "핀 지름 3.0mm. 세워서 출력"),
    ("A", "cell_pin_d2.9", 8, "PLA, 레이어 0.12~0.16mm, 인필 100%", "핀 지름 2.9mm (예비 굵기)"),
    ("A", "cell_pin_d2.8", 8, "PLA, 레이어 0.12~0.16mm, 인필 100%", "핀 지름 2.8mm (예비 굵기)"),
    ("A", "stand_base", 1, STANDARD, "카메라 스탠드 받침"),
    ("A", "stand_column", 3, STANDARD, "카메라 스탠드 기둥. 세워서(돌기가 위)"),
    ("A", "stand_arm", 1, STANDARD, "카메라 스탠드 팔. 가는 핀(지름 1.9·2.3mm)이 있음"),
    ("B", "cell_base", 1, STANDARD, "점자 셀 상자"),
    ("B", "cell_servo_mount", 7, STANDARD, "서보 받침판 6 + 예비 1"),
    ("B", "cell_lever_a", 5, "PLA, 레이어 0.2mm, 인필 100%", "레버(점 1·3·4·6) 4 + 예비 1. 끝부분이 2mm로 얇음(일부러 휘게 설계)"),
    ("B", "cell_lever_b", 3, "PLA, 레이어 0.2mm, 인필 100%", "레버(점 2·5) 2 + 예비 1"),
]

REQUEST = """\
[요청사항 — 견적/주문 메모에 붙여 넣기]
- 소재: PLA (색상 무관)
- 기본 설정: 레이어 0.2mm, 인필 20%, 벽 3줄. 파일은 출력 방향으로 놓여 있으니 회전하지 말아 주세요.
- 서포트 없이 출력되도록 설계했습니다.
- 예외:
  * cell_lever_a / cell_lever_b: 인필 100% (얇게 휘는 부분이 있어 끊어지지 않게)
  * cell_pin, cell_pin_d2.9, cell_pin_d2.8: 레이어 0.12~0.16mm, 인필 100%, 세워서 출력
- 파일 이름 끝의 _x숫자 = 수량입니다.
- cell_lid의 지름 3.3mm 구멍 6개에 핀이 미끄러져 움직여야 합니다. 구멍이 막히거나 작아지지 않게 부탁드립니다.
- 얇은 부분: 레버 끝 2mm, 스탠드 팔의 핀 지름 1.9mm / 2.3mm, 핀 지름 2.8~3.0mm.
"""


def stl_stats(path: Path) -> tuple[tuple[float, float, float], float]:
    """(가로, 세로, 높이) mm 와 부피 cm³ (ASCII STL)."""
    verts, vol, tri = [], 0.0, []
    for line in path.read_text().splitlines():
        line = line.strip()
        if line.startswith("vertex"):
            v = tuple(float(x) for x in line.split()[1:])
            verts.append(v)
            tri.append(v)
            if len(tri) == 3:
                a, b, c = tri
                vol += (a[0] * (b[1] * c[2] - b[2] * c[1]) - a[1] * (b[0] * c[2] - b[2] * c[0])
                        + a[2] * (b[0] * c[1] - b[1] * c[0])) / 6
                tri = []
    size = tuple(max(v[i] for v in verts) - min(v[i] for v in verts) for i in range(3))
    return size, abs(vol) / 1000


def main() -> None:
    if OUT.exists():
        shutil.rmtree(OUT)
    OUT.mkdir()
    rows = {"A": [], "B": []}
    files = []
    for group, name, qty, setting, memo in PARTS:
        src = STL / f"{name}.stl"
        dst = OUT / f"{group}_{name}_x{qty}.stl"
        shutil.copyfile(src, dst)
        files.append(dst)
        (w, d, h), vol = stl_stats(src)
        rows[group].append(f"| `{dst.name}` | {qty} | {w:.0f} × {d:.0f} × {h:.0f} | {vol:.1f} | {setting} | {memo} |")

    head = "| 업로드 파일 | 수량 | 크기 (mm) | 부피 1개 (cm³) | 출력 설정 | 메모 |\n|---|---:|---|---:|---|---|"
    sheet = f"""# 3D 출력 주문서

모든 파일은 단위 mm, 출력 방향으로 놓인 STL이다. 업로드할 때 파일마다 **수량**을 표의 값으로 넣는다 (파일 이름 끝 `_x숫자`).

## A 묶음 — 지금 주문 가능 (SG90 치수와 상관없음)

{head}
{chr(10).join(rows["A"])}

## B 묶음 — 서보 도착 후 치수 확인하고 주문 (견적은 지금 받아도 됨)

SG90은 제조사마다 치수가 조금씩 다르다. 서보가 오면 `hardware/braille_cell.scad`의 `[SG90 치수]` 값을 재서 고치고,
`bash hardware/export_stl.sh` → `python hardware/make_order.py`로 파일을 다시 만든 뒤 주문한다.

{head}
{chr(10).join(rows["B"])}

## 핀 굵기를 세 가지로 주문하는 이유

업체 출력은 받기까지 며칠이 걸려 "시험 출력 → 확인"을 반복하기 어렵다. 뚜껑 구멍은 지름 3.3mm로 고정하고
핀만 3.0 / 2.9 / 2.8mm로 받아, 구멍에서 걸리지도 흔들리지도 않는 핀 6개를 고른다. 핀은 아주 작아 비용이 거의 들지 않는다.

```
{REQUEST}```
"""
    (OUT / "주문서.md").write_text(sheet, encoding="utf-8")

    with zipfile.ZipFile(ZIP, "w", zipfile.ZIP_DEFLATED) as z:
        for f in files + [OUT / "주문서.md"]:
            z.write(f, f.name)
    print(f"{len(files)}개 파일 → {OUT}")
    print(f"zip → {ZIP}")


if __name__ == "__main__":
    main()
