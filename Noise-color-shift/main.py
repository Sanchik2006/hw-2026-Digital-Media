import cv2
from processor import apply_patina_effect

def main():
    INPUT_FILE  = "test.jpg"
    OUTPUT_FILE = "output.jpg"
    #改变数值调节噪声/色调偏移程度，建议范围：0~1，否则效果可能过强
    PACKAGE_LEVEL = 1
    GREEN_LEVEL = 0

    try:
        im = cv2.imread(INPUT_FILE)#fix:传入BGR uint8图片
        if im is None:
            raise FileNotFoundError(INPUT_FILE)#opencv空输入守卫
        
        res = apply_patina_effect(im, package_level=PACKAGE_LEVEL, green_level=GREEN_LEVEL)
        success=cv2.imwrite(
            OUTPUT_FILE,
            res,
            [cv2.IMWRITE_JPEG_QUALITY, 70]
        )
        if not success:
            raise OSError("图片保存失败")
        print(f"处理成功，图片已经保存为{OUTPUT_FILE}")

    except FileNotFoundError:
        print(f"找不到 {INPUT_FILE}，请在Noise-color-shift文件夹内放入图片")
    except OSError as e:
        print(e)

if __name__ == "__main__":
    main()
