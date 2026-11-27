# 测试自定义模式效果

from pathlib import Path

import cv2
import numpy as np

from .pipeline import apply_pipeline


def main():
    HERE = Path(__file__).resolve().parent

    INPUT_FILE = HERE / "test.jpg"
    OUTPUT_FILE = HERE / "output.jpg"

    # 读取原图
    img = cv2.imread(str(INPUT_FILE))

    if img is None:
        print("无法读取测试图片")
        return

    original = img.copy()

    # 调用图像处理流水线
    result = apply_pipeline(
        img,

        remove_params=None,

        rotate_params={
            "angle": 5,
            "clockwise": True,
            "expand": True,
        },

        noise_params={
            "package_level": 0.5,
            "green_level": 0.3,
        },

        watermark_params=[
            {
                "text": "包浆老图",
                "opacity": 0.3,
                "angle": 15,
                "font_size": 50,
            },
            {
                "text": "网络考古",
                "opacity": 0.15,
                "font_size": 30,
                "is_tiled": True,
            },
        ],

        compress_params={
            "age": 10,
        },
    )

    # 接口测试
    assert isinstance(result, np.ndarray)
    assert result.dtype == np.uint8
    assert result.ndim == 3
    assert result.shape[2] == 3
    assert np.array_equal(img, original)
    assert not np.shares_memory(img, result)

    # 保存图片
    if not cv2.imwrite(str(OUTPUT_FILE), result):
        raise OSError("图片保存失败")

    print("集成测试通过")
    print("输入形状:", img.shape)
    print("输出形状:", result.shape)
    print("像素类型:", result.dtype)
    print("输出路径:", OUTPUT_FILE)


if __name__ == "__main__":
    main()