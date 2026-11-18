"""이미지 → 한글 문자열 (RapidOCR PP-OCRv5 한국어 또는 Tesseract, 모두 오프라인)."""
from __future__ import annotations

import os
import re
import time

from PIL import Image, ImageChops, ImageFilter, ImageOps

from . import config

# 한글, 숫자, 점자로 바꿀 수 있는 문장부호, 공백만 남긴다
_UNSUPPORTED = re.compile(r"[^가-힣0-9\s.?!,·ㆍ:/\-~∼―—()“”‘’…\"']")
_SPACES = re.compile(r"\s+")


def crop(img: Image.Image, box: tuple[float, float, float, float] | None) -> Image.Image:
    """(왼쪽, 위, 오른쪽, 아래) 0~1 비율로 자른다. 해상도가 바뀌어도 같은 영역이 된다."""
    if box is None:
        return img
    left, top, right, bottom = box
    if not (0 <= left < right <= 1 and 0 <= top < bottom <= 1):
        raise ValueError(f"OCR_CROP 값이 잘못됨: {box}")
    w, h = img.size
    return img.crop((round(left * w), round(top * h), round(right * w), round(bottom * h)))


def preprocess(img: Image.Image) -> Image.Image:
    """영역 자르기 → 흑백 변환 → 확대 → 대비 보정 → 노이즈 제거 → 이진화."""
    gray = ImageOps.grayscale(crop(img, config.OCR_CROP))
    if gray.width < 1200:  # 너무 작으면 키워야 Tesseract가 잘 읽는다
        scale = 1200 / gray.width
        gray = gray.resize((1200, int(gray.height * scale)), Image.LANCZOS)
    gray = ImageOps.autocontrast(gray, cutoff=1)
    gray = gray.filter(ImageFilter.MedianFilter(3))
    threshold = config.OCR_BINARIZE_THRESHOLD
    if threshold is not None:
        return gray.point(lambda p: 255 if p > threshold else 0)
    if config.OCR_THRESHOLD_METHOD == "adaptive":
        return adaptive_threshold(gray, config.OCR_ADAPTIVE_RADIUS, config.OCR_ADAPTIVE_OFFSET)
    t = _otsu(gray)
    return gray.point(lambda p: 255 if p > t else 0)


def adaptive_threshold(gray: Image.Image, radius: float, offset: int) -> Image.Image:
    """주변 평균(가우시안)보다 offset 이상 어두운 픽셀만 글자(검정)로 본다.

    사진 한쪽이 그늘져도 그 부분의 배경은 주변과 밝기가 비슷하므로 흰색으로 남는다.
    (OpenCV adaptiveThreshold(GAUSSIAN_C)와 같은 원리, Pillow만 사용)
    """
    local_mean = gray.filter(ImageFilter.GaussianBlur(radius))
    darker_by = ImageChops.subtract(local_mean, gray)  # 주변보다 어두운 정도 (음수는 0)
    return darker_by.point(lambda d: 0 if d > offset else 255)


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


def image_to_text(img: Image.Image, engine: str | None = None) -> str:
    """전처리한 이미지를 OCR 엔진에 넣고, 점자로 바꿀 수 있는 문자만 남긴 문자열을 돌려준다."""
    engine = engine or config.OCR_ENGINE
    processed = preprocess(img)
    if config.PROCESSED_PATH:
        os.makedirs(os.path.dirname(config.PROCESSED_PATH) or ".", exist_ok=True)
        processed.save(config.PROCESSED_PATH)

    if engine == "rapidocr":
        _load_rapidocr()
    start = time.perf_counter()
    if engine == "rapidocr":
        lines = _rapidocr_lines(processed)
    elif engine == "tesseract":
        lines = _tesseract_lines(processed)
    else:
        raise ValueError(f"알 수 없는 OCR 엔진: {engine!r} (rapidocr 또는 tesseract)")
    elapsed = time.perf_counter() - start

    print(f"[OCR] {engine}, {len(lines)}줄, {elapsed:.2f}초")
    for text, score in lines:
        mark = "  ← 신뢰도 낮음" if score is not None and score < config.OCR_LOW_CONFIDENCE else ""
        conf = f"({score:.2f}) " if score is not None else ""
        print(f"  {conf}{text}{mark}")
    return clean_text("\n".join(text for text, _ in lines))


_rapid_engine = None


def _load_rapidocr() -> None:
    """RapidOCR + PP-OCRv5 한국어 모델 준비. 처음 한 번만 모델을 내려받는다 (약 13MB)."""
    global _rapid_engine
    from rapidocr import LangRec, ModelType, OCRVersion, RapidOCR  # RapidOCR를 쓸 때만 필요

    if _rapid_engine is None:
        t0 = time.perf_counter()
        _rapid_engine = RapidOCR(params={
            "Rec.lang_type": LangRec.KOREAN,
            "Rec.ocr_version": OCRVersion.PPOCRV5,
            "Rec.model_type": ModelType.MOBILE,   # 한국어 모델은 mobile만 있다
            "Global.log_level": "warning",
        })
        print(f"[OCR] 모델 준비 {time.perf_counter() - t0:.2f}초 (처음 한 번만)")


def _rapidocr_lines(processed: Image.Image) -> list[tuple[str, float | None]]:
    import numpy as np  # RapidOCR를 쓸 때만 필요

    _load_rapidocr()
    result = _rapid_engine(np.array(processed.convert("RGB")))
    return [(t, float(s)) for t, s in zip(result.txts or (), result.scores or ())]


def _tesseract_lines(processed: Image.Image) -> list[tuple[str, float | None]]:
    import pytesseract  # Tesseract를 쓸 때만 필요

    raw = pytesseract.image_to_string(processed, lang=config.OCR_LANG,
                                      config=f"--psm {config.OCR_PSM}")
    return [(line, None) for line in raw.splitlines() if line.strip()]
