# Integrate 图像处理全逻辑

整合项目中的五个独立图像处理算法，提供统一处理入口
提供自定义程度、固定程度预设和年份预设三种生成方式,所有配方均关闭自动去水印功能

## 图像接口规范

- 输入输出类型：numpy.ndarray
- 颜色通道顺序：BGR
- 像素类型：uint8
- 图像形状：(H, W, 3)

## 处理顺序(均可独立启用)

1. 去水印
2. 旋转+翻转
3. 噪点+色偏
4. 叠加新水印
5. 压缩图像


## 对外接口

```python
from integrate import (
    apply_pipeline,
    get_preset,
    get_year_preset,
    PipelineConfig,
)
```

| 接口 | 说明 |
|---|---|
| apply_pipeline() | 图像处理流水线 |
| get_preset() | 获取预设配方 |
| get_year_preset() | 获取指定流传年份配方 |
| PipelineConfig | 统一配方数据类型 |

### apply_pipeline()

| 参数 | 类型 | 说明 |
|---|---|---|
| input_image | np.ndarray | 输入图像 |
| remove_params | dict或None | 去水印参数 |
| rotate_params | dict或None | 旋转翻转参数 |
| noise_params | dict或None | 噪点色偏参数 |
| watermark_params | list[dict]或None | 多层水印配置 |
| compress_params | dict或None | 压缩参数 |

参数为None时跳过该模块。
水印叠加模块可传入多个参数字典，按顺序逐层叠加水印。

## 包浆配方系统

### 1.自定义模式

独立启用各图像处理模块，并手动设置对应算法参数

```python
import cv2
from integrate import apply_pipeline

img = cv2.imread("test.jpg")
result = apply_pipeline(
    img,
    noise_params={
        "package_level": 0.5,
        "green_level": 0.3,
    },
    watermark_params=[
        {
            "text": "包浆老图",
            "opacity": 0.3,
        },
    ],
    compress_params={
        "age": 10,
    },
)
cv2.imwrite("output.png", result)
```

调用示例:

```python
import cv2
from integrate import apply_pipeline, get_preset

img = cv2.imread("test.jpg")

config = get_preset("medium")
result = apply_pipeline(img, **config)

cv2.imwrite("output.png", result)
```

### 2.年份预设

get_year_preset(age)获取对应流传年份的配方(支持0～50)
噪点、色偏、压缩程度随年份变化

调用示例:

```python
import cv2
from integrate import apply_pipeline, get_year_preset

img = cv2.imread("test.jpg")

config = get_year_preset(25)
result = apply_pipeline(img, **config)

cv2.imwrite("output.png", result)
```

### 3.固定程度预设

```python
config = get_preset("medium")

# 修改噪点及色偏参数
config["noise_params"] = {
    "package_level": 0.7,
    "green_level": 0.5,
}

# 关闭压缩模块
config["compress_params"] = None

result = apply_pipeline(img, **config)
```

## 运行测试

将测试图片test.jpg放入integrate/目录
输出图片位于integrate/output.jpg

### 集成测试

在项目根目录执行：
`python -m integrate.main`

### 配方系统测试

在项目根目录执行：
`python -m integrate.test_presets`