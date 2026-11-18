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


# ── OCR 엔진 연결 ──────────────────────────────────────
from braille_reader import ocr  # noqa: E402


def test_image_to_text_uses_selected_engine(monkeypatch, tmp_path, capsys):
    monkeypatch.setattr(config, "PROCESSED_PATH", str(tmp_path / "p.png"))
    monkeypatch.setattr(ocr, "_load_rapidocr", lambda: None)
    monkeypatch.setattr(ocr, "_rapidocr_lines", lambda img: [("가나다!", 0.95), ("abc 라", 0.5)])
    text = ocr.image_to_text(Image.new("RGB", (300, 100), "white"), engine="rapidocr")
    assert text == "가나다! 라"                     # 영어는 버리고 줄은 공백으로 합침
    out = capsys.readouterr().out
    assert "2줄" in out and "신뢰도 낮음" in out     # 0.5 < OCR_LOW_CONFIDENCE
    assert (tmp_path / "p.png").exists()            # 전처리 이미지 저장


def test_unknown_engine():
    with pytest.raises(ValueError):
        ocr.image_to_text(Image.new("RGB", (300, 100), "white"), engine="nope")


@pytest.mark.slow
def test_rapidocr_reads_sample_with_shadow():
    """실제 PP-OCRv5 한국어 모델로 그늘진 샘플 사진을 읽는다 (rapidocr 설치 시에만, 처음엔 모델 다운로드)."""
    pytest.importorskip("rapidocr")
    from pathlib import Path
    img = Image.open(Path(__file__).parent.parent / "samples" / "sample_shadow.jpg")
    assert ocr.image_to_text(img, engine="rapidocr") == "점자는 손으로 읽는 글자입니다. 2026년 11월 19일 가나다"
