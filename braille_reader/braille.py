"""한글 → 6점 점자 셀 변환 (한국 점자 규정 기본 자모 규칙).

셀은 int 비트마스크로 표현한다. 점 n이 올라오면 bit (n-1)이 1이다.
이는 유니코드 점자 블록(U+2800 + mask)과 같은 배치라 디버깅이 쉽다.

MVP 범위 (docs/기획안.md):
  - 한글 완성형 음절(가-힣), 공백
  - 초성 ㅇ 생략, 된소리는 된시옷(점 6) + 자음
  - 약자 (abbreviations=True일 때): 가·나·다…하, 것, 억·언·얼·연·열·영·옥·온·옹·운·울·은·을·인
  - 약어 (abbreviations=True일 때): 그래서 그러나 그러면 그러므로 그런데 그리고 그리하여
  - 숫자, 문장부호, 모음 연쇄 구분표는 아직 지원하지 않음
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


# ── 약자 ──────────────────────────────────────────────
# '가', '사'는 고유한 약자 칸이 있다
_A_OWN_CELL = {"ㄱ": dots(1, 2, 4, 6), "ㅅ": dots(1, 2, 3)}
# '나, 다, 마, 바, 자, 카, 타, 파, 하'는 'ㅏ'를 생략하고 초성만 적는다
_A_OMITTED = {"ㄴ", "ㄷ", "ㅁ", "ㅂ", "ㅈ", "ㅋ", "ㅌ", "ㅍ", "ㅎ"}
# 모음+받침 약자 (억 언 얼 연 열 영 옥 온 옹 운 울 은 을 인). 앞에 초성이 와도 쓴다
_RIME = {
    ("ㅓ", "ㄱ"): dots(1, 4, 5, 6),
    ("ㅓ", "ㄴ"): dots(2, 3, 4, 5, 6),
    ("ㅓ", "ㄹ"): dots(2, 3, 4, 5),
    ("ㅕ", "ㄴ"): dots(1, 6),
    ("ㅕ", "ㄹ"): dots(1, 2, 5, 6),
    ("ㅕ", "ㅇ"): dots(1, 2, 4, 5, 6),
    ("ㅗ", "ㄱ"): dots(1, 3, 4, 6),
    ("ㅗ", "ㄴ"): dots(1, 2, 3, 5, 6),
    ("ㅗ", "ㅇ"): dots(1, 2, 3, 4, 5, 6),
    ("ㅜ", "ㄴ"): dots(1, 2, 4, 5),
    ("ㅜ", "ㄹ"): dots(1, 2, 3, 4, 6),
    ("ㅡ", "ㄴ"): dots(1, 3, 5, 6),
    ("ㅡ", "ㄹ"): dots(2, 3, 4, 6),
    ("ㅣ", "ㄴ"): dots(1, 2, 3, 4, 5),
}
_GEOT = (dots(4, 5, 6), dots(2, 3, 4))  # 것
# '성, 썽, 정, 쩡, 청'은 'ㅅ, ㅆ, ㅈ, ㅉ, ㅊ' 다음에 '영' 약자를 적는다
_SEONG_INITIALS = {"ㅅ", "ㅈ", "ㅊ"}
_TENSE_BASE = {"ㄲ": "ㄱ", "ㄸ": "ㄷ", "ㅃ": "ㅂ", "ㅆ": "ㅅ", "ㅉ": "ㅈ"}
# 겹받침 → (첫 받침, 나머지 받침)
_JONG_SPLIT = {"ㄲ": ("ㄱ", "ㄱ"), "ㄳ": ("ㄱ", "ㅅ"), "ㄵ": ("ㄴ", "ㅈ"), "ㄶ": ("ㄴ", "ㅎ"),
               "ㄺ": ("ㄹ", "ㄱ"), "ㄻ": ("ㄹ", "ㅁ"), "ㄼ": ("ㄹ", "ㅂ"), "ㄽ": ("ㄹ", "ㅅ"),
               "ㄾ": ("ㄹ", "ㅌ"), "ㄿ": ("ㄹ", "ㅍ"), "ㅀ": ("ㄹ", "ㅎ"), "ㅄ": ("ㅂ", "ㅅ")}


# ── 약어 ──────────────────────────────────────────────
# 단어 첫머리에서만 쓴다. 뒤에 다른 음절이 붙어도 쓴다 (예: 그래서인지).
_GEU = dots(1)
WORD_ABBREVIATIONS: dict[str, tuple[int, ...]] = {
    "그리하여": (_GEU, dots(1, 5, 6)),
    "그러므로": (_GEU, dots(2, 6)),
    "그래서": (_GEU, dots(2, 3, 4)),
    "그러나": (_GEU, dots(1, 4)),
    "그러면": (_GEU, dots(2, 5)),
    "그런데": (_GEU, dots(1, 3, 4, 5)),
    "그리고": (_GEU, dots(1, 3, 6)),
}
_WORDS_LONGEST_FIRST = sorted(WORD_ABBREVIATIONS, key=len, reverse=True)


def _match_word_abbreviation(text: str, i: int) -> str | None:
    """text[i]가 단어 첫머리이고 약어로 시작하면 그 약어를 돌려준다."""
    if i > 0 and is_syllable(text[i - 1]):
        return None  # 단어 중간 (예: 아그래서)
    for word in _WORDS_LONGEST_FIRST:
        if text.startswith(word, i):
            return word
    return None


def _starts_with_vowel(ch: str | None) -> bool:
    return ch is not None and is_syllable(ch) and decompose(ch)[0] == "ㅇ"


def _abbreviated_masks(ch: str, next_ch: str | None) -> list[int] | None:
    """약자로 적을 수 있으면 셀 목록, 아니면 None."""
    cho, jung, jong = decompose(ch)
    tense = cho in _TENSE_BASE
    base = _TENSE_BASE.get(cho, cho)
    prefix = [_DOEN] if tense else []

    # 것, 껏
    if base == "ㄱ" and jung == "ㅓ" and jong == "ㅅ":
        return prefix + list(_GEOT)

    # 가 사 / 나 다 마 바 자 카 타 파 하 (+ 된소리, + 받침)
    if jung == "ㅏ" and (base in _A_OWN_CELL or base in _A_OMITTED):
        # '나…하' 뒤에 모음으로 시작하는 글자가 오면 약자를 쓰지 않는다 (예: 나이)
        if base in _A_OMITTED and not jong and _starts_with_vowel(next_ch):
            return None
        head = _A_OWN_CELL.get(base) or CHOSEONG[base][0]
        return prefix + [head] + list(JONGSEONG[jong])

    # 모음+받침 약자 (예: 선 = ㅅ + 언, 한글의 글 = ㄱ + 을)
    if jong:
        first, rest = _JONG_SPLIT.get(jong, (jong, ""))
        rime = _RIME.get((jung, first))
        if rime is None and base in _SEONG_INITIALS and jung == "ㅓ" and first == "ㅇ":
            rime = _RIME[("ㅕ", "ㅇ")]
        if rime is not None:
            return list(CHOSEONG[cho]) + [rime] + list(JONGSEONG[rest])
    return None


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


def syllable_to_cells(ch: str, next_ch: str | None = None,
                      abbreviations: bool = True) -> list[BrailleCell]:
    if abbreviations:
        masks = _abbreviated_masks(ch, next_ch)
        if masks is not None:
            return [BrailleCell(m, f"{ch}:약자") for m in masks]
    cho, jung, jong = decompose(ch)
    cells = [BrailleCell(m, f"{ch}:{cho}") for m in CHOSEONG[cho]]
    cells += [BrailleCell(m, f"{ch}:{jung}") for m in JUNGSEONG[jung]]
    cells += [BrailleCell(m, f"{ch}:{jong}") for m in JONGSEONG[jong]]
    return cells


def text_to_braille(text: str, abbreviations: bool = True) -> ConversionResult:
    """문자열을 점자 셀 배열로 변환한다.

    공백·줄바꿈은 빈 셀 하나로 합치고, 앞뒤 공백은 버린다.
    지원하지 않는 문자는 건너뛰고 skipped에 기록한다.
    abbreviations=False면 약자·약어 없이 자모를 모두 풀어 쓴다 (예: 가 → ⠈⠣).
    """
    cells: list[BrailleCell] = []
    skipped: list[str] = []
    pending_space = False
    i = 0
    while i < len(text):
        ch = text[i]
        if ch.isspace():
            pending_space = bool(cells)
            i += 1
            continue
        if not is_syllable(ch):
            skipped.append(ch)
            i += 1
            continue
        if pending_space:
            cells.append(BrailleCell(BLANK, " "))
            pending_space = False
        word = _match_word_abbreviation(text, i) if abbreviations else None
        if word:
            cells.extend(BrailleCell(m, f"{word}:약어") for m in WORD_ABBREVIATIONS[word])
            i += len(word)
            continue
        next_ch = text[i + 1] if i + 1 < len(text) else None
        cells.extend(syllable_to_cells(ch, next_ch, abbreviations))
        i += 1
    return ConversionResult(cells, skipped)
