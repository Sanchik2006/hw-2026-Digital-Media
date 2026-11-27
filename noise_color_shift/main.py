import cv2
from .processor import apply_patina_effect
from pathlib import Path

HERE = Path(__file__).resolve().parent

INPUT_FILE = HERE / "test.jpg"
OUTPUT_FILE = HERE / "output.jpg"

def main():
    #改变数值调节噪声/色调偏移程度，建议范围：0~1，否则效果可能过强
    PACKAGE_LEVEL = 1
    GREEN_LEVEL = 0

    try:
        img = cv2.imread(str(INPUT_FILE))#fix:传入BGR uint8图片
        if img is None:
            raise FileNotFoundError(INPUT_FILE)#opencv空输入守卫
        
        result = apply_patina_effect(img, package_level=PACKAGE_LEVEL, green_level=GREEN_LEVEL)
        success=cv2.imwrite(str(OUTPUT_FILE), result)
        if not success:
            raise OSError("图片保存失败")
        print(f"处理成功，图片已经保存为{OUTPUT_FILE}")

    except FileNotFoundError:
        print(f"找不到 {INPUT_FILE}，请在Noise-color-shift文件夹内放入图片")
    except OSError as e:
        print(e)

if __name__ == "__main__":
    main()
