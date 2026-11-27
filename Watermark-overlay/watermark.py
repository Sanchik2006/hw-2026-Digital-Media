import random
import math
import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

# ==========================================
# 辅助函数：系统字体探测与随机文本生成
# ==========================================

def _get_system_font(
    font_size: int
) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """尝试加载系统中文字体，防止中文变方块"""

    font_paths = [
        # Windows
        "msyh.ttc",
        "msyhbd.ttc",
        "simhei.ttf",

        # macOS
        "/System/Library/Fonts/PingFang.ttc",
        "/System/Library/Fonts/STHeiti Medium.ttc",
        "/System/Library/Fonts/STHeiti Light.ttc",
        "/System/Library/Fonts/Supplemental/Songti.ttc",
        "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
        "/Library/Fonts/Arial Unicode.ttf",

        # Linux
        "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc",
        "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    ]

    for path in font_paths:
        try:
            return ImageFont.truetype(path, font_size)
        except OSError:
            continue

    print("警告：未找到系统中文字体，中文可能无法正常显示。")
    return ImageFont.load_default(size=font_size)

def _generate_random_text()->str:
    """无输入时，系统随机生成的包浆文本"""
    texts = [
        "包浆老图", "岁月痕迹", "转发过万", "原图已毁", "经典永流传", 
        "网络考古", "数字遗产", "建议放大看", "懂的都懂", "清晰度感人", 
        "摄于 1998", "请勿双击", "加载中...", "图已绿", "REAL MEME"
    ]
    return random.choice(texts)

# ==========================================
# 核心接口：供前端整合同学（张语瞳）调用
# ==========================================

#fix:原本支持传路径、PIL Image且支持保存图片,现统一为只接受和返回图像数组,将文件读取和保存逻辑提出交给调用方
def apply_watermark(
    input_image: np.ndarray,
    text: str | None = None,
    position: str = "center",
    opacity: float = 0.3,
    angle: float = 15.0,
    font_size: int = 50,
    is_tiled: bool = False,
) -> np.ndarray:
    """
    【任务3：水印叠加】核心处理函数
    
    参数:
        input_image : BGR uint8 图像数组(H W 3)
        text : 水印文本。若为None或空字则随机生成。
        position : 水印位置 (支持'left-top', 'right-top', 'left-bottom', 'right-bottom', 'center')。
        opacity : 不透明度 (0.0 完全透明 - 1.0 不透明)。默认 0.3。
        angle : 旋转角度 (顺时针)。默认 15。
        font_size : 字体大小。默认 50(像素)
        is_tiled (bool): 是否开启全屏平铺水印（满屏包浆效果）。默认 False。
        
    返回:
        处理后的BGR uint8 图像数组
    """

    # fix:添加参数合法性检查(直接抛异常)
    if not 0.0 <= opacity <= 1.0:
        raise ValueError("opacity必须在 0.0~1.0之间")
    if font_size <= 0:
        raise ValueError("font_size必须大于0")
    if not math.isfinite(angle):
        raise ValueError("angle必须为有限数值")

    valid_positions = (
        "left-top",
        "right-top",
        "left-bottom",
        "right-bottom",
        "center",
    )
    if position not in valid_positions:
        raise ValueError("无效的水印位置")
    # 完全透明时直接返回原图副本
    if opacity == 0:
        return input_image.copy()

    # 1. 处理输入图片
    base_image = Image.fromarray(
        cv2.cvtColor(input_image, cv2.COLOR_BGR2RGBA)
    )

    # 2. 处理文本
    if not text or str(text).strip() == "":
        text = _generate_random_text()

    # 3. 准备水印图层
    watermark = Image.new("RGBA", base_image.size, (0, 0, 0, 0))
    font = _get_system_font(font_size)
    
    # 计算文字尺寸
    #fix:已经更新为新版本Pillow,故删除了原本兼容旧版本pillow的try-expect逻辑
    draw_dummy = ImageDraw.Draw(watermark)
    left, top, right, bottom = draw_dummy.textbbox(
        (0, 0), text, font=font
    )
    text_w = max(1, right - left)
    text_h = max(1, bottom - top)

    # 在透明小图上绘制文字并旋转
    margin = int(max(text_w, text_h) * 0.5) # 留白防止旋转裁切
    text_img = Image.new("RGBA", (text_w + margin*2, text_h + margin*2), (0, 0, 0, 0))
    text_draw = ImageDraw.Draw(text_img)
    
    # 白色文字，带透明度
    text_color = (255, 255, 255, int(opacity * 255))
    # 为了增加质感，可以加一点极淡的黑色描边（可选）
    # text_draw.text((margin, margin), text, font=font, fill=text_color, stroke_width=1, stroke_fill=(0,0,0, int(opacity*100)))
    text_draw.text(
        (margin - left, margin - top),
        text,
        font=font,
        fill=text_color
    )



    text_img.save("debug_text.png")

    # 水印旋转方向和透明留白
    rotated_text = text_img.rotate(
        -angle,
        resample=Image.Resampling.BICUBIC,
        expand=True
    )
    # 裁掉旋转后的多余透明区域
    alpha_bbox = rotated_text.getchannel("A").getbbox()

    print("水印文本：", text)
    print("文字尺寸：", text_w, text_h)
    print("旋转后图层尺寸：", rotated_text.size)
    print("Alpha边界：", alpha_bbox)

    if alpha_bbox is None:
        print("警告：水印图层完全透明")
        return input_image.copy()

    if alpha_bbox is None:
        return input_image.copy()

    rotated_text = rotated_text.crop(alpha_bbox)
    rot_w, rot_h = rotated_text.size

    # 4. 定位与合成
    img_w, img_h = base_image.size
    padding = 20

    if is_tiled:
        # 平铺模式 (满屏包浆效果)
        for y in range(0, img_h + rot_h, rot_h + padding * 2):
            for x in range(0, img_w + rot_w, rot_w + padding * 2):
                watermark.paste(rotated_text, (x, y))
    else:
        # 单点模式
        if position == "left-top":
            pos = (padding, padding)
        elif position == "right-top":
            pos = (img_w - rot_w - padding, padding)
        elif position == "left-bottom":
            pos = (padding, img_h - rot_h - padding)
        elif position == "right-bottom":
            pos = (img_w - rot_w - padding, img_h - rot_h - padding)
        else: # center
            pos = ((img_w - rot_w) // 2, (img_h - rot_h) // 2)
            
        watermark.paste(rotated_text, pos)


        watermark.save("debug_watermark.png")

    # 5. 合并图层
    final_image = Image.alpha_composite(base_image, watermark).convert("RGB")

    # 6. 返回 BGR uint8 图像数组
    return cv2.cvtColor(
        np.array(final_image),
        cv2.COLOR_RGB2BGR
    )