# Watermark-remove

模块功能：自动检测白色半透明文字水印，并用 inpaint 修复，去除水印。

## 依赖

- pillow
- numpy
- opencv-python

```bash
pip install pillow numpy opencv-python
```

## 对外接口

```python
from watermark_remove import remove_watermark
```

```python
def remove_watermark(
    input_image,
    regions=None,
    auto_detect=True,
    method="inpaint",
    output_path=None,
    **detect_kwargs
)
```

### 参数说明

| 参数 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `input_image` | str 或 PIL.Image | 必填 | 输入图片的本地路径，或 PIL Image 对象 |
| `regions` | list[tuple] | None | 手动框选的水印区域，元素为 `(x1, y1, x2, y2)` |
| `auto_detect` | bool | True | 是否自动检测水印掩膜 |
| `method` | str | "inpaint" | 修复方式，目前仅支持 "inpaint" |
| `output_path` | str | None | 若提供，结果保存到该路径 |
| `**detect_kwargs` | - | - | 透传给 `detect_white_watermark_mask` 的调参参数 |

`detect_kwargs` 常用参数：

| 参数 | 默认值 | 说明 |
| --- | --- | --- |
| `v_thresh` | 200 | 通道 A 亮度阈值（V > 该值视为白色候选） |
| `s_thresh` | 40 | 通道 A 饱和度阈值（S < 该值视为低饱和） |
| `tophat_kernel_size` | 9 | 通道 B 顶帽变换结构元尺寸 |
| `tophat_thresh` | 20 | 通道 B 二值化阈值，传 None 用 Otsu |
| `min_area` | 30 | 连通域最小面积（过滤噪点） |
| `max_area_ratio` | 0.25 | 连通域面积占全图比例上限（过滤大片白底） |

### 返回值

- 处理完成后的 PIL Image 对象（RGB 模式）。

## 最短示例

```python
from watermark_remove import remove_watermark

result = remove_watermark("test.jpg", output_path="output.jpg")
```

## 进阶示例（手动框选）

```python
from watermark_remove import remove_watermark

# 关闭自动检测，只修复手动指定的矩形区域
result = remove_watermark(
    "test.jpg",
    regions=[(100, 80, 300, 200)],
    auto_detect=False,
    output_path="manual_output.jpg",
)
```

## 调参示例

```python
# 自动检测时微调阈值，避免把背景也算进去
result = remove_watermark(
    "test.jpg",
    v_thresh=225,
    s_thresh=25,
    tophat_thresh=30,
    max_area_ratio=0.15,
    output_path="output.jpg",
)
```

## 常见问题与调参

- **掩膜太大，把背景也算进去了**：把 `v_thresh` 提到 225、`s_thresh` 降到 25，`tophat_thresh` 改成固定 30，同时 `max_area_ratio` 降到 0.15。
- **文字笔画漏检、掩膜断成碎块**：`tophat_kernel_size` 从 9 提到 13、`close_kernel_size` 从 5 提到 9、`dilate_iter` 从 2 提到 3。
- **修完有明显糊块**：`inpaint_radius` 从 3 降到 2，并增大 `feather_sigma` 加强羽化（这两个是底层 `repair_by_mask` 的参数，暂未暴露到 `remove_watermark` 顶层接口，需直接调用 `repair_by_mask` 调整）。
- **白底图完全失效**：属算法固有局限，需增加"局部对比度"判据（先用大核均值模糊得到局部背景亮度，仅当像素比局部背景亮 15 以上才算候选）。

## 已知局限

- 白底图：白色文字在白色背景上对比度过低，自动检测可能失效。
- 密集文字：大量笔画粘连成大片区域时，掩膜可能过粗。
- 强纹理背景：纹理高亮区域易被误判为水印。

## 闭环演示

运行脚本会生成「原图｜带水印｜去水印」三图对比，需在同目录放入 `test.jpg`：

```bash
python watermark_remove.py
```