"""이미지 → 한글 문자열 (Tesseract, 오프라인)."""
from __future__ import annotations

import re

from PIL import Image, ImageFilter, ImageOps

from . import config

# 한글, 숫자, 점자로 바꿀 수 있는 문장부호, 공백만 남긴다
_UNSUPPORTED = re.compile(r"[^가-힣0-9\s.?!,·ㆍ:/\-~∼―—()“”‘’…\"']")
_SPACES = re.compile(r"\s+")


def preprocess(img: Image.Image) -> Image.Image:
    """흑백 변환 → 대비 보정 → 노이즈 제거 → 이진화."""
    gray = ImageOps.grayscale(img)
    if gray.width < 1200:  # 너무 작으면 키워야 Tesseract가 잘 읽는다
        scale = 1200 / gray.width
        gray = gray.resize((1200, int(gray.height * scale)), Image.LANCZOS)
    gray = ImageOps.autocontrast(gray, cutoff=1)
    gray = gray.filter(ImageFilter.MedianFilter(3))
    threshold = config.OCR_BINARIZE_THRESHOLD
    if threshold is None:
        threshold = _otsu(gray)
    return gray.point(lambda p: 255 if p > threshold else 0)


def _otsu(gray: Image.Image) -> int:
    hist = gray.histogram()
    total = sum(hist)
    sum_all = sum(i * h for i, h in enumerate(hist))
    sum_b = w_b = 0
    best, best_t = -1.0, 127
    for t in range(256):
        w_b += hist[t]
        if w_b == 0:
            continue
        w_f = total - w_b
        if w_f == 0:
            break
        sum_b += t * hist[t]
        m_b = sum_b / w_b
        m_f = (sum_all - sum_b) / w_f
        between = w_b * w_f * (m_b - m_f) ** 2
        if between > best:
            best, best_t = between, t
    return best_t


def clean_text(raw: str) -> str:
    """점자로 바꿀 수 없는 문자(영어 등)는 버리고 공백을 하나로 합친다."""
    text = _UNSUPPORTED.sub("", raw)
    return _SPACES.sub(" ", text).strip()


def image_to_text(img: Image.Image) -> str:
    import pytesseract  # 실제 OCR을 쓸 때만 필요

    raw = pytesseract.image_to_string(
        preprocess(img),
        lang=config.OCR_LANG,
        config=f"--psm {config.OCR_PSM}",
    )
    print(f"[OCR] 원문: {raw.strip()!r}")
    return clean_text(raw)
