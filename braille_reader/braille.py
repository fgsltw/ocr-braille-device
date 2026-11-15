"""한글 → 6점 점자 셀 변환 (한국 점자 규정 기본 자모 규칙).

셀은 int 비트마스크로 표현한다. 점 n이 올라오면 bit (n-1)이 1이다.
이는 유니코드 점자 블록(U+2800 + mask)과 같은 배치라 디버깅이 쉽다.

MVP 범위 (docs/기획안.md):
  - 한글 완성형 음절(가-힣), 공백
  - 초성 ㅇ 생략, 된소리는 된시옷(점 6) + 자음
  - 약자·약어, 숫자, 문장부호, 모음 연쇄 구분표는 아직 지원하지 않음
"""
from __future__ import annotations

from dataclasses import dataclass

from .hangul import decompose, is_syllable


def dots(*nums: int) -> int:
    """dots(1, 2, 6) -> 점 1·2·6이 올라온 셀 비트마스크."""
    mask = 0
    for n in nums:
        if not 1 <= n <= 6:
            raise ValueError(f"점 번호는 1~6: {n}")
        mask |= 1 << (n - 1)
    return mask


BLANK = 0

# ── 초성 ──────────────────────────────────────────────
_DOEN = dots(6)  # 된소리표(된시옷)
CHOSEONG: dict[str, tuple[int, ...]] = {
    "ㄱ": (dots(4),),
    "ㄴ": (dots(1, 4),),
    "ㄷ": (dots(2, 4),),
    "ㄹ": (dots(5),),
    "ㅁ": (dots(1, 5),),
    "ㅂ": (dots(4, 5),),
    "ㅅ": (dots(6),),
    "ㅇ": (),  # 초성 ㅇ은 적지 않는다
    "ㅈ": (dots(4, 6),),
    "ㅊ": (dots(5, 6),),
    "ㅋ": (dots(1, 2, 4),),
    "ㅌ": (dots(1, 2, 5),),
    "ㅍ": (dots(1, 4, 5),),
    "ㅎ": (dots(2, 4, 5),),
}
for _plain, _tense in (("ㄱ", "ㄲ"), ("ㄷ", "ㄸ"), ("ㅂ", "ㅃ"), ("ㅅ", "ㅆ"), ("ㅈ", "ㅉ")):
    CHOSEONG[_tense] = (_DOEN,) + CHOSEONG[_plain]

# ── 중성 ──────────────────────────────────────────────
_AE = dots(1, 2, 3, 5)
JUNGSEONG: dict[str, tuple[int, ...]] = {
    "ㅏ": (dots(1, 2, 6),),
    "ㅑ": (dots(3, 4, 5),),
    "ㅓ": (dots(2, 3, 4),),
    "ㅕ": (dots(1, 5, 6),),
    "ㅗ": (dots(1, 3, 6),),
    "ㅛ": (dots(3, 4, 6),),
    "ㅜ": (dots(1, 3, 4),),
    "ㅠ": (dots(1, 4, 6),),
    "ㅡ": (dots(2, 4, 6),),
    "ㅣ": (dots(1, 3, 5),),
    "ㅐ": (_AE,),
    "ㅔ": (dots(1, 3, 4, 5),),
    "ㅒ": (dots(3, 4, 5), _AE),
    "ㅖ": (dots(3, 4),),
    "ㅘ": (dots(1, 2, 3, 6),),
    "ㅙ": (dots(1, 2, 3, 6), _AE),
    "ㅚ": (dots(1, 3, 4, 5, 6),),
    "ㅝ": (dots(1, 2, 3, 4),),
    "ㅞ": (dots(1, 2, 3, 4), _AE),
    "ㅟ": (dots(1, 3, 4), _AE),
    "ㅢ": (dots(2, 4, 5, 6),),
}

# ── 종성 ──────────────────────────────────────────────
_JONG_SINGLE: dict[str, int] = {
    "ㄱ": dots(1),
    "ㄴ": dots(2, 5),
    "ㄷ": dots(3, 5),
    "ㄹ": dots(2),
    "ㅁ": dots(2, 6),
    "ㅂ": dots(1, 2),
    "ㅅ": dots(3),
    "ㅇ": dots(2, 3, 5, 6),
    "ㅈ": dots(1, 3),
    "ㅊ": dots(2, 3),
    "ㅋ": dots(2, 3, 5),
    "ㅌ": dots(2, 3, 6),
    "ㅍ": dots(2, 5, 6),
    "ㅎ": dots(3, 5, 6),
}
JONGSEONG: dict[str, tuple[int, ...]] = {"": ()}
JONGSEONG.update({k: (v,) for k, v in _JONG_SINGLE.items()})
JONGSEONG["ㅆ"] = (dots(3, 4),)  # 받침 ㅆ은 3-4점 한 칸으로 적는다
# 겹받침은 두 받침을 차례로 적는다
for _pair, (_a, _b) in {
    "ㄲ": ("ㄱ", "ㄱ"),
    "ㄳ": ("ㄱ", "ㅅ"),
    "ㄵ": ("ㄴ", "ㅈ"),
    "ㄶ": ("ㄴ", "ㅎ"),
    "ㄺ": ("ㄹ", "ㄱ"),
    "ㄻ": ("ㄹ", "ㅁ"),
    "ㄼ": ("ㄹ", "ㅂ"),
    "ㄽ": ("ㄹ", "ㅅ"),
    "ㄾ": ("ㄹ", "ㅌ"),
    "ㄿ": ("ㄹ", "ㅍ"),
    "ㅀ": ("ㄹ", "ㅎ"),
    "ㅄ": ("ㅂ", "ㅅ"),
}.items():
    JONGSEONG[_pair] = (_JONG_SINGLE[_a], _JONG_SINGLE[_b])


@dataclass(frozen=True)
class BrailleCell:
    mask: int      # 올라올 점 비트마스크
    source: str    # 어떤 글자의 어떤 부분인지 (예: "가:ㄱ")

    @property
    def raised(self) -> list[int]:
        """올라오는 점 번호 목록, 예: [1, 2, 6]"""
        return [n for n in range(1, 7) if self.mask & (1 << (n - 1))]

    @property
    def unicode(self) -> str:
        return chr(0x2800 + self.mask)


@dataclass
class ConversionResult:
    cells: list[BrailleCell]
    skipped: list[str]  # 지원하지 않아 건너뛴 문자

    @property
    def unicode(self) -> str:
        return "".join(c.unicode for c in self.cells)


def syllable_to_cells(ch: str) -> list[BrailleCell]:
    cho, jung, jong = decompose(ch)
    cells = [BrailleCell(m, f"{ch}:{cho}") for m in CHOSEONG[cho]]
    cells += [BrailleCell(m, f"{ch}:{jung}") for m in JUNGSEONG[jung]]
    cells += [BrailleCell(m, f"{ch}:{jong}") for m in JONGSEONG[jong]]
    return cells


def text_to_braille(text: str) -> ConversionResult:
    """문자열을 점자 셀 배열로 변환한다.

    공백·줄바꿈은 빈 셀 하나로 합치고, 앞뒤 공백은 버린다.
    지원하지 않는 문자는 건너뛰고 skipped에 기록한다.
    """
    cells: list[BrailleCell] = []
    skipped: list[str] = []
    pending_space = False
    for ch in text:
        if ch.isspace():
            pending_space = bool(cells)
            continue
        if not is_syllable(ch):
            skipped.append(ch)
            continue
        if pending_space:
            cells.append(BrailleCell(BLANK, " "))
            pending_space = False
        cells.extend(syllable_to_cells(ch))
    return ConversionResult(cells, skipped)
