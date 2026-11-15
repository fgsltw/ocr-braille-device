"""점자 셀 배열을 앞뒤로 탐색하는 상태 (하드웨어와 무관)."""
from __future__ import annotations

from .braille import BrailleCell


class Navigator:
    def __init__(self, cells: list[BrailleCell] | None = None):
        self.load(cells or [])

    def load(self, cells: list[BrailleCell]) -> None:
        self.cells = list(cells)
        self.index = 0

    @property
    def empty(self) -> bool:
        return not self.cells

    @property
    def current(self) -> BrailleCell | None:
        return self.cells[self.index] if self.cells else None

    def next(self) -> bool:
        """다음 셀로 이동. 이미 마지막이면 False."""
        if self.index + 1 < len(self.cells):
            self.index += 1
            return True
        return False

    def prev(self) -> bool:
        """이전 셀로 이동. 이미 처음이면 False."""
        if self.index > 0:
            self.index -= 1
            return True
        return False

    def reset(self) -> None:
        self.index = 0
