# 水印叠加模块 (Watermark-overlay)

负责人：夏郡晗
依赖库：`pip install Pillow`

## 接口说明

python
from watermark import apply_watermark

# 你的图片路径
img_path = "input.jpg"

# 调用函数 (最简单用法：居中，半透明，旋转15度，随机文字)
result_img = apply_watermark(img_path)

# 保存结果
result_img.save("output.jpg")