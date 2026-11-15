#!/usr/bin/env bash
# Raspberry Pi OS (Bookworm, 64-bit) 설치 스크립트. 저장소 루트에서 실행:  bash scripts/install_pi.sh
set -euo pipefail

sudo apt update
sudo apt install -y \
  python3-venv python3-pip \
  python3-picamera2 python3-libcamera \
  python3-gpiozero python3-lgpio \
  tesseract-ocr tesseract-ocr-kor \
  i2c-tools

# I2C 켜기 (PCA9685)
sudo raspi-config nonint do_i2c 0

# picamera2/gpiozero는 시스템 패키지를 쓰므로 --system-site-packages
python3 -m venv --system-site-packages .venv
.venv/bin/pip install --upgrade pip
.venv/bin/pip install -r requirements.txt

echo
echo "설치 완료. 확인:"
echo "  tesseract --list-langs | grep kor     # kor 가 보여야 함"
echo "  i2cdetect -y 1                         # PCA9685 연결 시 40 이 보여야 함"
echo "  rpicam-hello -t 2000                   # 카메라 미리보기"
echo
echo "실행:  .venv/bin/python -m braille_reader"
