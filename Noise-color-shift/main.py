from PIL import Image
from processor import apply_patina_effect

def main():
    INPUT_FILE  = "test.jpg"
    OUTPUT_FILE = "output.jpg"
    #改变数值调节噪声/色调偏移程度，建议范围：0~1，否则效果可能过强
    PACKAGE_LEVEL = 1
    GREEN_LEVEL = 1

    try:
        im = Image.open(INPUT_FILE)
        res = apply_patina_effect(im, package_level=PACKAGE_LEVEL, green_level=GREEN_LEVEL)
        res.save(OUTPUT_FILE, quality=70)
        print(f"处理成功，图片已经保存为{OUTPUT_FILE}")
    except FileNotFoundError:
        print(f"找不到 {INPUT_FILE}，请在Noise-color-shift文件夹内放入图片")

if __name__ == "__main__":
    main()
