# Noise-color-shift

模块功能：高斯噪点 + 绿色色调偏移，包浆强度可手动调节。

## 依赖

- pillow
- numpy

```bash
pip install pillow numpy
```

## 对外接口

```python
from Noise-color-shift.processor import apply_patina_effect
```

```python
def apply_patina_effect(input_img, package_level, green_level=0.5)
```

### 参数说明

- `input_img`: PIL Image RGB 对象，和其他模块对接。
- `package_level`: float，0~1（推荐值），整体包浆强度，控制轻度模糊和噪点。
- `green_level`: float，0~1（推荐值），绿色偏色强度。

### 返回值

- 处理完成后的 PIL Image 对象。

## 规则说明

参数负数会自动置 0 并打印警告；大于推荐上限只警告，不截断。
