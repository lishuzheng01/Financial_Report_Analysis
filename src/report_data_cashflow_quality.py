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


COLUMN_ALIASES = {
    "ocf": ["Net Cash Flow from Operating Activities"],
    "net_profit": ["Net Profit", "Net Profit Attributable to Parent"],
    "capex": ["Cash Paid for Acquisition of Fixed Assets, Intangible Assets, and Other Long-term Assets"],
    "depreciation": [
        # 折旧/摊销字段表头未提供，留作扩展。缺失时按 0 处理。
    ],
}


def prepare_dataset(symbol: str, number: int) -> tuple[pd.DataFrame, bool]:
    _, profit_df, cash_flow_df = report_data_reader(symbol, number)

    profit_df = normalize_frame(profit_df)
    cash_flow_df = normalize_frame(cash_flow_df)

    needed_cols = ["Report Date"]
    for cols in COLUMN_ALIASES.values():
        needed_cols.extend(cols)
    needed_cols = list(dict.fromkeys(needed_cols))

    merged = profit_df[profit_df.columns.intersection(needed_cols)]
    merged = merged.merge(cash_flow_df[cash_flow_df.columns.intersection(needed_cols)], on="Report Date", how="left")
    merged = merged.sort_values("Report Date").reset_index(drop=True)

    for key, aliases in COLUMN_ALIASES.items():
        merged[key] = pick_series(merged, aliases, default=0 if key in {"capex", "depreciation"} else np.nan)

    dep_all_zero = merged["depreciation"].fillna(0).abs().sum() == 0

    merged["ocf_net_profit_ratio"] = safe_divide(merged["ocf"], merged["net_profit"])
    merged["cash_reinvest_ratio"] = safe_divide(merged["capex"] - merged["depreciation"], merged["ocf"])
    merged["fcf"] = merged["ocf"] - merged["capex"]

    return merged, dep_all_zero


def stability_summary(df: pd.DataFrame) -> dict:
    summary = {}
    metrics = {
        "OCF/净利润比": df["ocf_net_profit_ratio"],
        "现金再投资比率": df["cash_reinvest_ratio"],
        "自由现金流": df["fcf"],
    }
    for name, series in metrics.items():
        mean = series.mean()
        std = series.std(ddof=0)
        cv = std / mean if (pd.notna(mean) and mean != 0) else np.nan
        summary[name] = {"mean": mean, "std": std, "cv": cv}
    return summary


def format_value(value: float, kind: str) -> str:
    if pd.isna(value) or np.isinf(value):
        return ""
    if kind == "percent":
        return f"{value * 100:.2f}%"
    if kind == "number":
        return f"{value:,.2f}"
    return f"{value:.2f}"


def build_indicator_table(df: pd.DataFrame) -> str:
    headers = ["Report Date", "OCF/净利润比", "现金再投资比率", "自由现金流"]
    lines = ["| " + " | ".join(headers) + " |", "|" + "|".join(["---"] * len(headers)) + "|"]
    for _, row in df.iterrows():
        lines.append(
            "| "
            + " | ".join(
                [
                    row["Report Date"].strftime("%Y-%m-%d"),
                    format_value(row["ocf_net_profit_ratio"], "percent"),
                    format_value(row["cash_reinvest_ratio"], "percent"),
                    format_value(row["fcf"], "number"),
                ]
            )
            + " |"
        )
    return "\n".join(lines)


def build_stability_table(summary: dict) -> str:
    headers = ["指标", "均值", "标准差", "变异系数"]
    lines = ["| " + " | ".join(headers) + " |", "|" + "|".join(["---"] * len(headers)) + "|"]
    for name, stats in summary.items():
        lines.append(
            "| "
            + " | ".join(
                [
                    name,
                    format_value(stats["mean"], "percent" if "比" in name else "number") if name != "自由现金流" else format_value(stats["mean"], "number"),
                    format_value(stats["std"], "percent" if "比" in name else "number") if name != "自由现金流" else format_value(stats["std"], "number"),
                    format_value(stats["cv"], "percent"),
                ]
            )
            + " |"
        )
    return "\n".join(lines)


def plot_trends(df: pd.DataFrame, symbol: str, output_dir: Path) -> str:
    fig, ax1 = plt.subplots(figsize=(10, 6))

    ax1.plot(df["Report Date"], df["ocf_net_profit_ratio"] * 100, marker="o", label="OCF/净利润比(%)")
    ax1.plot(df["Report Date"], df["cash_reinvest_ratio"] * 100, marker="s", label="现金再投资比率(%)")
    ax1.set_ylabel("百分比(%)")

    ax2 = ax1.twinx()
    ax2.plot(df["Report Date"], df["fcf"], marker="^", color="#06A77D", label="自由现金流")
    ax2.set_ylabel("自由现金流")

    ax1.set_title(f"{symbol} 现金流质量趋势", fontsize=14, fontweight="bold")
    ax1.set_xlabel("报告期")
    ax1.grid(alpha=0.3)
    ax1.tick_params(axis="x", rotation=45)

    lines, labels = ax1.get_legend_handles_labels()
    lines2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(lines + lines2, labels + labels2, loc="upper left")

    plt.tight_layout()
    filename = f"{symbol}_cashflow_quality_trend.png"
    output_dir.mkdir(parents=True, exist_ok=True)
    plt.savefig(output_dir / filename, dpi=300, bbox_inches="tight")
    plt.close()
    return filename


def generate_markdown(symbol: str, df: pd.DataFrame, image_file: str, summary: dict, freq_note: str | None, dep_zero: bool, output_dir: Path) -> Path:
    lines: list[str] = []
    lines.append("prompt：请在适当的位置插入图片，严格遵守markdown图片的插入规范，图片内容如下：")
    lines.append(f"图片1：{image_file}")
    lines.append("")
    lines.append(f"# {symbol} 现金流质量分析报告")
    lines.append("")
    if freq_note:
        lines.append(f"> {freq_note}")
        lines.append("")
    if dep_zero:
        lines.append("> 折旧/摊销未在表头中提供，现金再投资比率按折旧摊销为 0 处理，请在有数据时更新。")
        lines.append("")
    lines.append("## 现金流质量指标")
    lines.append(build_indicator_table(df))
    lines.append("")
    lines.append("## 稳定性摘要（均值/标准差/变异系数）")
    lines.append(build_stability_table(summary))
    lines.append("")
    # lines.append("## 趋势图")
    # lines.append(f"![现金流质量趋势]({image_file})")
    lines.append("")

    report_path = output_dir / f"{symbol}_cashflow_quality.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return report_path


def cashflow_quality_analysis(symbol: str, number: int = 4) -> str:
    df, dep_zero = prepare_dataset(symbol, number)
    freq_note = detect_frequency_note(df["Report Date"])

    output_dir = Path(f"stock_report_data/report_data/{symbol}/cashflow_quality")
    image_file = plot_trends(df, symbol, output_dir)
    summary = stability_summary(df)
    report_path = generate_markdown(symbol, df, image_file, summary, freq_note, dep_zero, output_dir)

    print(f"现金流质量分析报告已生成: {report_path}")
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

    cashflow_quality_analysis(stock_code, periods)
