"""兼容入口：拉取并保存全部宏观经济数据。

本文件仅作为命令行执行入口，核心逻辑在 `macroeconomic_data_get_all.py`。
"""

from src.macroeconomic_data_get_all import fetch_all


if __name__ == "__main__":
    fetch_all(save=True)
