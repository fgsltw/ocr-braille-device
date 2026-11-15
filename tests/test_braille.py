import pytest

from braille_reader.braille import BLANK, dots, text_to_braille
from braille_reader.hangul import decompose
from braille_reader.navigator import Navigator


def u(text):
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
    result = text_to_braille("  가   나\n")
    masks = [c.mask for c in result.cells]
    assert masks == [dots(4), dots(1, 2, 6), BLANK, dots(1, 4), dots(1, 2, 6)]


def test_unsupported_chars_are_skipped():
    result = text_to_braille("가1나!")
    assert result.unicode == "⠈⠣⠉⠣"
    assert result.skipped == ["1", "!"]


def test_cell_metadata():
    cell = text_to_braille("가").cells[1]
    assert cell.raised == [1, 2, 6]
    assert cell.source == "가:ㅏ"


def test_navigator():
    nav = Navigator(text_to_braille("가나").cells)
    assert nav.current.unicode == "⠈"
    assert nav.prev() is False
    for _ in range(3):
        assert nav.next() is True
    assert nav.current.unicode == "⠣"
    assert nav.next() is False
    nav.reset()
    assert nav.index == 0
    assert Navigator().current is None
