"""메인 루프: 이벤트를 받아 촬영 → OCR → 점자 변환 → 셀 출력/탐색.

이벤트: capture / next / prev / reset / repeat / auto_toggle / quit
자동 읽기 중에는 next·prev가 속도 조절(빠르게·느리게)로 바뀐다. (docs/와이어프레임.md)
"""
from __future__ import annotations

import queue
import time

from . import config
from .braille import text_to_braille
from .display import BaseDisplay
from .navigator import Navigator


class App:
    def __init__(self, display: BaseDisplay, source, events: queue.Queue,
                 abbreviations: bool = True,
                 intervals: list[float] | None = None,
                 start_level: int | None = None) -> None:
        self.display = display
        self.abbreviations = abbreviations
        self.source = source
        self.events = events
        self.nav = Navigator()
        # 자동 읽기: 셀당 머무는 시간(초), 느린 것부터 빠른 것 순서
        self.intervals = list(intervals or config.AUTO_READ_INTERVALS_SEC)
        level = config.AUTO_READ_START_LEVEL if start_level is None else start_level
        self.level = max(0, min(level, len(self.intervals) - 1))
        self.auto = False
        self._deadline = 0.0

    @property
    def interval(self) -> float:
        return self.intervals[self.level]

    def run(self) -> None:
        print("[준비] 촬영 버튼을 누르세요.")
        while True:
            timeout = None
            if self.auto:
                timeout = max(0.0, self._deadline - time.monotonic())
            try:
                event = self.events.get(timeout=timeout)
            except queue.Empty:
                self.auto_step()
                continue
            if event == "quit":
                return
            self.handle(event)

    def handle(self, event: str) -> None:
        if event == "capture":
            self.stop_auto(quiet=True)
            self.capture()
            return
        if self.nav.empty:
            print("[안내] 아직 읽은 문서가 없습니다. 먼저 촬영하세요.")
            return
        if event == "auto_toggle":
            if self.auto:
                self.stop_auto()
            else:
                self.start_auto()
            return
        if self.auto:
            self.handle_auto(event)
            return

        if event == "next":
            moved = self.nav.next()
        elif event == "prev":
            moved = self.nav.prev()
        elif event == "reset":
            self.nav.reset()
            moved = True
        elif event == "repeat":
            moved = True
        else:
            return
        if moved:
            self.show_current()
        else:
            print("[끝] 더 이상 이동할 셀이 없습니다.")
            self.display.end_signal(self.nav.current.mask)

    # ── 자동 읽기 ──────────────────────────────────────────
    def start_auto(self) -> None:
        if self.nav.index == len(self.nav.cells) - 1:
            self.nav.reset()  # 마지막 셀에서 켜면 처음부터
            self.show_current()
        self.auto = True
        self._restart_timer()
        print(f"[자동 읽기] 시작 — 셀당 {self.interval}초 ({self.level + 1}/{len(self.intervals)}단계)")

    def stop_auto(self, quiet: bool = False) -> None:
        if self.auto and not quiet:
            print("[자동 읽기] 정지")
        self.auto = False

    def handle_auto(self, event: str) -> None:
        if event == "next":
            self.change_speed(+1)
        elif event == "prev":
            self.change_speed(-1)
        elif event == "reset":
            self.nav.reset()
            self.show_current()
            self._restart_timer()
        elif event == "repeat":
            self.show_current()
            self._restart_timer()

    def change_speed(self, step: int) -> None:
        new_level = self.level + step
        if not 0 <= new_level < len(self.intervals):
            print("[자동 읽기] 더 이상 바꿀 수 없는 속도입니다.")
            self.display.end_signal(self.nav.current.mask)
            return
        self.level = new_level
        self._restart_timer()
        word = "빠르게" if step > 0 else "느리게"
        print(f"[자동 읽기] {word} — 셀당 {self.interval}초 ({self.level + 1}/{len(self.intervals)}단계)")

    def auto_step(self) -> None:
        """간격이 지나면 다음 셀로. 마지막 셀이면 끝 신호를 주고 멈춘다."""
        if self.nav.next():
            self.show_current()
            self._restart_timer()
        else:
            print("[자동 읽기] 마지막 셀입니다. 자동 읽기를 멈춥니다.")
            self.display.end_signal(self.nav.current.mask)
            self.stop_auto(quiet=True)

    def _restart_timer(self) -> None:
        self._deadline = time.monotonic() + self.interval

    # ── 촬영 / 출력 ────────────────────────────────────────
    def capture(self) -> None:
        print("[촬영] 문서를 읽는 중...")
        self.display.clear()
        try:
            text = self.source.read_text()
        except Exception as e:
            print(f"[오류] 촬영/OCR 실패: {e}")
            self.display.error_signal()
            return
        finally:
            self._drain_events()  # 처리 중에 눌린 버튼은 무시

        result = text_to_braille(text, self.abbreviations)
        print(f"[인식] {text!r}")
        if result.skipped:
            print(f"[건너뜀] 지원하지 않는 문자: {''.join(result.skipped)!r}")
        if not result.cells:
            print("[오류] 읽을 수 있는 한글이 없습니다.")
            self.display.error_signal()
            return
        print(f"[점자] {result.unicode}  ({len(result.cells)}셀)")
        self.nav.load(result.cells)
        self.show_current()

    def show_current(self) -> None:
        cell = self.nav.current
        print(f"[{self.nav.index + 1}/{len(self.nav.cells)}] {cell.unicode}  "
              f"점 {cell.raised or '없음(띄어쓰기)'}  ← {cell.source}")
        self.display.show(cell.mask)

    def _drain_events(self) -> None:
        try:
            while True:
                ev = self.events.get_nowait()
                if ev == "quit":
                    self.events.put("quit")
                    return
        except queue.Empty:
            pass
