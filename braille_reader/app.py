"""메인 루프: 이벤트를 받아 촬영 → OCR → 점자 변환 → 셀 출력/탐색."""
from __future__ import annotations

import queue

from .braille import text_to_braille
from .display import BaseDisplay
from .navigator import Navigator


class App:
    def __init__(self, display: BaseDisplay, source, events: queue.Queue,
                 abbreviations: bool = True) -> None:
        self.display = display
        self.abbreviations = abbreviations
        self.source = source
        self.events = events
        self.nav = Navigator()

    def run(self) -> None:
        print("[준비] 촬영 버튼을 누르세요.")
        while True:
            event = self.events.get()
            if event == "quit":
                return
            self.handle(event)

    def handle(self, event: str) -> None:
        if event == "capture":
            self.capture()
            return
        if self.nav.empty:
            print("[안내] 아직 읽은 문서가 없습니다. 먼저 촬영하세요.")
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
