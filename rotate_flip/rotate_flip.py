"""图片旋转与翻转模块（Rotate-flip）。

主接口：
    apply_rotate_flip(input_img, angle=0, clockwise=True,
                      flip_horizontal=False, flip_vertical=False,
                      expand=True, fill_color=None) -> np.ndarry
"""

from __future__ import annotations

import math
from typing import Optional, Sequence, Tuple, Union

import numpy as np
from PIL import Image

import cv2 #导入OpenCV库

FillColor = Optional[Union[int, Sequence[int]]]


def _round_up(x: float) -> int:
    """向上取整，同时消除 cos(90°) 这类浮点误差。"""
    nearest = round(x)
    if abs(x - nearest) < 1e-6:
        return int(nearest)
    return int(math.ceil(x))


def _default_fill(img: Image.Image) -> Union[int, Tuple[int, ...]]:
    if img.mode == "RGBA":
        return (0, 0, 0, 0)
    if img.mode == "LA":
        return (0, 0)
    if img.mode == "RGB":
        return (0, 0, 0)
    return 0


def _normalise_fill(img: Image.Image, fill_color: FillColor):
    if fill_color is None:
        return _default_fill(img)
    if isinstance(fill_color, int):
        return fill_color
    return tuple(fill_color)


def rotate_image(
    input_img: Image.Image,
    angle: float = 15.0,
    clockwise: bool = True,
    expand: bool = True,
    fill_color: FillColor = None,
    resample=Image.BICUBIC,
) -> Image.Image:
    """按任意角度旋转图片。

    :param input_img: PIL Image
    :param angle: 旋转角度（度），取绝对值；方向由 clockwise 决定
    :param clockwise: True 顺时针，False 逆时针
    :param expand: True 自动扩大画布，避免四角被裁掉
    :param fill_color: 旋转后空白区域颜色；默认 RGB 黑、RGBA 透明
    :return: 新的 PIL Image（不修改原图）
    """
    if angle == 0:
        return input_img.copy()

    theta = math.radians(abs(angle))
    if not clockwise:
        theta = -theta

    w, h = input_img.size
    cos_t, sin_t = math.cos(theta), math.sin(theta)

    if expand:
        out_w = max(1, _round_up(abs(w * cos_t) + abs(h * sin_t)))
        out_h = max(1, _round_up(abs(w * sin_t) + abs(h * cos_t)))
    else:
        out_w, out_h = w, h

    cx, cy = w / 2.0, h / 2.0          # 原图中心
    ocx, ocy = out_w / 2.0, out_h / 2.0  # 输出图中心

    # Pillow 的 AFFINE 需要"输出坐标 -> 输入坐标"的逆变换矩阵。
    # 正向旋转：x' = cosθ(x-cx) - sinθ(y-cy) + ocx
    #           y' = sinθ(x-cx) + cosθ(y-cy) + ocy
    a, b = cos_t, sin_t
    d, e = -sin_t, cos_t
    c = cx - cos_t * ocx - sin_t * ocy
    f = cy + sin_t * ocx - cos_t * ocy

    return input_img.transform(
        (out_w, out_h),
        Image.AFFINE,
        (a, b, c, d, e, f),
        resample=resample,
        fillcolor=_normalise_fill(input_img, fill_color),
    )


def flip_image(input_img: Image.Image, mode: str = "horizontal") -> Image.Image:
    """翻转图片。

    mode:
        "horizontal" 左右镜像（绕竖直对称轴）
        "vertical"   上下镜像（绕水平对称轴）
        "both"       左右 + 上下（等价于旋转 180°）
    """
    if mode == "horizontal":
        slicer = (slice(None), slice(None, None, -1))
    elif mode == "vertical":
        slicer = (slice(None, None, -1), slice(None))
    elif mode == "both":
        slicer = (slice(None, None, -1), slice(None, None, -1))
    else:
        raise ValueError("mode 必须是 'horizontal'、'vertical' 或 'both'")

    # 用 NumPy 切片手写翻转，不直接调用 Pillow 的封装
    if input_img.mode in ("L", "RGB", "RGBA"):
        pixels = np.array(input_img)[slicer]
        return Image.fromarray(pixels)

    # 调色板等少见模式回退到 Pillow
    pil_mode = {
        "horizontal": Image.FLIP_LEFT_RIGHT,
        "vertical": Image.FLIP_TOP_BOTTOM,
        "both": Image.ROTATE_180,
    }[mode]
    return input_img.transpose(pil_mode)


def apply_rotate_flip(
    input_img: np.ndarray,
    angle: float = 0.0,
    clockwise: bool = True,
    flip_horizontal: bool = False,
    flip_vertical: bool = False,
    expand: bool = True,
    fill_color: FillColor = None,
) -> np.ndarray:
    """主接口：先翻转，再旋转。
    
    传入:
    input_img: BGR uint8 ndarry
    angle: 旋转角度(度)
    clockwise: True->顺时针
    flip_horizontal: True->水平翻转
    flip_vertical: True->垂直翻转
    expand: True->开启自动扩大画布
    fill_color: 空白区域填充色(RGB)，默认黑色

返回:
    处理后的 BGR uint8 图像数组，
    宽高可能因旋转发生变化，不修改原图。
    """
    result = Image.fromarray(
    cv2.cvtColor(input_img, cv2.COLOR_BGR2RGB) #fix:输入BGR uint8 ndarry并转Pillow
)

    if flip_horizontal:
        result = flip_image(result, "horizontal")
    if flip_vertical:
        result = flip_image(result, "vertical")
    if angle:
        result = rotate_image(
            result,
            angle=angle,
            clockwise=clockwise,
            expand=expand,
            fill_color=fill_color,
        )

    # 没有任何操作时也返回副本，避免调用方误改原图
    # fix:Pillow image -> BGR uint8 ndarry
    return cv2.cvtColor(
        np.array(result),
        cv2.COLOR_RGB2BGR
    )