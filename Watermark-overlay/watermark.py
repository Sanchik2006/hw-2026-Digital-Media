import os
import random
import io
from PIL import Image, ImageDraw, ImageFont

# ==========================================
# 辅助函数：系统字体探测与随机文本生成
# ==========================================

def _get_system_font(font_size):
    """尝试加载系统中文字体，防止中文变方块"""
    # 常见中文字体路径列表（Windows / macOS / Linux）
    font_paths = [
        "msyh.ttc", "msyhbd.ttc", "simhei.ttf",  # Windows
        "/System/Library/Fonts/PingFang.ttc",    # macOS
        "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc" # Linux
    ]
    for path in font_paths:
        try:
            return ImageFont.truetype(path, font_size)
        except IOError:
            continue
    print("警告: 未找到系统中文字体，使用默认字体，中文可能显示为方块。")
    return ImageFont.load_default()

def _generate_random_text():
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

def apply_watermark(
    input_image, 
    text=None, 
    position="center", 
    opacity=0.3, 
    angle=15, 
    font_size=50,
    is_tiled=False,
    output_path=None
):
    """
    【任务3：水印叠加】核心处理函数
    
    参数:
        input_image (str or Image.Image): 输入图片的本地路径，或 PIL Image 对象。
        text (str): 用户输入的水印文本。若为 None 或空字符串，则系统随机生成。
        position (str): 位置 ('left-top', 'right-top', 'left-bottom', 'right-bottom', 'center')。
        opacity (float): 透明度 (0.0 完全透明 - 1.0 不透明)。默认 0.3。
        angle (int): 旋转角度 (顺时针)。默认 15。
        font_size (int): 字体大小。默认 50。
        is_tiled (bool): 是否开启全屏平铺水印（满屏包浆效果）。默认 False。
        output_path (str): 如果提供，会将图片保存到该路径。
        
    返回:
        PIL.Image.Image: 处理后的图片对象 (RGB模式)，供前端直接展示或保存。
    """
    # 1. 处理输入图片
    if isinstance(input_image, str):
        base_image = Image.open(input_image).convert("RGBA")
    elif isinstance(input_image, Image.Image):
        base_image = input_image.convert("RGBA")
    else:
        raise TypeError("input_image 必须是文件路径 (str) 或 PIL Image 对象")

    # 2. 处理文本
    if not text or str(text).strip() == "":
        text = _generate_random_text()

    # 3. 准备水印图层
    watermark = Image.new("RGBA", base_image.size, (0, 0, 0, 0))
    font = _get_system_font(font_size)
    
    # 计算文字尺寸
    draw_dummy = ImageDraw.Draw(watermark)
    try:
        bbox = draw_dummy.textbbox((0, 0), text, font=font)
        text_w, text_h = bbox[2] - bbox[0], bbox[3] - bbox[1]
    except AttributeError:
        text_w, text_h = draw_dummy.textsize(text, font=font)

    # 在透明小图上绘制文字并旋转
    margin = int(max(text_w, text_h) * 0.5) # 留白防止旋转裁切
    text_img = Image.new("RGBA", (text_w + margin*2, text_h + margin*2), (0, 0, 0, 0))
    text_draw = ImageDraw.Draw(text_img)
    
    # 白色文字，带透明度
    text_color = (255, 255, 255, int(opacity * 255))
    # 为了增加质感，可以加一点极淡的黑色描边（可选）
    # text_draw.text((margin, margin), text, font=font, fill=text_color, stroke_width=1, stroke_fill=(0,0,0, int(opacity*100)))
    text_draw.text((margin, margin), text, font=font, fill=text_color)
    
    rotated_text = text_img.rotate(angle, expand=True)
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

    # 5. 合并图层
    final_image = Image.alpha_composite(base_image, watermark).convert("RGB")

    # 6. 保存或返回
    if output_path:
        final_image.save(output_path, quality=95)
        
    return final_image