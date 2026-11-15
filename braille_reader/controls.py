"""입력 장치 → 이벤트 큐. 이벤트: capture / next / prev / reset / repeat / quit"""
from __future__ import annotations

import queue
import threading

from . import config


class GpioControls:
    """4버튼 모듈 + (선택) KY-040 엔코더."""

    def __init__(self, events: queue.Queue) -> None:
        from gpiozero import Button  # 라즈베리파이에서만 필요

        self._devices = []
        for pin, name in (
            (config.BUTTON_CAPTURE, "capture"),
            (config.BUTTON_NEXT, "next"),
            (config.BUTTON_PREV, "prev"),
            (config.BUTTON_RESET, "reset"),
        ):
            btn = Button(pin, pull_up=True, bounce_time=config.BUTTON_BOUNCE_SEC)
            btn.when_pressed = lambda n=name: events.put(n)
            self._devices.append(btn)

        if config.ENCODER_ENABLED:
            from gpiozero import RotaryEncoder

            enc = RotaryEncoder(config.ENCODER_CLK, config.ENCODER_DT, max_steps=0)
            enc.when_rotated_clockwise = lambda: events.put("next")
            enc.when_rotated_counter_clockwise = lambda: events.put("prev")
            sw = Button(config.ENCODER_SW, pull_up=True, bounce_time=config.BUTTON_BOUNCE_SEC)
            sw.when_pressed = lambda: events.put("repeat")
            self._devices += [enc, sw]

    def close(self) -> None:
        for d in self._devices:
            d.close()


KEY_HELP = "[키보드] c=촬영  n=다음  p=이전  r=처음부터  s=다시출력  q=종료  (입력 후 Enter)"
_KEYMAP = {"c": "capture", "n": "next", "p": "prev", "r": "reset", "s": "repeat", "q": "quit"}


class KeyboardControls:
    """버튼 대신 키보드로 조작 (부품 없이 테스트)."""

    def __init__(self, events: queue.Queue) -> None:
        print(KEY_HELP)
        threading.Thread(target=self._loop, args=(events,), daemon=True).start()

    @staticmethod
    def _loop(events: queue.Queue) -> None:
        while True:
            try:
                line = input()
            except EOFError:
                events.put("quit")
                return
            for ch in line.strip().lower():
                if ch in _KEYMAP:
                    events.put(_KEYMAP[ch])
                    if ch == "q":
                        return  # 종료 시 input() 대기 중인 스레드가 남지 않도록
                else:
                    print(KEY_HELP)

    def close(self) -> None:
        pass
