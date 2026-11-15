"""촬영 버튼을 눌렀을 때 읽을 문자열을 가져오는 방법들."""
from __future__ import annotations

import os
import time

from . import config


class CameraOcrSource:
    """Camera Module 3로 촬영 → OCR."""

    def __init__(self) -> None:
        from picamera2 import Picamera2  # 라즈베리파이에서만 필요

        self._cam = Picamera2()
        self._cam.configure(self._cam.create_still_configuration(
            main={"size": config.CAMERA_RESOLUTION}))
        self._cam.start()
        if config.CAMERA_AUTOFOCUS:
            try:
                from libcamera import controls
                self._cam.set_controls({"AfMode": controls.AfModeEnum.Auto})
            except Exception as e:  # 자동 초점 미지원 카메라여도 계속 진행
                print(f"[카메라] 자동 초점 설정 실패: {e}")
        time.sleep(config.CAMERA_WARMUP_SEC)

    def read_text(self) -> str:
        from .ocr import image_to_text

        if config.CAMERA_AUTOFOCUS:
            try:
                self._cam.autofocus_cycle()
            except Exception as e:
                print(f"[카메라] 초점 맞추기 실패: {e}")
        img = self._cam.capture_image("main").convert("RGB")
        os.makedirs(os.path.dirname(config.CAPTURE_PATH) or ".", exist_ok=True)
        img.save(config.CAPTURE_PATH)
        print(f"[카메라] 촬영 저장: {config.CAPTURE_PATH}")
        return image_to_text(img)

    def close(self) -> None:
        self._cam.stop()


class ImageFileSource:
    """카메라 없이 이미지 파일로 OCR 테스트."""

    def __init__(self, path: str) -> None:
        self.path = path

    def read_text(self) -> str:
        from PIL import Image

        from .ocr import image_to_text

        return image_to_text(Image.open(self.path))

    def close(self) -> None:
        pass


class FixedTextSource:
    """카메라·OCR 없이 정해진 문장을 사용 (점자 출력·버튼 테스트용)."""

    def __init__(self, text: str) -> None:
        self.text = text

    def read_text(self) -> str:
        return self.text

    def close(self) -> None:
        pass
