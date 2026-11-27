#presets.py存预设配方和年份参数映射

from copy import deepcopy
from .types import PipelineConfig

#预设配方
PRESETS: dict[str, PipelineConfig] = {
    # 原图
    "original": {
        "remove_params": None,
        "rotate_params": None,
        "noise_params": None,
        "watermark_params": None,
        "compress_params": None,
    },

    # 轻度包浆
    "light": {
        "remove_params": None,
        "rotate_params": None,
        "noise_params": {
            "package_level": 0.2,
            "green_level": 0.1,
        },
        "watermark_params": None,
        "compress_params": {
            "age": 5,
        },
    },

    # 中度包浆
    "medium": {
        "remove_params": None,
        "rotate_params": None,
        "noise_params": {
            "package_level": 0.5,
            "green_level": 0.3,
        },
        "watermark_params": [
            {
                "text": "包浆老图",
                "opacity": 0.3,
                "font_size": 50,
                "position": "right-bottom",
            },
        ],
        "compress_params": {
            "age": 15,
        },
    },

    # 重度包浆
    "heavy": {
        "remove_params": None,
        "rotate_params": {
            "angle": 2,
        },
        "noise_params": {
            "package_level": 0.8,
            "green_level": 0.7,
        },
        "watermark_params": [
            {
                "text": "包浆老图",
                "opacity": 0.4,
                "font_size": 50,
            },
            {
                "text": "转发过万",
                "opacity": 0.3,
                "font_size": 30,
                "position": "right-bottom",
            },
        ],
        "compress_params": {
            "age": 30,
        },
    },

    # 远古包浆
    "ancient": {
        "remove_params": None,
        "rotate_params": {
            "angle": 5,
        },
        "noise_params": {
            "package_level": 1.0,
            "green_level": 1.0,
        },
        "watermark_params": [
            {
                "text": "远古老图",
                "opacity": 0.5,
                "font_size": 60,
            },
            {
                "text": "网络考古",
                "opacity": 0.2,
                "font_size": 30,
                "is_tiled": True,
            },
            {
                "text": "转发过万",
                "opacity": 0.4,
                "font_size": 40,
                "position": "right-bottom",
            },
        ],
        "compress_params": {
            "age": 50,
        },
    },
}

# 获取预设配方
def get_preset(name: str) -> PipelineConfig:
    if name not in PRESETS:
        raise ValueError(f"未知的预设配方：{name}")
    return deepcopy(PRESETS[name])
#调用方式
#config = get_preset("medium")
#result = apply_pipeline(img, **config)

# 根据年份生成整套配方(压缩逻辑中存在根据年份生成压缩参数,但不冲突)
def get_year_preset(age: int) -> PipelineConfig:
    if not 0 <= age <= 50:
        raise ValueError("流传年份必须在0~50之间")

    # 0年表示保留原图
    if age == 0:
        return get_preset("original")

    # 将年份归一化至0~1
    t = age / 50

    config = get_preset("original")

    # 图像压缩
    config["compress_params"] = {
        "age": age,
    }

    # 噪点与色偏
    config["noise_params"] = {
        "package_level": round(t, 2),
        "green_level": round(t, 2),
    }

    # 旋转
    if age >= 20:
        config["rotate_params"] = {
            "angle": round(t * 5, 2),
        }

    # 水印
    if age >= 10:
        config["watermark_params"] = [
            {
                "text": "包浆老图",
                "opacity": round(0.1 + t * 0.4, 2),
                "font_size": 50,
            },
        ]

    if age >= 30:
        config["watermark_params"].append({
            "text": "网络考古",
            "opacity": 0.2,
            "font_size": 30,
            "is_tiled": True,
        })

    if age >= 40:
        config["watermark_params"].append({
            "text": "转发过万",
            "opacity": 0.3,
            "font_size": 40,
            "position": "right-bottom",
        })

    return config