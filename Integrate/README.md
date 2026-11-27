# Integrate 图像处理全逻辑

整合项目中的五个独立图像处理算法，提供统一处理入口

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
from integrate import apply_pipeline
```

| 参数 | 类型 | 说明 |
|---|---|---|
| input_image | np.ndarray | 输入图像 |
| remove_params | dict或None | 去水印参数 |
| rotate_params | dict或None | 旋转翻转参数 |
| noise_params | dict或None | 噪点色偏参数 |
| watermark_params | list[dict]或None | 多层水印配置 |
| compress_params | dict或None | 压缩参数 |

参数为None时跳过该模块。

## 调用示例

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

cv2.imwrite("output.jpg", result)
```

## 运行测试

将测试图片 test.jpg 放入 /integrate。

在项目根目录执行：

```bash
python -m integrate.main
```

输出图片位于 integrate/output.jpg。

## 已知局限

- 当前采用固定算法执行顺序。
- 图像压缩与旋转可能改变输出尺寸。
- 水印自动检测效果取决于图片内容。
- 暂未支持预设配方和独立压缩参数。
- 暂未接入网站及 HTTP API。