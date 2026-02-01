"""Fetch and persist commonly used macroeconomic datasets via akshare.

Optimizations:
- Centralized mapping of dataset names to callables for easier maintenance.
- Basic error handling keeps the script running even if a single endpoint fails.
- Uses ``__main__`` guard to avoid side effects when the module is imported.
"""

import os
from concurrent.futures import ThreadPoolExecutor, TimeoutError
from typing import Callable, Dict

import akshare as ak


SAVE_PATH = "macroeconomic_data"
# Use env var to tweak per-dataset timeout without editing code.
FETCH_TIMEOUT_SECONDS = int(os.getenv("MACRO_FETCH_TIMEOUT", "60"))
os.makedirs(SAVE_PATH, exist_ok=True)


def save_to_csv(df, filename: str) -> None:
    """Persist a DataFrame to UTF-8 CSV inside ``SAVE_PATH``."""

    filepath = os.path.join(SAVE_PATH, f"{filename}.csv")
    df.to_csv(filepath, index=False, encoding="utf-8-sig")


def macroeconomic_data_get() -> Dict[str, Callable[[], object]]:
    """Return a mapping of dataset names to the akshare fetch callables."""

    return {
        "macroeconomic_china_gdp_yearly": ak.macro_china_gdp_yearly,
        "macro_china_cpi_yearly": ak.macro_china_cpi_yearly,
        "macro_china_cpi_monthly": ak.macro_china_cpi_monthly,
        "macro_china_ppi_yearly": ak.macro_china_ppi_yearly,
        # 财新制造业 PMI 终值 (年度)
        "macro_china_cx_manufacturing_pmi": ak.macro_china_cx_pmi_yearly,
        "macro_china_exports_yoy": ak.macro_china_exports_yoy,
        "macro_china_shrzgm": ak.macro_china_shrzgm,
    }


def macroeconomic_data_get_all() -> None:
    """Fetch each macro dataset and save it to CSV; continue on errors.

    Each fetch is wrapped with a timeout so the batch can't hang on a slow endpoint.
    """

    with ThreadPoolExecutor(max_workers=1) as executor:
        for name, fetcher in macroeconomic_data_get().items():
            future = executor.submit(fetcher)
            try:
                df = future.result(timeout=FETCH_TIMEOUT_SECONDS)
                save_to_csv(df, name)
                print(f"Saved {name} ({len(df)} rows)")
            except TimeoutError:
                future.cancel()
                print(f"Skipped {name}: fetch exceeded {FETCH_TIMEOUT_SECONDS}s timeout")
            except Exception as exc:  # noqa: BLE001 - best-effort batch job
                print(f"Failed to fetch {name}: {exc}")


if __name__ == "__main__":
    macroeconomic_data_get_all()
