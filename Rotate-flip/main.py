from PIL import Image

from rotate_flip import apply_rotate_flip


def main():
    INPUT_FILE = "test.jpg"
    OUTPUT_FILE = "output.jpg"

    ANGLE = 15              # 旋转角度（度）
    CLOCKWISE = True         # True 顺时针，False 逆时针
    FLIP_HORIZONTAL = False  # 左右镜像
    FLIP_VERTICAL = False    # 上下镜像
    EXPAND = True            # 自动扩大画布，防止裁角

    try:
        img = Image.open(INPUT_FILE)
    except FileNotFoundError:
        print(f"找不到 {INPUT_FILE}。请把一张图片放到本文件夹，并命名为 test.jpg")
        return

    result = apply_rotate_flip(
        img,
        angle=ANGLE,
        clockwise=CLOCKWISE,
        flip_horizontal=FLIP_HORIZONTAL,
        flip_vertical=FLIP_VERTICAL,
        expand=EXPAND,
    )
    result.save(OUTPUT_FILE)
    print(f"处理完成：{OUTPUT_FILE}（{result.width}x{result.height}）")


if __name__ == "__main__":
    main()
