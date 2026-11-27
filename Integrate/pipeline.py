#图像处理流水线
#   remove_watermark 去水印
# ->apply_rotate_flip 旋转翻转
# ->apply_patina_effect 噪点和色偏
# ->apply_watermark 叠加新水印
# ->image_compress 图像压缩

import numpy as np

#操作模块导入
from image_compress import image_compress
from noise_color_shift import apply_patina_effect
from rotate_flip import apply_rotate_flip
from watermark_overlay import apply_watermark
from watermark_remove import remove_watermark


def apply_pipeline(
    input_image: np.ndarray,
    remove_params: dict | None = None,
    rotate_params: dict | None = None,
    noise_params: dict | None = None,
    watermark_params: list[dict] | None = None,
    compress_params: dict | None = None,
) -> np.ndarray:
    """
    统一图像处理流水线。
    各模块参数传None->跳过

    ps:watermark_params支持传入多个水印配置
    """

    # 1. 守卫:先审输入图像是否合法?
    if not isinstance(input_image, np.ndarray):
        raise TypeError("输入必须为 numpy 数组")
    if input_image.ndim != 3 or input_image.shape[2] != 3:
        raise ValueError("输入必须为三通道 BGR 图像")
    if input_image.dtype != np.uint8:
        raise TypeError("图像像素类型必须为 uint8")
    if input_image.size == 0:
        raise ValueError("输入图像不能为空")

    result = input_image.copy()

    # 去水印
    if remove_params is not None:
        result = remove_watermark(
            result,
            **remove_params
        )

    # 旋转翻转
    if rotate_params is not None:
        result = apply_rotate_flip(
            result,
            **rotate_params
        )

    # 噪点+色偏
    if noise_params is not None:
        result = apply_patina_effect(
            result,
            **noise_params
        )

    # 叠加新的多层水印
    if watermark_params is not None:
        for params in watermark_params:
            result = apply_watermark(
                result,
                **params
            )

    # 图像压缩
    if compress_params is not None:
        result = image_compress(
            result,
            **compress_params
        )

    return result