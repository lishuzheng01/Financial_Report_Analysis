import warnings
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.report_data_reader import report_data_reader

warnings.filterwarnings("ignore")

# Fonts for CJK display
plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei", "Arial Unicode MS"]
plt.rcParams["axes.unicode_minus"] = False


def safe_divide(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
    num = pd.to_numeric(numerator, errors="coerce")
    den = pd.to_numeric(denominator, errors="coerce")
    result = num / den
    result = result.where((den != 0) & (~den.isna()))
    return result


def normalize_frame(df: pd.DataFrame) -> pd.DataFrame:
    frame = df.copy()
    frame["Report Date"] = pd.to_datetime(frame["Report Date"].astype(str), format="%Y%m%d", errors="coerce")
    for col in frame.columns:
        if col == "Report Date":
            continue
        frame[col] = pd.to_numeric(frame[col], errors="coerce")
    return frame.sort_values("Report Date").reset_index(drop=True)


def pick_series(df: pd.DataFrame, candidates: list[str], default: float = np.nan) -> pd.Series:
    for name in candidates:
        if name in df.columns:
            return pd.to_numeric(df[name], errors="coerce")
    return pd.Series([default] * len(df), index=df.index, dtype=float)


def rolling_average(series: pd.Series) -> pd.Series:
    previous = series.shift(1).fillna(series)
    return (series + previous) / 2


COLUMN_ALIASES = {
    "revenue": ["Operating Revenue", "Total Operating Revenue"],
    "net_profit": ["Net Profit", "Net Profit Attributable to Parent"],
    "total_assets": ["Total Assets"],
    "equity": [
        "Total Equity Attributable to Shareholders of the Parent Company",
        "Total Owner's Equity (or Shareholders' Equity)",
    ],
}


def prepare_dataset(symbol: str, number: int) -> pd.DataFrame:
    balance_df, profit_df, _ = report_data_reader(symbol, number)
    balance_df = normalize_frame(balance_df)
    profit_df = normalize_frame(profit_df)

    needed_cols = ["Report Date"]
    for cols in COLUMN_ALIASES.values():
        needed_cols.extend(cols)
    needed_cols = list(dict.fromkeys(needed_cols))

    merged = balance_df[balance_df.columns.intersection(needed_cols)]
    merged = merged.merge(profit_df[profit_df.columns.intersection(needed_cols)], on="Report Date", how="left")
    merged = merged.sort_values("Report Date").reset_index(drop=True)

    for key, aliases in COLUMN_ALIASES.items():
        merged[key] = pick_series(merged, aliases)

    merged["average_total_assets"] = rolling_average(merged["total_assets"])
    merged["average_equity"] = rolling_average(merged["equity"])

    merged["net_margin"] = safe_divide(merged["net_profit"], merged["revenue"])
    merged["asset_turnover"] = safe_divide(merged["revenue"], merged["average_total_assets"])
    merged["equity_multiplier"] = safe_divide(merged["average_total_assets"], merged["average_equity"])
    merged["roe"] = merged["net_margin"] * merged["asset_turnover"] * merged["equity_multiplier"]

    return merged


def detect_frequency_note(dates: pd.Series) -> str | None:
    if len(dates) < 2:
        return None
    diffs = dates.sort_values().diff().dropna()
    if diffs.empty:
        return None
    month_gaps = diffs.dt.days.apply(lambda d: round(d / 30))
    if month_gaps.nunique() > 1:
        return "注意：报告期频率不一致（可能混合年报/季报），请谨慎比较。"
    return None


def format_value(value: float, as_percent: bool = False) -> str:
    if pd.isna(value) or np.isinf(value):
        return ""
    if as_percent:
        return f"{value * 100:.2f}%"
    return f"{value:.2f}"


def build_table(df: pd.DataFrame) -> str:
    headers = ["Report Date", "净利率", "总资产周转率", "权益乘数", "ROE"]
    lines = ["| " + " | ".join(headers) + " |", "|" + "|".join(["---"] * len(headers)) + "|"]
    for _, row in df.iterrows():
        lines.append(
            "| "
            + " | ".join(
                [
                    row["Report Date"].strftime("%Y-%m-%d"),
                    format_value(row["net_margin"], True),
                    format_value(row["asset_turnover"]),
                    format_value(row["equity_multiplier"]),
                    format_value(row["roe"], True),
                ]
            )
            + " |"
        )
    return "\n".join(lines)


def plot_dupont(df: pd.DataFrame, symbol: str, output_dir: Path) -> str:
    fig, ax1 = plt.subplots(figsize=(10, 6))

    ax1.plot(df["Report Date"], df["net_margin"] * 100, marker="o", label="净利率(%)")
    ax1.plot(df["Report Date"], df["roe"] * 100, marker="o", label="ROE(%)", linewidth=2.5)
    ax1.set_ylabel("百分比(%)")

    ax2 = ax1.twinx()
    ax2.plot(df["Report Date"], df["asset_turnover"], marker="s", color="#F18F01", label="总资产周转率")
    ax2.plot(df["Report Date"], df["equity_multiplier"], marker="^", color="#06A77D", label="权益乘数")
    ax2.set_ylabel("倍数/周转率")

    ax1.set_title(f"{symbol} 杜邦分析趋势", fontsize=14, fontweight="bold")
    ax1.set_xlabel("报告期")
    ax1.grid(alpha=0.3)
    ax1.tick_params(axis="x", rotation=45)

    # Combine legends from both axes
    lines, labels = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines + lines2, labels + labels2, loc="upper left")

    plt.tight_layout()
    filename = f"{symbol}_dupont_trend.png"
    output_dir.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_dir / filename, dpi=300, bbox_inches="tight")
    plt.close()
    return filename


def generate_markdown(symbol: str, df: pd.DataFrame, image_file: str, output_dir: Path, freq_note: str | None) -> Path:
    lines: list[str] = []
    lines.append("prompt：请在适当的位置插入图片，严格遵守markdown图片的插入规范，图片内容如下：")
    lines.append(f"图片1：{image_file}")
    lines.append("")
    lines.append(f"# {symbol} 杜邦分析报告")
    lines.append("")
    if freq_note:
        lines.append(f"> {freq_note}")
        lines.append("")
    lines.append("## 杜邦三分解指标")
    lines.append(build_table(df))
    lines.append("")
    # lines.append("## 趋势图")
    # lines.append(f"![杜邦分析]({image_file})")
    lines.append("")

    report_path = output_dir / f"{symbol}_dupont_analysis.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return report_path


def dupont_analysis(symbol: str, number: int = 4) -> str:
    df = prepare_dataset(symbol, number)
    freq_note = detect_frequency_note(df["Report Date"])

    output_dir = Path(f"stock_report_data/report_data/{symbol}/dupont_analysis")
    image_file = plot_dupont(df, symbol, output_dir)
    report_path = generate_markdown(symbol, df, image_file, output_dir, freq_note)

    print(f"杜邦分析报告已生成: {report_path}")
    return str(output_dir)


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 2:
        stock_code = sys.argv[1]
        periods = int(sys.argv[2])
    elif len(sys.argv) > 1:
        stock_code = sys.argv[1]
        periods = 4
    else:
        stock_code = input("请输入股票代码: ").strip()
        periods_input = input("请输入分析期数（默认4）: ").strip()
        periods = int(periods_input) if periods_input else 4

    dupont_analysis(stock_code, periods)
