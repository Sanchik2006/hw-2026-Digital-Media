# 新建main用于测试
import cv2
from watermark import apply_watermark
import numpy as np

def main():
    INPUT_FILE = "test.jpg"
    OUTPUT_FILE = "output.jpg"

    TEXT = "包浆老图"
    POSITION = "center"
    OPACITY = 1.0
    ANGLE = 0
    FONT_SIZE = 150
    IS_TILED = False

    img = cv2.imread(INPUT_FILE)

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





    # 检查水印是否成功叠加
    diff = cv2.absdiff(img, result)

    print("原图尺寸：", img.shape)
    print("结果尺寸：", result.shape)
    print("最大像素差异：", np.max(diff))
    print("平均像素差异：", np.mean(diff))
    print("发生变化的像素数量：",
        np.count_nonzero(np.any(diff != 0, axis=2)))


    success = cv2.imwrite(OUTPUT_FILE, result)

    if not success:
        print("图片保存失败")
        return

    h, w = result.shape[:2]

if __name__ == "__main__":
    main()