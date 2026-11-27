import cv2
import numpy as np
# fix :移除了用于测试程序的os和用于读图存图和转换的Pillow库

# fix:移除_load_rgb,限制调用方传入算法模块格式仅为RGB

def refine_mask(
    mask: np.ndarray,
    min_area: int = 30,
    max_area_ratio: float = 0.25,
    min_fill_ratio: float = 0.10,
    max_aspect_ratio: float = 20,
) -> np.ndarray:
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
    bgr: np.ndarray,
    v_thresh: int = 200,
    s_thresh: int = 40,
    tophat_kernel_size: int = 9,
    tophat_thresh: float | None = 20,
    close_kernel_size: int = 5,
    dilate_kernel_size: int = 3,
    dilate_iter: int = 2,
    refine: bool = True,
    min_area: int = 30,
    max_area_ratio: float = 0.25,
    min_fill_ratio: float = 0.10,
    max_aspect_ratio: float = 20,
    debug: bool = False,
) -> np.ndarray | tuple[np.ndarray, dict[str, np.ndarray]]:
    """自动检测白色半透明文字水印，返回二值掩膜

    采用双通道融合策略：
    - 通道 A：HSV 空间"高亮度 + 低饱和度"的白色区域；
    - 通道 B：灰度顶帽变换提取的"比周围明显更亮的细长结构"，即文字笔画。
    两者按位或合并后，用闭运算连接笔画间隙；随后先经 refine_mask 做连通域过滤
    （在膨胀之前去噪点、去大片白底，避免膨胀把噪点放大后逃过过滤），
    最后再膨胀覆盖文字边缘的抗锯齿过渡带。

    :param rgb: BGR uint8 图像数组
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
    if not isinstance(bgr, np.ndarray):
        raise TypeError("bgr 必须是 numpy 数组")
    if bgr.ndim != 3 or bgr.shape[2] != 3:
        raise ValueError("bgr 必须是三通道图像 (H, W, 3)")
    if bgr.dtype != np.uint8:
        raise TypeError("bgr 的像素类型必须为 uint8")
    if bgr.size == 0:
        raise ValueError("输入图像不能为空")

    arr = np.ascontiguousarray(bgr)

    # 通道 A：HSV 白色阈值（注意是 RGB -> HSV）
    hsv = cv2.cvtColor(arr, cv2.COLOR_BGR2HSV)
    _h, s, v = cv2.split(hsv)
    channel_a = ((v > v_thresh) & (s < s_thresh)).astype(np.uint8) * 255

    # 通道 B：灰度顶帽变换，抠出细长亮笔画
    gray = cv2.cvtColor(arr, cv2.COLOR_BGR2GRAY)
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
    bgr: np.ndarray,
    mask: np.ndarray,
    method: str = "inpaint",
    inpaint_radius: float = 3,
    feather_sigma: float = 3,
) -> np.ndarray:
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

    #fix:将原本允许传入3通道自动拉取第一通道的逻辑修改为
    #统一要求单通道
    if method != "inpaint":
        raise ValueError("目前仅支持 inpaint 修复方式")
    if not np.isfinite(inpaint_radius) or inpaint_radius <= 0:
        raise ValueError("inpaint_radius 必须为有限正数")
    if not np.isfinite(feather_sigma) or feather_sigma < 0:
        raise ValueError("feather_sigma 必须为有限非负数")

    m = np.asarray(mask)

    if m.ndim != 2:
        raise ValueError("mask 必须是单通道掩膜 (H, W)")
    if m.shape != bgr.shape[:2]:
        raise ValueError("mask 尺寸必须与输入图像一致")
    if not (m > 0).any():
        return bgr.copy()

    binary = (m > 0).astype(np.uint8) * 255

    # 直接处理BGR；inpaint 的 mask 必须是 uint8 单通道
    inpainted = cv2.inpaint(
        bgr,
        binary,
        float(inpaint_radius),
        cv2.INPAINT_TELEA
    )

    # 边缘羽化：把掩膜高斯模糊成水印权重 w（水印中心≈1、背景≈0、过渡带介于其间），
    # 用 w 混合原图与修复图，消除 inpaint 掩膜边缘的方块感。
    w = cv2.GaussianBlur(
        binary.astype(np.float32) / 255.0, (0, 0), sigmaX=float(feather_sigma)
    )
    w = w[..., None].astype(np.float32)

    src = bgr.astype(np.float32)
    fixed = inpainted.astype(np.float32)
    result = src * (1.0 - w) + fixed * w
    result = np.clip(result, 0, 255).astype(np.uint8)

    return result


def build_mask_from_regions(
    size: tuple[int, int],
    regions: list[tuple[int, int, int, int]] | None,
) -> np.ndarray:
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
    input_image: np.ndarray,
    regions: list[tuple[int, int, int, int]] | None = None,
    auto_detect: bool = True,
    method: str = "inpaint",
    inpaint_radius: float = 3,
    feather_sigma: float = 3,
    **detect_kwargs,
) -> np.ndarray:
    """【任务4：去除水印】核心处理函数

    处理流程：
    1. 加载图片并统一为 RGB；
    2. 若有手动 regions，则据此生成掩膜；
    3. 若 auto_detect，则自动检测水印掩膜并与手动掩膜合并；
    4. 掩膜为空时打印提示并原样返回；
    5. 否则按掩膜修复（inpaint），可选保存并返回。

    :param input_image: BGR uint8 图像数组 (H, W, 3)
    :param regions: 手动指定的水印区域列表，元素为 (x1, y1, x2, y2)，默认 None
    :param auto_detect: 是否自动检测水印，默认 True
    :param method: 修复方式，目前仅支持 "inpaint"，非法值回退到 inpaint
    :param detect_kwargs: 透传给 detect_white_watermark_mask 的关键字参数
        （如 v_thresh / s_thresh / tophat_thresh / min_area / max_area_ratio 等）

    :return:处理后的 BGR uint8 图像数组，
    """
        # 1. 检查输入图像
    if not isinstance(input_image, np.ndarray):
        raise TypeError("input_image 必须是 numpy 数组")

    if input_image.ndim != 3 or input_image.shape[2] != 3:
        raise ValueError("输入图像必须为 (H, W, 3)")

    if input_image.dtype != np.uint8:
        raise TypeError("输入图像必须为 uint8 类型")

    if input_image.size == 0:
        raise ValueError("输入图像不能为空")

    bgr = np.ascontiguousarray(input_image)

    # 手动区域掩膜（兜底能力），再叠加自动检测结果
    h, w = bgr.shape[:2]
    mask = build_mask_from_regions((w,h), regions)
    if auto_detect:
        detected = detect_white_watermark_mask(bgr, **detect_kwargs)
        mask = cv2.bitwise_or(mask, detected)

    # 自动检测+合并掩膜
    if auto_detect:
        detected = detect_white_watermark_mask(
            bgr,
            **detect_kwargs
        )

    #若debug===True->检测函数返回元组
    if isinstance(detected, tuple):
        detected = detected[0]

    mask = cv2.bitwise_or(mask, detected)

    # 4. 根据掩膜修复图像
    return repair_by_mask(
        bgr,
        mask,
        method=method,
        inpaint_radius=inpaint_radius,
        feather_sigma=feather_sigma,
    )
