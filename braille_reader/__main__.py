"""실행: python -m braille_reader [옵션]

  (옵션 없음)          실제 하드웨어: 카메라 + OCR + 서보 + 버튼
  --mock               부품 없이: 터미널 점자 출력 + 키보드 조작 (문장 기본값 "가나다")
  --mock-display       서보 대신 터미널 출력만
  --keyboard           버튼 대신 키보드 조작만
  --text "문장"        카메라·OCR 대신 이 문장 사용
  --image 파일.jpg     카메라 대신 이 이미지로 OCR
"""
from __future__ import annotations

import argparse
import queue
import sys


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(prog="braille_reader", description="OCR 한글 점자 리더")
    p.add_argument("--mock", action="store_true", help="부품 없이 실행 (--mock-display --keyboard)")
    p.add_argument("--mock-display", action="store_true", help="서보 대신 터미널에 셀 출력")
    p.add_argument("--keyboard", action="store_true", help="버튼 대신 키보드로 조작")
    src = p.add_mutually_exclusive_group()
    src.add_argument("--text", help="카메라·OCR 대신 사용할 문장")
    src.add_argument("--image", help="카메라 대신 OCR할 이미지 파일")
    args = p.parse_args(argv)

    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8")  # Windows 터미널에서 점자/한글 출력

    if args.mock:
        args.mock_display = args.keyboard = True
        if not args.text and not args.image:
            args.text = "가나다"

    from .app import App
    from .controls import GpioControls, KeyboardControls
    from .display import MockDisplay, ServoDisplay
    from .sources import CameraOcrSource, FixedTextSource, ImageFileSource

    events: queue.Queue = queue.Queue()

    display = MockDisplay() if args.mock_display else ServoDisplay()
    if args.text:
        source = FixedTextSource(args.text)
    elif args.image:
        source = ImageFileSource(args.image)
    else:
        source = CameraOcrSource()
    controls = KeyboardControls(events) if args.keyboard else GpioControls(events)

    try:
        App(display, source, events).run()
    except KeyboardInterrupt:
        pass
    finally:
        print("[종료] 돌기를 내리고 장치를 해제합니다.")
        controls.close()
        source.close()
        display.close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
