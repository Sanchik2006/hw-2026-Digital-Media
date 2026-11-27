import cv2 #fix:main中传入传出uint8 ndarry,在函数内转pillow

from .rotate_flip import apply_rotate_flip
from pathlib import Path

HERE = Path(__file__).resolve().parent

INPUT_FILE = HERE / "test.jpg"
OUTPUT_FILE = HERE / "output.jpg"


def main():

    ANGLE = 15              # 旋转角度（度）
    CLOCKWISE = True         # True 顺时针，False 逆时针
    FLIP_HORIZONTAL = False  # 左右镜像
    FLIP_VERTICAL = False    # 上下镜像
    EXPAND = True            # 自动扩大画布，防止裁角

    img = cv2.imread(str(INPUT_FILE)) #cv2.imread失败直接回None
    if img is None:
        print(f"无法读取 {INPUT_FILE}")
        return

    result = apply_rotate_flip(
        img,
        angle=ANGLE,
        clockwise=CLOCKWISE,
        flip_horizontal=FLIP_HORIZONTAL,
        flip_vertical=FLIP_VERTICAL,
        expand=EXPAND,
    )
    success = cv2.imwrite(str(OUTPUT_FILE), result)
    if not success:
        print("图片保存失败")
        return
    
    h, w = result.shape[:2]
    print(f"处理完成：{OUTPUT_FILE} ({w}x{h})")


if __name__ == "__main__":
    main()
