from PIL import Image, ImageDraw

from braille_reader.ocr import clean_text, preprocess


def test_clean_text_keeps_hangul_digits_punctuation():
    assert clean_text(" 가 나1!\n\n다 ") == "가 나1! 다"
    assert clean_text("abc 123 @#") == "123"
    assert clean_text("“가”(3.5)") == "“가”(3.5)"


def test_preprocess_binarizes_and_upscales():
    img = Image.new("RGB", (400, 100), "white")
    ImageDraw.Draw(img).rectangle((50, 30, 100, 60), fill="black")
    out = preprocess(img)
    assert out.width == 1200
    assert set(out.tobytes()) <= {0, 255}
