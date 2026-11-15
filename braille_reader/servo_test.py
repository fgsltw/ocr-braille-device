"""서보 점검·각도 보정 도구 (부품 도착 후 가장 먼저 실행).

  python -m braille_reader.servo_test            점 1~6을 차례로 올렸다 내림
  python -m braille_reader.servo_test --text 가   특정 글자의 셀들을 차례로 출력
  python -m braille_reader.servo_test --angle 1 75
                                                 점 1 서보를 75도로 (보정용)

보정 순서: --angle로 각 점의 '돌기 올림/내림' 각도를 찾아
config.py의 SERVO_UP_ANGLE / SERVO_DOWN_ANGLE에 적는다.
"""
from __future__ import annotations

import argparse
import sys
import time

from . import config


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="servo_test")
    p.add_argument("--angle", nargs=2, type=int, metavar=("DOT", "ANGLE"),
                   help="점 번호(1~6) 서보를 지정 각도(0~180)로")
    p.add_argument("--text", help="이 글자들의 점자 셀을 1초 간격으로 출력")
    p.add_argument("--mock", action="store_true", help="서보 없이 터미널로 확인")
    args = p.parse_args(argv)
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")

    from .display import MockDisplay, ServoDisplay

    if args.angle:
        dot, angle = args.angle
        if not (1 <= dot <= 6 and 0 <= angle <= 180):
            p.error("점은 1~6, 각도는 0~180")
        if args.mock:
            print(f"[mock] 점 {dot} (채널 {config.SERVO_CHANNELS[dot - 1]}) → {angle}도")
            return 0
        from adafruit_servokit import ServoKit

        kit = ServoKit(channels=config.PCA9685_CHANNELS, address=config.PCA9685_ADDRESS)
        servo = kit.servo[config.SERVO_CHANNELS[dot - 1]]
        servo.set_pulse_width_range(config.SERVO_MIN_PULSE_US, config.SERVO_MAX_PULSE_US)
        servo.angle = angle
        print(f"점 {dot} (채널 {config.SERVO_CHANNELS[dot - 1]}) → {angle}도")
        time.sleep(0.5)
        return 0

    display = MockDisplay() if args.mock else ServoDisplay()
    try:
        if args.text:
            from .braille import text_to_braille

            for cell in text_to_braille(args.text).cells:
                print(f"{cell.unicode} 점 {cell.raised} ← {cell.source}")
                display.show(cell.mask)
                time.sleep(1.0)
        else:
            for i in range(6):
                print(f"점 {i + 1} 올림")
                display.show(1 << i)
                time.sleep(0.8)
            print("전체 올림")
            display.show(0b111111)
            time.sleep(1.0)
    finally:
        display.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
