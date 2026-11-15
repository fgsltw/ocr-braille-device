import queue
import threading

from braille_reader.app import App
from braille_reader.controls import ShortOrHold
from braille_reader.display import BaseDisplay
from braille_reader.sources import FixedTextSource


class FakeDisplay(BaseDisplay):
    def __init__(self):
        self.shown = []
        self.end_signals = 0

    def show(self, mask):
        self.shown.append(mask)

    def end_signal(self, mask):
        self.end_signals += 1

    def error_signal(self):
        pass


def make_app(text="가나다", intervals=(3.0, 2.0, 1.0), start_level=1):
    display = FakeDisplay()
    events = queue.Queue()
    app = App(display, FixedTextSource(text), events,
              intervals=list(intervals), start_level=start_level)
    return app, display, events


def test_auto_toggle_needs_document():
    app, _, _ = make_app()
    app.handle("auto_toggle")
    assert app.auto is False


def test_auto_reads_to_end_then_stops():
    app, display, _ = make_app()          # 가나다 → 3셀
    app.handle("capture")
    app.handle("auto_toggle")
    assert app.auto
    app.auto_step()
    app.auto_step()
    assert app.nav.index == 2
    app.auto_step()                       # 마지막 셀 → 끝 신호 후 정지
    assert app.auto is False
    assert display.end_signals == 1


def test_speed_change_in_auto_mode():
    app, display, _ = make_app()
    app.handle("capture")
    app.handle("auto_toggle")
    assert app.interval == 2.0
    app.handle("next")                    # 자동 읽기 중 next = 빠르게
    assert app.interval == 1.0
    assert app.nav.index == 0             # 셀은 그대로
    app.handle("next")                    # 가장 빠름 → 끝 신호
    assert app.interval == 1.0
    assert display.end_signals == 1
    app.handle("prev")
    app.handle("prev")
    assert app.interval == 3.0
    app.handle("prev")                    # 가장 느림 → 끝 신호
    assert display.end_signals == 2


def test_speed_is_kept_after_stop():
    app, _, _ = make_app()
    app.handle("capture")
    app.handle("auto_toggle")
    app.handle("next")
    app.handle("auto_toggle")             # 정지
    assert app.auto is False
    app.handle("next")                    # 정지 후 next = 다음 셀
    assert app.nav.index == 1
    app.handle("auto_toggle")
    assert app.interval == 1.0            # 바꾼 속도 유지


def test_auto_from_last_cell_restarts():
    app, _, _ = make_app()
    app.handle("capture")
    app.handle("next")
    app.handle("next")
    app.handle("auto_toggle")
    assert app.nav.index == 0


def test_reset_and_capture_in_auto_mode():
    app, _, _ = make_app()
    app.handle("capture")
    app.handle("auto_toggle")
    app.auto_step()
    app.handle("reset")
    assert app.nav.index == 0 and app.auto
    app.handle("capture")                 # 새 촬영은 자동 읽기를 끈다
    assert app.auto is False


def test_run_loop_advances_on_timer():
    app, display, events = make_app(text="가나다", intervals=(0.01,), start_level=0)
    events.put("capture")
    t = threading.Thread(target=app.run, daemon=True)
    t.start()
    for _ in range(100):                  # 촬영 중에 누른 버튼은 무시되므로 촬영이 끝난 뒤에 켠다
        if not app.nav.empty:
            break
        t.join(timeout=0.01)
    events.put("auto_toggle")
    t.join(timeout=0.5)                   # 자동으로 끝까지 읽고 멈춘 상태
    events.put("quit")
    t.join(timeout=1)
    assert not t.is_alive()
    assert app.nav.index == 2
    assert display.end_signals == 1
    assert app.auto is False


def test_short_or_hold():
    events = queue.Queue()
    b = ShortOrHold(events, "next", "auto_toggle")
    b.pressed()
    b.released()                          # 짧게
    b.pressed()
    b.held()                              # 길게: 누르고 있는 동안 1번
    b.released()                          # 길게 누른 뒤 떼면 아무것도 안 보냄
    got = []
    while not events.empty():
        got.append(events.get())
    assert got == ["next", "auto_toggle"]
