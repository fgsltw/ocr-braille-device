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

# ── KY-040 로터리 엔코더 (추가 기능) ─────────────────────
ENCODER_ENABLED = False
ENCODER_CLK = 5
ENCODER_DT = 6
ENCODER_SW = 13

# ── 점자 ───────────────────────────────────────────────
# True: 약자 사용 (가→⠫, 한글→⠚⠒⠈⠮). False: 자모를 모두 풀어 씀 (가→⠈⠣)
BRAILLE_ABBREVIATIONS = True

# ── 카메라 / OCR ───────────────────────────────────────
CAMERA_RESOLUTION = (2304, 1296)
CAMERA_WARMUP_SEC = 1.5
CAMERA_AUTOFOCUS = True        # Camera Module 3 자동 초점
CAPTURE_PATH = "captures/last.jpg"   # 마지막 촬영 이미지 (OCR 문제 확인용)

OCR_LANG = "kor"
OCR_PSM = 6                    # 6 = 하나의 텍스트 블록으로 가정. 한 줄이면 7도 시도해 볼 것
OCR_BINARIZE_THRESHOLD = None  # None = 자동(Otsu), 숫자(0~255) = 고정 임계값
