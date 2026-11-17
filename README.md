# OCR 기반 한글 인식 및 촉각 점자 출력 장치 (MVP)

라즈베리파이 카메라로 인쇄된 한글을 찍어 OCR로 읽고, 한글 점자로 바꿔 서보모터 6개로 만든 점자 셀에 한 칸씩 출력하는 장치.

- 기획: [docs/기획안.md](docs/기획안.md)
- 조작 흐름: [docs/와이어프레임.md](docs/와이어프레임.md)
- 배선: [docs/배선도.md](docs/배선도.md)
- 서보 고정·카메라 거치: [docs/기구.md](docs/기구.md)
- 진행 상황: [progress.md](progress.md)

## 부품 없이 PC에서 먼저 해보기

```bash
pip install -r requirements-dev.txt
python -m pytest                       # 점자 변환 테스트
python -m braille_reader --mock        # "가나다"를 터미널 점자 셀로 출력
python -m braille_reader --mock --text "안녕하세요"
python -m braille_reader --mock --text "그리고 안녕"   # 약어 + 약자
python -m braille_reader --mock --text "3시에 만나요!"  # 숫자 + 문장부호
python -m braille_reader --mock --no-abbrev   # 약자·약어 없이 풀어 쓰기
```

`--mock`에서는 키보드로 조작한다: `c`=촬영, `n`=다음, `p`=이전, `r`=처음부터, `s`=다시 출력, `a`=자동 읽기 켜기/끄기, `q`=종료 (입력 후 Enter).

**자동 읽기**: 버튼 2를 1초 이상 누르면(키보드 `a`) 셀이 일정 간격으로 넘어간다. 자동 읽기 중에는 버튼 2/3(`n`/`p`)이 빠르게/느리게(셀당 3.0~0.7초, 5단계)로 바뀌고, 마지막 셀에서 멈춘다. 간격은 `config.py`의 `AUTO_READ_INTERVALS_SEC`에서 바꾼다.

## 부품 도착 후 라즈베리파이에서

### 1. 설치 (한 번만)

Raspberry Pi OS Bookworm 64-bit 기준.

```bash
git clone https://github.com/fgsltw/ocr-braille-device.git
cd ocr-braille-device
bash scripts/install_pi.sh
```

### 2. 단계별 점검 (배선한 부품부터 하나씩)

| 순서 | 연결한 부품 | 명령 | 확인할 것 |
|---|---|---|---|
| 1 | PCA9685 | `i2cdetect -y 1` | 표에 `40` |
| 2 | + 서보 6개 + 5V 어댑터 | `.venv/bin/python -m braille_reader.servo_test` | 점 1→6 순서로 하나씩 올라옴 |
| 3 | (보정) | `.venv/bin/python -m braille_reader.servo_test --angle 1 70` | 각 점의 올림/내림 각도를 찾아 `config.py`에 기록 |
| 4 | | `.venv/bin/python -m braille_reader.servo_test --text 가나다` | ⠫ ⠉ ⠊ 순서로 출력 (약자 끄면 ⠈ ⠣ ⠉ ⠣ ⠊ ⠣) |
| 5 | + 버튼 | `.venv/bin/python -m braille_reader --text 가나다` | 버튼1로 시작, 버튼2/3/4 탐색, 버튼2 길게 누르면 자동 읽기 |
| 6 | + 카메라 | `rpicam-hello -t 2000` | 미리보기가 뜸 |
| 7 | 전체 | `.venv/bin/python -m braille_reader` | 촬영 → OCR → 점자 출력 |

부품 일부만 있을 때는 옵션을 섞어 쓴다.

- 서보 없이: `--mock-display`
- 버튼 없이: `--keyboard`
- 카메라 없이: `--text "문장"` 또는 `--image 사진.jpg`

OCR 결과가 이상하면 마지막 촬영 사진 `captures/last.jpg`와 OCR에 실제로 들어간 흑백 이미지 `captures/last_processed.png`를 확인한다. 문서 바깥이 많이 찍히면 `OCR_CROP`, 글자가 끊기거나 얼룩이 글자로 잡히면 `OCR_ADAPTIVE_RADIUS`·`OCR_ADAPTIVE_OFFSET`(또는 `OCR_THRESHOLD_METHOD = "otsu"`), 그 밖에 `OCR_PSM`(6 또는 7)·`CAMERA_RESOLUTION`을 조정한다.

### 3. 전원 켜면 자동 실행 (선택)

[scripts/braille-reader.service](scripts/braille-reader.service) 안의 안내를 따른다.

## 구조

```
braille_reader/
  config.py      핀 번호, 서보 각도, OCR 설정 (하드웨어 값은 여기만)
  hangul.py      음절 → 초성·중성·종성
  braille.py     한글 → 6점 셀 배열 (기본 규칙, 약자·약어, 모음 연쇄 구분표, 숫자, 문장부호)
  navigator.py   셀 앞뒤 이동
  ocr.py         이미지 전처리(영역 자르기, 적응형 이진화) + Tesseract
  sources.py     카메라+OCR / 이미지 파일 / 고정 문장
  display.py     PCA9685 서보 출력 / 터미널 모의 출력
  controls.py    버튼·엔코더 / 키보드 → 이벤트
  app.py         메인 루프
  servo_test.py  서보 점검·보정 도구
tests/           점자 변환·탐색·OCR 전처리 테스트
hardware/        3D 프린트 모델(.scad)과 출력용 STL — 점자 셀, 카메라 스탠드
```

## MVP에서 지원하지 않는 것

영어, %·@ 같은 기호, 여러 셀 동시 출력. 지원하지 않는 문자는 건너뛰고 터미널에 표시한다.
