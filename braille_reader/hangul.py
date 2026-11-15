"""한글 음절 → 초성·중성·종성 분해."""

_BASE = 0xAC00
_LAST = 0xD7A3

CHO = "ㄱㄲㄴㄷㄸㄹㅁㅂㅃㅅㅆㅇㅈㅉㅊㅋㅌㅍㅎ"
JUNG = "ㅏㅐㅑㅒㅓㅔㅕㅖㅗㅘㅙㅚㅛㅜㅝㅞㅟㅠㅡㅢㅣ"
JONG = ["", "ㄱ", "ㄲ", "ㄳ", "ㄴ", "ㄵ", "ㄶ", "ㄷ", "ㄹ", "ㄺ", "ㄻ", "ㄼ", "ㄽ", "ㄾ",
        "ㄿ", "ㅀ", "ㅁ", "ㅂ", "ㅄ", "ㅅ", "ㅆ", "ㅇ", "ㅈ", "ㅊ", "ㅋ", "ㅌ", "ㅍ", "ㅎ"]


def is_syllable(ch: str) -> bool:
    return len(ch) == 1 and _BASE <= ord(ch) <= _LAST


def decompose(ch: str) -> tuple[str, str, str]:
    """'각' -> ('ㄱ', 'ㅏ', 'ㄱ'), '가' -> ('ㄱ', 'ㅏ', '')"""
    if not is_syllable(ch):
        raise ValueError(f"한글 음절이 아님: {ch!r}")
    code = ord(ch) - _BASE
    return CHO[code // 588], JUNG[(code % 588) // 28], JONG[code % 28]
