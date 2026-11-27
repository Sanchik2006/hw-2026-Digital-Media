#types.py存固定参数配方的数据类型

from typing import TypedDict

class PipelineConfig(TypedDict):
    remove_params: dict | None
    rotate_params: dict | None
    noise_params: dict | None
    watermark_params: list[dict] | None
    compress_params: dict | None