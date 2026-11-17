import pytest
from PIL import Image, ImageDraw

from braille_reader import config
from braille_reader.ocr import clean_text, crop, preprocess


def test_clean_text_keeps_hangul_digits_punctuation():
    assert clean_text(" 가 나1!\n\n다 ") == "가 나1! 다"
    assert clean_text("abc 123 @#") == "123"
    assert clean_text("“가”(3.5)") == "“가”(3.5)"


@pytest.mark.parametrize("method", ["adaptive", "otsu"])
def test_preprocess_binarizes_and_upscales(monkeypatch, method):
    monkeypatch.setattr(config, "OCR_THRESHOLD_METHOD", method)
    img = Image.new("RGB", (400, 100), "white")
    ImageDraw.Draw(img).rectangle((50, 30, 100, 60), fill="black")
    out = preprocess(img)
    assert out.width == 1200
    assert set(out.tobytes()) <= {0, 255}


def shadowed_page():
    """왼쪽이 그늘진(어두운) 종이 위에 글자 획 같은 세로줄들."""
    w, h = 1200, 200
    img = Image.new("L", (w, h))
    for x in range(w):
        bg = 40 + int(200 * x / (w - 1))          # 40(그늘) → 240(밝음)
        for y in range(h):
            img.putpixel((x, y), bg)
    draw = ImageDraw.Draw(img)
    strokes = list(range(60, w - 60, 120))
    for x in strokes:
        draw.rectangle((x, 60, x + 5, 140), fill=0)  # 글자 획
    return img.convert("RGB"), strokes


def white_ratio(img, box):
    region = img.crop(box).tobytes()
    return sum(1 for p in region if p == 255) / len(region)


def test_adaptive_keeps_shadowed_background_white(monkeypatch):
    img, strokes = shadowed_page()
    shadow_bg = (20, 0, 50, 200)                     # 그늘진 왼쪽, 획이 없는 곳

    monkeypatch.setattr(config, "OCR_THRESHOLD_METHOD", "otsu")
    otsu = preprocess(img)
    assert white_ratio(otsu, shadow_bg) < 0.1         # Otsu: 그늘이 통째로 검게 됨

    monkeypatch.setattr(config, "OCR_THRESHOLD_METHOD", "adaptive")
    adaptive = preprocess(img)
    assert white_ratio(adaptive, shadow_bg) > 0.95    # 적응형: 그늘진 배경도 흰색
    for x in strokes:                                 # 획은 어두운 쪽·밝은 쪽 모두 검정
        assert adaptive.getpixel((x + 2, 100)) == 0


def test_crop_uses_ratios():
    img = Image.new("RGB", (100, 50))
    assert crop(img, None).size == (100, 50)
    assert crop(img, (0.1, 0.2, 0.5, 1.0)).size == (40, 40)
    with pytest.raises(ValueError):
        crop(img, (0.5, 0, 0.4, 1))
