# Rotate-flip 图片旋转与翻转

按建议书要求实现：顺/逆时针 15° 旋转、水平/垂直翻转，基于仿射变换矩阵。

## 依赖

- pillow
- numpy
- opencv-python

安装：

    pip install pillow numpy

## 对外接口

```python
from rotate_flip import apply_rotate_flip

result = apply_rotate_flip(
    input_img,
    angle=15,
    clockwise=True,
    flip_horizontal=False,
    flip_vertical=False,
    expand=True,
    fill_color=None,
)
```

参数：

- `input_img`：BGR uint8 (H,W,3)
- `angle`：旋转角度（度），取绝对值。
- `clockwise`：True 顺时针，False 逆时针。
- `flip_horizontal`：左右镜像（绕竖直对称轴）。
- `flip_vertical`：上下镜像（绕水平对称轴）。
- `expand`：True 自动扩大画布，避免四角被裁；False 保持原尺寸。
- `fill_color`：旋转后空白区域颜色；默认黑色

返回：新的 PIL Image（不修改原图）。处理顺序：先翻转，再旋转。

底层也可以单独调用：

- `rotate_image(img, angle=15, clockwise=True, expand=True, fill_color=None)`
- `flip_image(img, mode="horizontal" | "vertical" | "both")`

底层函数说明:rotate_image()和flip_image()内部仍旧使用PIL Image

## 如何测试

1. 把一张图片放到本文件夹，命名为 `test.jpg`。
2. 在本文件夹运行：

       python main.py

3. 查看生成的 `output.jpg`。

## 整合说明

仓库文件夹名带连字符，不能直接 `from Rotate-flip...` 导入。整合时：

```python
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "Rotate-flip"))
from rotate_flip import apply_rotate_flip
```

为避免与 `Noise-color-shift/processor.py` 重名，本模块文件名使用 `rotate_flip.py`。
