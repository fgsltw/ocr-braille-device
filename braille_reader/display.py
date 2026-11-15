"""6점 점자 셀 출력: 실제 서보(PCA9685) 또는 터미널 모의 출력."""
from __future__ import annotations

import time

from . import config


class BaseDisplay:
    def show(self, mask: int) -> None:
        raise NotImplementedError

    def clear(self) -> None:
        self.show(0)

    def end_signal(self, mask: int) -> None:
        """처음/마지막 셀에서 더 이동하려 할 때: 잠깐 내렸다가 다시 올린다."""
        self.clear()
        time.sleep(0.25)
        self.show(mask)

    def error_signal(self) -> None:
        """인식 실패: 돌기 6개를 모두 올렸다 내리기를 2회."""
        for _ in range(2):
            self.show(0b111111)
            time.sleep(0.4)
            self.clear()
            time.sleep(0.3)

    def close(self) -> None:
        self.clear()


class ServoDisplay(BaseDisplay):
    def __init__(self) -> None:
        from adafruit_servokit import ServoKit  # 라즈베리파이에서만 필요

        self._kit = ServoKit(channels=config.PCA9685_CHANNELS,
                             address=config.PCA9685_ADDRESS,
                             frequency=config.SERVO_FREQUENCY_HZ)
        for ch in config.SERVO_CHANNELS:
            self._kit.servo[ch].set_pulse_width_range(config.SERVO_MIN_PULSE_US,
                                                      config.SERVO_MAX_PULSE_US)
        self._state: list[bool | None] = [None] * 6  # 처음엔 모든 서보를 강제로 위치시킴
        self.clear()

    def set_dot(self, dot_index: int, up: bool) -> None:
        angle = config.SERVO_UP_ANGLE[dot_index] if up else config.SERVO_DOWN_ANGLE[dot_index]
        self._kit.servo[config.SERVO_CHANNELS[dot_index]].angle = angle

    def show(self, mask: int) -> None:
        moved = []
        for i in range(6):
            up = bool(mask & (1 << i))
            if self._state[i] is up and not config.SERVO_RELEASE_AFTER_MOVE:
                continue
            self.set_dot(i, up)
            self._state[i] = up
            moved.append(i)
            time.sleep(config.SERVO_STAGGER_SEC)
        if moved:
            time.sleep(config.SERVO_SETTLE_SEC)
            if config.SERVO_RELEASE_AFTER_MOVE:
                for i in moved:
                    self._kit.servo[config.SERVO_CHANNELS[i]].angle = None

    def close(self) -> None:
        self.clear()
        for ch in config.SERVO_CHANNELS:
            self._kit.servo[ch].angle = None


class MockDisplay(BaseDisplay):
    """서보 대신 터미널에 셀을 그린다. ● = 올림, ○ = 내림"""

    def show(self, mask: int) -> None:
        print(render_cell(mask))

    def end_signal(self, mask: int) -> None:
        print("  (끝 신호: 더 이상 이동할 셀 없음)")

    def error_signal(self) -> None:
        print("  (오류 신호: 돌기 6개 깜빡임 ×2)")


def render_cell(mask: int) -> str:
    def d(n: int) -> str:
        return "●" if mask & (1 << (n - 1)) else "○"

    return f"  {d(1)} {d(4)}\n  {d(2)} {d(5)}\n  {d(3)} {d(6)}"
