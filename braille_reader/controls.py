"""입력 장치 → 이벤트 큐. 이벤트: capture / next / prev / reset / repeat / auto_toggle / quit"""
from __future__ import annotations

import queue
import threading

from . import config


class ShortOrHold:
    """한 버튼의 짧게 누르기와 길게 누르기를 구분한다 (하드웨어와 무관).

    길게 누르면 누르고 있는 동안 hold_event를 한 번 보내고,
    짧게 눌렀다 떼면 뗄 때 short_event를 보낸다.
    """

    def __init__(self, events: queue.Queue, short_event: str, hold_event: str) -> None:
        self.events = events
        self.short_event = short_event
        self.hold_event = hold_event
        self._held = False

    def pressed(self) -> None:
        self._held = False

    def held(self) -> None:
        self._held = True
        self.events.put(self.hold_event)

    def released(self) -> None:
        if not self._held:
            self.events.put(self.short_event)
        self._held = False


class GpioControls:
    """4버튼 모듈 + (선택) KY-040 엔코더."""

    def __init__(self, events: queue.Queue) -> None:
        from gpiozero import Button  # 라즈베리파이에서만 필요

        self._devices = []
        for pin, name in (
            (config.BUTTON_CAPTURE, "capture"),
            (config.BUTTON_PREV, "prev"),
            (config.BUTTON_RESET, "reset"),
        ):
            btn = Button(pin, pull_up=True, bounce_time=config.BUTTON_BOUNCE_SEC)
            btn.when_pressed = lambda n=name: events.put(n)
            self._devices.append(btn)

        # 다음 버튼: 짧게 = 다음 셀(뗄 때), 길게 = 자동 읽기 켜기/끄기
        nxt = Button(config.BUTTON_NEXT, pull_up=True, bounce_time=config.BUTTON_BOUNCE_SEC,
                     hold_time=config.BUTTON_HOLD_SEC)
        self._next = ShortOrHold(events, "next", "auto_toggle")
        nxt.when_pressed = self._next.pressed
        nxt.when_held = self._next.held
        nxt.when_released = self._next.released
        self._devices.append(nxt)

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


KEY_HELP = ("[키보드] c=촬영  n=다음(자동 읽기 중: 빠르게)  p=이전(느리게)  r=처음부터  "
            "s=다시출력  a=자동 읽기 켜기/끄기(버튼2 길게)  q=종료  (입력 후 Enter)")
_KEYMAP = {"c": "capture", "n": "next", "p": "prev", "r": "reset", "s": "repeat",
           "a": "auto_toggle", "q": "quit"}


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
