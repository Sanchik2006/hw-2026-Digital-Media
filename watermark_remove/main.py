import sys
from pathlib import Path

import cv2
import numpy as np

from watermark_remove import (
    remove_watermark,
    detect_white_watermark_mask,
)

# 当前文件夹和项目根目录
HERE = Path(__file__).resolve().parent
ROOT = HERE.parent

from watermark_overlay import apply_watermark

from .watermark_remove import (
    remove_watermark,
    detect_white_watermark_mask,
)

from pathlib import Path

HERE = Path(__file__).resolve().parent

INPUT_FILE = HERE / "test.jpg"
OUTPUT_FILE = HERE / "output.jpg"

def main():
    WM_INPUT_FILE = HERE / "watermark_input.jpg"
    WM_REMOVED_FILE = HERE / "watermark_removed.jpg"
    COMPARE_FILE = HERE / "compare.jpg"

     # 1. 读取原图
    original = cv2.imread(str(INPUT_FILE))

    if original is None:
        print("无法读取 test.jpg")
        return

    # 2. 叠加水印
    watermarked = apply_watermark(
        original,
        text="包浆老图",
        position="center",
        opacity=0.3,
        angle=15,
        font_size=50,
    )

    # 自动检测参数
    detect_params = {
        "v_thresh": 200,
        "s_thresh": 40,
        "tophat_thresh": 20,
        "min_area": 30,
    }

    # 3. 保存输入副本，用于检查原图是否被修改
    before = watermarked.copy()

    # 4. 去除水印
    removed = remove_watermark(
        watermarked,
        auto_detect=True,
        inpaint_radius=3,
        feather_sigma=3,
        **detect_params,
    )

    # 5. 验证统一接口
    assert isinstance(removed, np.ndarray)
    assert removed.dtype == np.uint8
    assert removed.shape == watermarked.shape
    assert np.array_equal(watermarked, before)
    assert not np.shares_memory(watermarked, removed)

    print("接口测试通过")

    # 6. 生成三图对比
    h, w = original.shape[:2]

    gap = np.full(
        (h, 10, 3),
        255,
        dtype=np.uint8
    )

    compare = np.concatenate(
        [
            original,
            gap,
            watermarked,
            gap,
            removed,
        ],
        axis=1
    )

    # 7. 保存结果
    outputs = [
        (WM_INPUT_FILE, watermarked),
        (WM_REMOVED_FILE, removed),
        (COMPARE_FILE, compare),
    ]

    for path, image in outputs:
        if not cv2.imwrite(str(OUTPUT_FILE), image):
            raise OSError(f"图片保存失败: {path}")

    # 8. 保存调试掩膜
    mask, debug_info = detect_white_watermark_mask(
        watermarked,
        debug=True,
        **detect_params,
    )

    for name, image in debug_info.items():
        path = HERE / f"_tmp_{name}.png"

        if not cv2.imwrite(str(OUTPUT_FILE), image):
            raise OSError(f"调试图片保存失败: {path}")


if __name__ == "__main__":
    main()