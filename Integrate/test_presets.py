# 测试预设模式(固定配方和年份预设)

from pathlib import Path

import cv2
import numpy as np

from .pipeline import apply_pipeline
from .presets import get_preset, get_year_preset

# 测试预设配方是否相互独立
def test_deepcopy():
    config1 = get_preset("medium")
    config2 = get_preset("medium")

    config1["noise_params"]["package_level"] = 0.9
    config1["watermark_params"][0]["text"] = "测试水印"

    assert config2["noise_params"]["package_level"] == 0.5
    assert config2["watermark_params"][0]["text"] == "包浆老图"

    config3 = get_preset("medium")

    assert config3 == config2

    print("深拷贝测试通过")


    # 测试年份映射及阶段变化
def test_year_preset():
    assert get_year_preset(0) == get_preset("original")

    config = get_year_preset(50)

    assert config["compress_params"]["age"] == 50
    assert config["noise_params"]["package_level"] == 1.0
    assert config["noise_params"]["green_level"] == 1.0
    assert config["rotate_params"]["angle"] == 5
    assert len(config["watermark_params"]) == 3

    # 测试水印层数变化的临界年份
    cases = {
        9: 0,
        10: 1,
        29: 1,
        30: 2,
        39: 2,
        40: 3,
    }

    for age, expected in cases.items():
        config = get_year_preset(age)
        layers = config["watermark_params"] or []

        assert len(layers) == expected

    # 测试旋转启用的临界年份
    assert get_year_preset(19)["rotate_params"] is None
    assert get_year_preset(20)["rotate_params"] is not None

    print("年份映射测试通过")

# 测试非法配方名称和年份
def test_invalid_params():
    try:
        get_preset("unknown")
    except ValueError:
        pass
    else:
        raise AssertionError("非法配方名称未被拦截")

    for age in [-1, 51]:
        try:
            get_year_preset(age)
        except ValueError:
            pass
        else:
            raise AssertionError(f"非法年份未被拦截：{age}")

    print("异常参数测试通过")


    # 执行配方并检查输出
def generate_image(img, config, output_path):
    original = img.copy()

    result = apply_pipeline(img, **config)

    # 检查输出接口
    assert isinstance(result, np.ndarray)
    assert result.dtype == np.uint8
    assert result.ndim == 3
    assert result.shape[2] == 3
    assert result.size > 0

    # 检查原图是否被修改
    assert np.array_equal(img, original)
    assert not np.shares_memory(img, result)

    # 保存测试结果
    if not cv2.imwrite(str(output_path), result):
        raise OSError(f"图片保存失败：{output_path}")

    print(f"生成成功：{output_path.name}，尺寸：{result.shape}")

    # 批量生成配方测试图片
def test_generate_images():
    here = Path(__file__).resolve().parent

    input_file = here / "test.jpg"
    output_dir = here / "test_outputs"

    img = cv2.imread(str(input_file))

    if img is None:
        raise FileNotFoundError("无法读取测试图片")

    # 创建测试输出目录
    output_dir.mkdir(exist_ok=True)

    # 测试原图配方
    result = apply_pipeline(img, **get_preset("original"))
    assert np.array_equal(img, result)

    # 固定预设测试
    for name in ["original", "light", "medium", "heavy", "ancient"]:
        config = get_preset(name)

        generate_image(
            img,
            config,
            output_dir / f"preset_{name}.png",
        )

    # 年份预设测试
    for age in [0, 10, 20, 30, 40, 50]:
        config = get_year_preset(age)

        generate_image(
            img,
            config,
            output_dir / f"year_{age:02d}.png",
        )

    print("全部配方图片生成完成")


def main():
    test_deepcopy()
    test_year_preset()
    test_invalid_params()
    test_generate_images()

    print("\n全部配方测试通过！")


if __name__ == "__main__":
    main()