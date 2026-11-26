import os
import cv2
import numpy as np
from PIL import Image


def _load_rgb(input_image):
    """加载图片并统一转为 RGB 模式

    :param input_image: 输入图片的本地路径 (str) 或 PIL Image 对象
    :return: RGB 模式的 PIL Image 对象
    """
    if isinstance(input_image, str):
        return Image.open(input_image).convert("RGB")
    if isinstance(input_image, Image.Image):
        return input_image.convert("RGB")
    raise TypeError("input_image 必须是文件路径 (str) 或 PIL Image 对象")


def refine_mask(
    mask,
    min_area=30,
    max_area_ratio=0.25,
    min_fill_ratio=0.10,
    max_aspect_ratio=20
):
    """按连通域过滤掩膜，去掉噪点与大片误检区域

    过滤规则（按顺序）：
    1. 面积小于 min_area 的连通域视为噪点，丢弃；
    2. 面积超过"图像总面积 * max_area_ratio"的连通域视为大片白色背景/天空，丢弃；
    3. 长宽比极端（超过 max_aspect_ratio）且填充率很低（area/(w*h) 小于 min_fill_ratio）
       的连通域视为零散细线噪声，丢弃；
    4. 其余连通域保留，重组成干净的 0/255 掩膜。

    :param mask: 输入掩膜，numpy 数组 (H, W)，非零即视为候选（uint8 / bool 均可）
    :param min_area: 连通域最小面积，默认 30
    :param max_area_ratio: 连通域面积占全图比例上限，默认 0.25
    :param min_fill_ratio: 填充率下限（仅在长宽比极端时生效），默认 0.10
    :param max_aspect_ratio: 长宽比上限，超过则视为"极端长条"，默认 20
    :return: 过滤后的 uint8 单通道掩膜（保留处 255，其余 0）
    """
    if mask is None:
        raise TypeError("mask 不能为 None")
    m = np.asarray(mask)
    if m.ndim != 2:
        raise ValueError("mask 必须是单通道二值图，形状为 (H, W)")

    binary = (m > 0).astype(np.uint8)
    clean = np.zeros(binary.shape, dtype=np.uint8)

    if not binary.any():
        return clean

    num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(
        binary, connectivity=8
    )
    total_area = float(binary.size)

    for i in range(1, num_labels):
        x, y, w, h, area = stats[i]
        if area < min_area:
            continue
        if area > total_area * max_area_ratio:
            continue
        if w <= 0 or h <= 0:
            continue

        fill_ratio = area / float(w * h)
        aspect_ratio = max(w, h) / float(min(w, h))
        if aspect_ratio > max_aspect_ratio and fill_ratio < min_fill_ratio:
            continue

        roi = labels[y:y + h, x:x + w]
        clean[y:y + h, x:x + w][roi == i] = 255

    return clean


def detect_white_watermark_mask(
    rgb,
    v_thresh=200,
    s_thresh=40,
    tophat_kernel_size=9,
    tophat_thresh=20,
    close_kernel_size=5,
    dilate_kernel_size=3,
    dilate_iter=2,
    refine=True,
    min_area=30,
    max_area_ratio=0.25,
    min_fill_ratio=0.10,
    max_aspect_ratio=20,
    debug=False
):
    """自动检测白色半透明文字水印，返回二值掩膜

    采用双通道融合策略：
    - 通道 A：HSV 空间"高亮度 + 低饱和度"的白色区域；
    - 通道 B：灰度顶帽变换提取的"比周围明显更亮的细长结构"，即文字笔画。
    两者按位或合并后，用闭运算连接笔画间隙；随后先经 refine_mask 做连通域过滤
    （在膨胀之前去噪点、去大片白底，避免膨胀把噪点放大后逃过过滤），
    最后再膨胀覆盖文字边缘的抗锯齿过渡带。

    :param rgb: RGB 顺序的图像，numpy 数组 (H, W, 3) 或 PIL Image 对象
    :param v_thresh: 通道 A 亮度阈值，V > v_thresh 视为白色候选，默认 200
    :param s_thresh: 通道 A 饱和度阈值，S < s_thresh 视为低饱和度，默认 40
    :param tophat_kernel_size: 通道 B 顶帽变换的结构元尺寸（自动取奇数），默认 9
    :param tophat_thresh: 通道 B 二值化阈值；传 None 时改用 Otsu 自动阈值，默认 20
    :param close_kernel_size: 形态学闭运算核尺寸（自动取奇数），默认 5
    :param dilate_kernel_size: 膨胀核尺寸（自动取奇数），默认 3
    :param dilate_iter: 膨胀迭代次数，默认 2
    :param refine: 是否对掩膜做连通域过滤，默认 True
    :param min_area: 连通域最小面积，默认 30
    :param max_area_ratio: 连通域面积占全图比例上限，默认 0.25
    :param min_fill_ratio: 填充率下限（长宽比极端时生效），默认 0.10
    :param max_aspect_ratio: 长宽比上限，默认 20
    :param debug: 为 True 时额外返回中间结果，便于肉眼排查
    :return: debug=False 返回 uint8 单通道掩膜（水印处 255，其余 0）；
             debug=True 返回 (mask, debug_info)，debug_info 含 'channel_a'、'channel_b'、
             'fused'、'mask_before_refine'、'mask'
    """
    if isinstance(rgb, Image.Image):
        rgb = np.array(rgb.convert("RGB"))
    if not isinstance(rgb, np.ndarray):
        raise TypeError("rgb 必须是 numpy 数组 (H, W, 3) 或 PIL Image 对象")
    if rgb.ndim != 3 or rgb.shape[2] < 3:
        raise ValueError("rgb 必须是三通道图像，形状为 (H, W, 3)")

    arr = np.ascontiguousarray(rgb[..., :3]).astype(np.uint8)

    # 通道 A：HSV 白色阈值（注意是 RGB -> HSV）
    hsv = cv2.cvtColor(arr, cv2.COLOR_RGB2HSV)
    _h, s, v = cv2.split(hsv)
    channel_a = ((v > v_thresh) & (s < s_thresh)).astype(np.uint8) * 255

    # 通道 B：灰度顶帽变换，抠出细长亮笔画
    gray = cv2.cvtColor(arr, cv2.COLOR_RGB2GRAY)
    k = max(3, int(tophat_kernel_size) | 1)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k))
    tophat = cv2.morphologyEx(gray, cv2.MORPH_TOPHAT, kernel)

    if tophat_thresh is None:
        _, channel_b = cv2.threshold(tophat, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    else:
        _, channel_b = cv2.threshold(tophat, float(tophat_thresh), 255, cv2.THRESH_BINARY)

    # 融合：先并集，再闭运算连接笔画间隙
    fused = cv2.bitwise_or(channel_a, channel_b)
    ck = max(3, int(close_kernel_size) | 1)
    fused = cv2.morphologyEx(fused, cv2.MORPH_CLOSE, np.ones((ck, ck), np.uint8))

    # 先连通域过滤（必须在膨胀之前：此时噪点仍是孤立小点、白底大片仍是单块，
    # 过滤最干净；若先膨胀，噪点会被放大成连通域，逃过 min_area 门槛）
    mask_before_refine = fused.copy()
    if refine:
        mask = refine_mask(
            fused,
            min_area=min_area,
            max_area_ratio=max_area_ratio,
            min_fill_ratio=min_fill_ratio,
            max_aspect_ratio=max_aspect_ratio,
        )
    else:
        mask = fused.copy()

    # 最后膨胀，覆盖文字边缘的抗锯齿过渡带
    dk = max(3, int(dilate_kernel_size) | 1)
    mask = cv2.dilate(mask, np.ones((dk, dk), np.uint8), iterations=max(0, int(dilate_iter)))

    if debug:
        debug_info = {
            "channel_a": channel_a,
            "channel_b": channel_b,
            "fused": fused,
            "mask_before_refine": mask_before_refine,
            "mask": mask,
        }
        return mask, debug_info

    return mask


def repair_by_mask(
    rgb,
    mask,
    method="inpaint",
    inpaint_radius=3,
    feather_sigma=3
):
    """按掩膜修复水印区域，返回修复后的 RGB 图像

    修复流程：
    1. 掩膜全 0 时直接返回原图（是否打印提示由上层调用方负责）；
    2. method="inpaint" 时调用 cv2.inpaint 用周围像素填补；
    3. 对掩膜做高斯模糊得到水印权重 w，再做羽化融合，避免 inpaint 硬边界。

    :param rgb: RGB 顺序的图像，numpy 数组 (H, W, 3)
    :param mask: 单通道掩膜，numpy 数组 (H, W)，水印处非零
    :param method: 修复方式，目前仅支持 "inpaint"，非法值回退到 inpaint
    :param inpaint_radius: cv2.inpaint 的修复半径，默认 3
    :param feather_sigma: 边缘羽化高斯核的 sigma，默认 3
    :return: 修复后的 RGB numpy 数组 (H, W, 3)，uint8
    """
    m = np.asarray(mask)
    if m.ndim == 3:
        m = m[..., 0]
    if m.ndim != 2:
        raise ValueError("mask 必须是单通道掩膜，形状为 (H, W)")

    if not (m > 0).any():
        # 掩膜为空：原样返回，打印提示交由上层调用方负责
        return np.asarray(rgb).copy()

    binary = (m > 0).astype(np.uint8) * 255

    if method != "inpaint":
        print(f"[WARN] 未知修复方式 {method}，回退到 inpaint")
        method = "inpaint"

    # 全程 RGB，不转 BGR；inpaint 的 mask 必须是 uint8 单通道
    inpainted = cv2.inpaint(
        rgb.astype(np.uint8), binary, int(inpaint_radius), cv2.INPAINT_TELEA
    )

    # 边缘羽化：把掩膜高斯模糊成水印权重 w（水印中心≈1、背景≈0、过渡带介于其间），
    # 用 w 混合原图与修复图，消除 inpaint 掩膜边缘的方块感。
    w = cv2.GaussianBlur(
        binary.astype(np.float32) / 255.0, (0, 0), sigmaX=float(feather_sigma)
    )
    w = w[..., None].astype(np.float32)

    src = rgb.astype(np.float32)
    fixed = inpainted.astype(np.float32)
    result = src * (1.0 - w) + fixed * w
    result = np.clip(result, 0, 255).astype(np.uint8)

    return result


def build_mask_from_regions(size, regions):
    """根据手动框选区域生成掩膜

    :param size: 图像尺寸 (width, height)，与 PIL Image.size 一致
    :param regions: 区域列表，元素为 (x1, y1, x2, y2)，可为 None 或空列表
    :return: uint8 单通道掩膜 (H, W)，区域内为 255，其余 0
    """
    width, height = size
    mask = np.zeros((height, width), dtype=np.uint8)

    for (x1, y1, x2, y2) in regions or []:
        x1, x2 = sorted((int(x1), int(x2)))
        y1, y2 = sorted((int(y1), int(y2)))
        x1 = max(0, min(x1, width))
        x2 = max(0, min(x2, width))
        y1 = max(0, min(y1, height))
        y2 = max(0, min(y2, height))
        if x2 > x1 and y2 > y1:
            mask[y1:y2, x1:x2] = 255

    return mask


def remove_watermark(
    input_image,
    regions=None,
    auto_detect=True,
    method="inpaint",
    output_path=None,
    **detect_kwargs
):
    """【任务4：去除水印】核心处理函数

    处理流程：
    1. 加载图片并统一为 RGB；
    2. 若有手动 regions，则据此生成掩膜；
    3. 若 auto_detect，则自动检测水印掩膜并与手动掩膜合并；
    4. 掩膜为空时打印提示并原样返回；
    5. 否则按掩膜修复（inpaint），可选保存并返回。

    :param input_image: 输入图片的本地路径 (str) 或 PIL Image 对象
    :param regions: 手动指定的水印区域列表，元素为 (x1, y1, x2, y2)，默认 None
    :param auto_detect: 是否自动检测水印，默认 True
    :param method: 修复方式，目前仅支持 "inpaint"，非法值回退到 inpaint
    :param output_path: 若提供，则将结果保存到该路径
    :param detect_kwargs: 透传给 detect_white_watermark_mask 的关键字参数
        （如 v_thresh / s_thresh / tophat_thresh / min_area / max_area_ratio 等）
    :return: 处理后的 PIL Image 对象 (RGB 模式)
    """
    img = _load_rgb(input_image)
    rgb = np.array(img)

    # 手动区域掩膜（兜底能力），再叠加自动检测结果
    mask = build_mask_from_regions(img.size, regions)
    if auto_detect:
        detected = detect_white_watermark_mask(rgb, **detect_kwargs)
        mask = cv2.bitwise_or(mask, detected)

    if not (mask > 0).any():
        print("[INFO] 未检测到水印区域，返回原图")
        result = img
    else:
        fixed_rgb = repair_by_mask(rgb, mask, method=method)
        result = Image.fromarray(fixed_rgb)

    if output_path:
        result.save(output_path, quality=95)

    return result


if __name__ == "__main__":
    import sys

    HERE = os.path.dirname(os.path.abspath(__file__))
    ROOT = os.path.dirname(HERE)

    INPUT_FILE = os.path.join(HERE, "test.jpg")
    WM_INPUT_FILE = os.path.join(HERE, "watermark_input.jpg")
    WM_REMOVED_FILE = os.path.join(HERE, "watermark_removed.jpg")
    COMPARE_FILE = os.path.join(HERE, "compare.jpg")

    # 跨目录导入水印叠加模块（失败时给出可读提示，不让脚本崩溃）
    try:
        sys.path.insert(0, os.path.join(ROOT, "Watermark-overlay"))
        from watermark import apply_watermark
    except Exception as exc:
        print(f"[ERROR] 无法导入水印叠加模块 Watermark-overlay/watermark.py：{exc}")
        print("请确认该模块存在，且已安装依赖：pip install pillow numpy opencv-python")
        sys.exit(1)

    # 读取原图
    try:
        original = _load_rgb(INPUT_FILE)
    except FileNotFoundError:
        print("找不到 test.jpg，请在 Watermark-remove 文件夹内放入图片")
        sys.exit(1)

    # 1. 叠加水印
    watermarked = apply_watermark(
        original,
        text="包浆老图",
        position="center",
        opacity=0.3,
        angle=15,
        font_size=50,
    )
    watermarked.save(WM_INPUT_FILE, quality=95)

    # 2. 去除水印
    removed = remove_watermark(WM_INPUT_FILE, output_path=WM_REMOVED_FILE)

    # 3. 三图横向拼接（高度对齐，中间加 10px 白边分隔）
    gap = 10
    height = max(original.height, watermarked.height, removed.height)
    gap_img = Image.new("RGB", (gap, height), (255, 255, 255))
    compare = Image.new(
        "RGB", (original.width * 3 + gap * 2, height), (255, 255, 255)
    )

    compare.paste(original, (0, 0))
    compare.paste(gap_img, (original.width, 0))
    compare.paste(watermarked, (original.width + gap, 0))
    compare.paste(gap_img, (original.width * 2 + gap, 0))
    compare.paste(removed, (original.width * 2 + gap * 2, 0))
    compare.save(COMPARE_FILE, quality=95)

    print("闭环对比演示完成：")
    print(f"  原图   : {INPUT_FILE}")
    print(f"  带水印 : {WM_INPUT_FILE}")
    print(f"  去水印 : {WM_REMOVED_FILE}")
    print(f"  对比图 : {COMPARE_FILE}")