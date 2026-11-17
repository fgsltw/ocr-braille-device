"""하드웨어 설정값. 배선이나 기구물이 바뀌면 이 파일만 고친다. (docs/배선도.md 참고)"""

# ── PCA9685 / 서보 ─────────────────────────────────────
PCA9685_ADDRESS = 0x40
PCA9685_CHANNELS = 16          # 보드의 전체 채널 수
SERVO_FREQUENCY_HZ = 50

# 점 1~6 → PCA9685 채널
SERVO_CHANNELS = [0, 1, 2, 3, 4, 5]

# SG90 펄스 폭 범위 (µs). 끝까지 돌지 않거나 떨리면 조정
SERVO_MIN_PULSE_US = 500
SERVO_MAX_PULSE_US = 2400

# 점 1~6 각각의 "돌기 올림 / 내림" 각도.
# 서보를 거꾸로 달았다면 해당 점의 두 값을 서로 바꾸면 된다.
# 실제 값은 `python -m braille_reader.servo_test` 로 맞춘다.
# 3D 프린트 셀(hardware/)은 혼을 90°에서 수평으로 끼우므로 올림 ≈ 90 ± 3~5, 내림 ≈ 올림에서 8~10° 반대쪽.
SERVO_UP_ANGLE = [60, 60, 60, 60, 60, 60]
SERVO_DOWN_ANGLE = [90, 90, 90, 90, 90, 90]

SERVO_STAGGER_SEC = 0.03   # 서보를 동시에 움직이면 순간 전류가 커서 조금씩 시차를 둔다
SERVO_SETTLE_SEC = 0.35    # 움직임이 끝날 때까지 기다리는 시간
# True면 이동 후 PWM을 끊어 떨림·발열을 줄인다 (대신 손가락 압력에 돌기가 밀릴 수 있음)
SERVO_RELEASE_AFTER_MOVE = False

# ── 버튼 (BCM 번호, 누르면 GND) ─────────────────────────
BUTTON_CAPTURE = 17
BUTTON_NEXT = 27
BUTTON_PREV = 22
BUTTON_RESET = 23
BUTTON_BOUNCE_SEC = 0.05
BUTTON_HOLD_SEC = 1.0          # 다음 버튼을 이만큼 누르고 있으면 자동 읽기 켜기/끄기

# ── 자동 읽기 (출력 속도) ────────────────────────────────
# 셀당 머무는 시간(초), 느린 것 → 빠른 것. 서보 이동 시간(약 0.5초)보다 길어야 한다
AUTO_READ_INTERVALS_SEC = [3.0, 2.0, 1.5, 1.0, 0.7]
AUTO_READ_START_LEVEL = 1      # 처음 속도 = 위 목록의 몇 번째 (0부터), 1 → 2.0초

# ── KY-040 로터리 엔코더 (추가 기능) ─────────────────────
ENCODER_ENABLED = False
ENCODER_CLK = 5
ENCODER_DT = 6
ENCODER_SW = 13

# ── 점자 ───────────────────────────────────────────────
# True: 약자·약어 사용 (가→⠫, 한글→⠚⠒⠈⠮, 그리고→⠁⠥). False: 자모를 모두 풀어 씀 (가→⠈⠣)
BRAILLE_ABBREVIATIONS = True

# ── 카메라 / OCR ───────────────────────────────────────
CAMERA_RESOLUTION = (2304, 1296)
CAMERA_WARMUP_SEC = 1.5
CAMERA_AUTOFOCUS = True        # Camera Module 3 자동 초점
CAPTURE_PATH = "captures/last.jpg"   # 마지막 촬영 이미지 (OCR 문제 확인용)

OCR_LANG = "kor"
OCR_PSM = 6                    # 6 = 하나의 텍스트 블록으로 가정. 한 줄이면 7도 시도해 볼 것
# 촬영 사진에서 문서 부분만 잘라 OCR한다. (왼쪽, 위, 오른쪽, 아래)를 0~1 비율로.
# 예: (0.1, 0.05, 0.9, 0.95). None = 자르지 않음. 카메라 거치대를 고정한 뒤 captures/last.jpg를 보고 정한다
OCR_CROP = None
# 이진화 방식: "adaptive" = 주변 밝기 기준(조명이 고르지 않을 때 유리), "otsu" = 사진 전체에 임계값 하나
OCR_THRESHOLD_METHOD = "adaptive"
OCR_ADAPTIVE_RADIUS = 15       # 주변 밝기를 볼 범위(픽셀). 글자 획보다 충분히 커야 한다
OCR_ADAPTIVE_OFFSET = 10       # 주변보다 이만큼 더 어두워야 글자로 본다. 얼룩이 글자로 잡히면 키운다
OCR_BINARIZE_THRESHOLD = None  # 숫자(0~255)를 넣으면 위 방식 대신 고정 임계값 사용
PROCESSED_PATH = "captures/last_processed.png"  # OCR에 실제로 들어간 이미지 (문제 확인용)
