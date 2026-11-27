# Watermark-remove

模块功能：自动检测白色半透明文字水印，并用 inpaint 修复，去除水印。

## 依赖

- numpy
- opencv-python
闭环测试还依赖Watermark-overlay模块及Pillow

在本文件夹中安装依赖:
pip install -r ../requirements.txt

## 对外接口

```python
from watermark_remove import remove_watermark
```

```python
def remove_watermark(
    input_image: np.ndarray,
    regions: list[tuple[int, int, int, int]] | None = None,
    auto_detect: bool = True,
    method: str = "inpaint",
    inpaint_radius: float = 3,
    feather_sigma: float = 3,
    **detect_kwargs,
) -> np.ndarray:
```

### 参数说明

| 参数 | 类型 | 默认值 | 说明 |
| --- | --- | --- | --- |
| `input_image` | np.ndarry | 必填 | BGR uint8 图像数组 (H, W, 3) |
| `regions` | list[tuple] | None | 手动框选的水印区域，元素为 `(x1, y1, x2, y2)` |
| `auto_detect` | bool | True | 是否自动检测水印掩膜 |
| `inpaint_radius` | float | 3 | 图像修复半径，必须>0 |
| `feather_sigma` | float | 3 | 羽化强度，0表示关闭 |
| `method` | str | "inpaint" | 修复方式，目前仅支持 "inpaint" |
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

- 返回新的 BGR uint8 图像数组

## 最短示例

```python
import cv2
from watermark_remove import remove_watermark

img = cv2.imread("watermark_input.jpg")
if img is None:
    raise FileNotFoundError("watermark_input.jpg")
result = remove_watermark(img)
cv2.imwrite("output.jpg", result)
```

## 进阶示例（手动框选）

```python
result = remove_watermark(
    img,
    regions=[(100, 80, 300, 200)],
    auto_detect=False,
)
```

## 调参示例

```python
result = remove_watermark(
    img,
    v_thresh=180,
    s_thresh=80,
    tophat_thresh=10,
    min_area=10,
    inpaint_radius=3,
    feather_sigma=1,
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

在同目录放入 `test.jpg`：
运行 `python main.py`

```bash
python watermark_remove.py
```