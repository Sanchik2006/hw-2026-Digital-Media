from PIL import Image, ImageFilter
import numpy as np


def add_noise(img_array: np.ndarray, noise_strength: float) -> np.ndarray:
    """添加高斯噪点"""
    if noise_strength <= 0:
        return img_array.copy()

    sigma = noise_strength * 65
    noise = np.random.normal(loc=0, scale=sigma, size=img_array.shape)
    noisy = img_array.astype(np.float32) + noise
    noisy = np.clip(noisy, 0, 255)
    return noisy.astype(np.uint8)


def color_shift_green(img_array: np.ndarray, green_strength: float) -> np.ndarray:
    """绿色偏色，强度可调"""
    if green_strength <= 0:
        return img_array.copy()

    arr = img_array.astype(np.float32)
    r, g, b = arr[..., 0], arr[..., 1], arr[..., 2]

    r = r * (1 - 0.30 * green_strength)
    g = g * (1 + 0.18 * green_strength)
    b = b * (1 - 0.28 * green_strength)

    new_arr = np.stack([r, g, b], axis=-1)
    new_arr = np.clip(new_arr, 0, 255)
    return new_arr.astype(np.uint8)


def apply_patina_effect(
    input_img: Image.Image,
    package_level: float,
    green_level: float = 0.5
) -> Image.Image:
    """
    加噪及绿调主接口
    :param input_img: PIL Image RGB对象（输入，和其他模块对接）
    :param package_level: float 0~1（推荐值），整体包浆强度，控制轻度模糊和噪点
    :param green_level: float 0~1（推荐值），绿色偏色强度
    :return: 处理完成后的PIL Image对象
    """
    if package_level < 0:
        print(f"[WARN] package_level {package_level} 为负数，自动置0")
        package_level = 0.0
    if green_level < 0:
        print(f"[WARN] green_level {green_level} 为负数，自动置0")
        green_level = 0.0
    
    img_rgb = input_img.convert("RGB")

    if package_level > 0:
        radius = 0.35 + package_level * 1.15
        img_rgb = img_rgb.filter(ImageFilter.GaussianBlur(radius=radius))

    img_arr = np.array(img_rgb)
    img_with_noise = add_noise(img_arr, package_level)
    img_final = color_shift_green(img_with_noise, green_level)

    return Image.fromarray(img_final)
