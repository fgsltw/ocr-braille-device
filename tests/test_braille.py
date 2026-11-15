import pytest

from braille_reader.braille import BLANK, dots, text_to_braille
from braille_reader.hangul import decompose
from braille_reader.navigator import Navigator


def u(text):
    """약자 없이 풀어 쓴 결과 (기획안의 기본 자모 규칙)"""
    return text_to_braille(text, abbreviations=False).unicode


def a(text):
    """약자를 적용한 결과"""
    return text_to_braille(text).unicode


def test_dots_matches_unicode_layout():
    assert chr(0x2800 + dots(4)) == "⠈"
    assert chr(0x2800 + dots(1, 2, 6)) == "⠣"
    assert chr(0x2800 + dots(1, 2, 3, 4, 5, 6)) == "⠿"


def test_decompose():
    assert decompose("가") == ("ㄱ", "ㅏ", "")
    assert decompose("닭") == ("ㄷ", "ㅏ", "ㄺ")
    assert decompose("힣") == ("ㅎ", "ㅣ", "ㅎ")


def test_spec_example_ga():
    # 기획안 예시: 가 -> [⠈, ⠣]
    assert u("가") == "⠈⠣"


def test_demo_sentence():
    assert u("가나다") == "⠈⠣⠉⠣⠊⠣"


@pytest.mark.parametrize("text, expected", [
    ("아", "⠣"),          # 초성 ㅇ 생략
    ("오", "⠥"),
    ("우유", "⠍⠩"),
    ("까", "⠠⠈⠣"),        # 된소리 = 된시옷 + ㄱ
    ("싸", "⠠⠠⠣"),
    ("각", "⠈⠣⠁"),        # 받침 ㄱ
    ("강", "⠈⠣⠶"),        # 받침 ㅇ
    ("있", "⠕⠌"),          # 받침 ㅆ = 3-4점
    ("닭", "⠊⠣⠂⠁"),       # 겹받침 ㄺ
    ("의", "⠺"),
    ("왜", "⠧⠗"),          # ㅙ = ㅘ + ㅐ
    ("위", "⠍⠗"),          # ㅟ = ㅜ + ㅐ
    ("예", "⠌"),
    ("하", "⠚⠣"),
])
def test_basic_jamo(text, expected):
    assert u(text) == expected


def test_space_becomes_one_blank_cell():
    result = text_to_braille("  가   나\n", abbreviations=False)
    masks = [c.mask for c in result.cells]
    assert masks == [dots(4), dots(1, 2, 6), BLANK, dots(1, 4), dots(1, 2, 6)]


def test_unsupported_chars_are_skipped():
    result = text_to_braille("가1나!", abbreviations=False)
    assert result.unicode == "⠈⠣⠉⠣"
    assert result.skipped == ["1", "!"]


def test_cell_metadata():
    cell = text_to_braille("가", abbreviations=False).cells[1]
    assert cell.raised == [1, 2, 6]
    assert cell.source == "가:ㅏ"


def test_navigator():
    nav = Navigator(text_to_braille("가나", abbreviations=False).cells)
    assert nav.current.unicode == "⠈"
    assert nav.prev() is False
    for _ in range(3):
        assert nav.next() is True
    assert nav.current.unicode == "⠣"
    assert nav.next() is False
    nav.reset()
    assert nav.index == 0
    assert Navigator().current is None


# ── 약자 ──────────────────────────────────────────────
def test_demo_sentence_with_abbreviations():
    assert a("가나다") == "⠫⠉⠊"


@pytest.mark.parametrize("text, expected", [
    ("사자", "⠇⠨"),
    ("나무", "⠉⠑⠍"),
    ("하마", "⠚⠑"),
    ("까", "⠠⠫"),             # 된소리표 + 가 약자
    ("싸", "⠠⠇"),
    ("따", "⠠⠊"),
    ("각", "⠫⠁"),             # 약자 + 받침
    ("강", "⠫⠶"),
    ("한글", "⠚⠒⠈⠮"),        # 하+ㄴ, ㄱ+을
    ("안녕", "⠣⠒⠉⠻"),        # 아+ㄴ, ㄴ+영
    ("안녕하세요", "⠣⠒⠉⠻⠚⠠⠝⠬"),
    ("것", "⠸⠎"),
    ("껏", "⠠⠸⠎"),
    ("성", "⠠⠻"),             # ㅅ·ㅈ·ㅊ + ㅓㅇ → 영 약자
    ("정", "⠨⠻"),
    ("청", "⠰⠻"),
    ("썽", "⠠⠠⠻"),
    ("경", "⠈⠻"),
    ("선생", "⠠⠾⠠⠗⠶"),
    ("억", "⠹"), ("언", "⠾"), ("얼", "⠞"), ("연", "⠡"), ("열", "⠳"),
    ("영", "⠻"), ("옥", "⠭"), ("온", "⠷"), ("옹", "⠿"), ("운", "⠛"),
    ("울", "⠯"), ("은", "⠵"), ("을", "⠮"), ("인", "⠟"),
    ("볶", "⠘⠭⠁"),           # 겹받침: 옥 약자 + 나머지 ㄱ
])
def test_abbreviations(text, expected):
    assert a(text) == expected


@pytest.mark.parametrize("text, expected", [
    ("나이", "⠉⠣⠕"),          # '나…하' 뒤에 모음이 오면 약자를 쓰지 않음
    ("하얀", "⠚⠣⠜⠒"),
    ("가이", "⠫⠕"),           # '가'는 예외 없음
    ("사이", "⠇⠕"),
    ("나 이", "⠉⠀⠕"),         # 띄어 쓰면 예외 적용 안 함
    ("난이", "⠉⠒⠕"),          # 받침이 있으면 약자 사용
])
def test_abbreviation_exception_before_vowel(text, expected):
    assert a(text) == expected


def test_abbreviation_off_matches_spec_example():
    assert u("가나다") == "⠈⠣⠉⠣⠊⠣"


# ── 약어 ──────────────────────────────────────────────
@pytest.mark.parametrize("text, expected", [
    ("그래서", "⠁⠎"),
    ("그러나", "⠁⠉"),
    ("그러면", "⠁⠒"),
    ("그러므로", "⠁⠢"),
    ("그런데", "⠁⠝"),
    ("그리고", "⠁⠥"),
    ("그리하여", "⠁⠱"),
])
def test_word_abbreviations(text, expected):
    assert a(text) == expected


def test_word_abbreviation_with_suffix():
    # 뒤에 다른 음절이 붙어도 약어 사용: 그래서 + 인(약자) + 지
    assert a("그래서인지") == "⠁⠎⠟⠨⠕"


def test_word_abbreviation_only_at_word_start():
    # 단어 중간이면 약어를 쓰지 않음: 아 + 그(ㄱ ㅡ) + 래(ㄹ ㅐ) + 서(ㅅ ㅓ)
    assert a("아그래서") == "⠣⠈⠪⠐⠗⠠⠎"
    assert a("가 그리고 나") == "⠫⠀⠁⠥⠀⠉"
    assert a("\"그러나") == "⠁⠉"   # 앞의 문장부호는 단어 경계


def test_word_abbreviation_off():
    assert u("그리고") == "⠈⠪⠐⠕⠈⠥"


# ── 모음 연쇄 구분표 (3-6점 ⠤) ────────────────────────────
@pytest.mark.parametrize("text, expected", [
    ("아예", "⠣⠤⠌"),          # 모음 + 예
    ("서예", "⠠⠎⠤⠌"),
    ("도예", "⠊⠥⠤⠌"),
    ("나예", "⠉⠣⠤⠌"),         # '나' 뒤 모음 → 약자 미사용 + 구분표
    ("구애", "⠈⠍⠤⠗"),         # ㅜ + 애 (ㅟ와 구분)
    ("야애", "⠜⠤⠗"),          # ㅑ + 애 (ㅒ와 구분)
    ("과애", "⠈⠧⠤⠗"),         # ㅘ + 애 (ㅙ와 구분)
    ("뭐애", "⠑⠏⠤⠗"),         # ㅝ + 애 (ㅞ와 구분)
])
def test_vowel_separator(text, expected):
    assert a(text) == expected


@pytest.mark.parametrize("text, expected", [
    ("한예", "⠚⠒⠌"),           # 앞 글자에 받침이 있으면 구분표 없음
    ("아 예", "⠣⠀⠌"),          # 띄어 쓰면 구분표 없음
    ("오애", "⠥⠗"),            # ㅗ + 애는 해당 없음
    ("예", "⠌"),
])
def test_no_vowel_separator(text, expected):
    assert a(text) == expected


def test_vowel_separator_without_abbreviations():
    assert u("아예") == "⠣⠤⠌"
    assert u("나예") == "⠉⠣⠤⠌"
