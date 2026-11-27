# 水印叠加模块 (Watermark-overlay)

支持自定义文字水印、随机文字水印、指定位置、透明度调整、角度旋转、全屏平铺水印
负责人：夏郡晗
依赖 :
 - Pillow
 - numpy
 - opencv-python

安装项目依赖：
 - pip install -r ../requirements.txt

## 接口说明

python
from watermark import apply_watermark

result = apply_watermark(
    img,
    txet="包浆老图"
    position="center"
    opacity=0.3,
    angle=15,
    font_size=50,
    is_tiled=False,
)
cv2.imwrite("output.jpg", result)

## 参数说明
- `img`：BGR uint8 (H,W,3) 
- `text`(str或None) 水印文本。若为None或空字则随机生成。
- `cposition`(str) 水印位置
                支持'left-top'
                'right-top'
                'left-bottom'
                'right-bottom'
                'center'
- `opacity`(float) 不透明度 (0.0 完全透明 - 1.0 不透明)。默认 0.3
- `angle`(float) 旋转角度 (顺时针)。默认 15.0
- `font_size`(int) 字体大小。默认 50(像素)
- `is_tiled`(bool) 是否开启全屏平铺水印（满屏包浆效果）。默认 False。

返回：新的 BGR uint8 图像数组（不修改原图）

# 如何测试
将测试图片放入本文件夹，命名为 test.jpg。
在本文件夹运行：
    python main.py
查看生成的 output.jpg。