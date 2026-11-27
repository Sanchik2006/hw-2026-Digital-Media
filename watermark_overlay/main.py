# 新建main用于测试
import cv2
from .watermark import apply_watermark
import numpy as np
from pathlib import Path

HERE = Path(__file__).resolve().parent

INPUT_FILE = HERE / "test.jpg"
OUTPUT_FILE = HERE / "output.jpg"

def main():

    TEXT = "包浆老图"
    POSITION = "center"
    OPACITY = 1.0
    ANGLE = 0
    FONT_SIZE = 150
    IS_TILED = False

    img = cv2.imread(str(INPUT_FILE))

    if img is None:
        print(f"无法读取 {INPUT_FILE}")
        return

    result = apply_watermark(
        img,
        text=TEXT,
        position=POSITION,
        opacity=OPACITY,
        angle=ANGLE,
        font_size=FONT_SIZE,
        is_tiled=IS_TILED,
    )

    success = cv2.imwrite(str(OUTPUT_FILE), result)

    if not success:
        print("图片保存失败")
        return

    h, w = result.shape[:2]

if __name__ == "__main__":
    main()