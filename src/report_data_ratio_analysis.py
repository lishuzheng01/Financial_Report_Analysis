import warnings
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.report_data_reader import report_data_reader

warnings.filterwarnings("ignore")

# Use common CJK-capable fonts for charts
plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei", "Arial Unicode MS"]
plt.rcParams["axes.unicode_minus"] = False


def safe_divide(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
    """Divide with zero/NaN protection."""
    num = pd.to_numeric(numerator, errors="coerce")
    den = pd.to_numeric(denominator, errors="coerce")
    result = num / den
    result = result.where((den != 0) & (~den.isna()))
    return result


def normalize_frame(df: pd.DataFrame) -> pd.DataFrame:
    """Ensure datetime index and numeric columns."""
    frame = df.copy()
    frame["Report Date"] = pd.to_datetime(frame["Report Date"].astype(str), format="%Y%m%d", errors="coerce")
    for col in frame.columns:
        if col == "Report Date":
            continue
        frame[col] = pd.to_numeric(frame[col], errors="coerce")
    return frame.sort_values("Report Date").reset_index(drop=True)


def trim_columns(df: pd.DataFrame, desired: list[str]) -> pd.DataFrame:
    keep = ["Report Date"]
    keep.extend([col for col in desired if col in df.columns and col != "Report Date"])
    return df[keep]


def pick_series(df: pd.DataFrame, candidates: list[str], default: float = np.nan) -> pd.Series:
    for name in candidates:
        if name in df.columns:
            return pd.to_numeric(df[name], errors="coerce")
    return pd.Series([default] * len(df), index=df.index, dtype=float)


def rolling_average(series: pd.Series) -> pd.Series:
    """Average of current and previous period, fallback to current when lacking history."""
    previous = series.shift(1).fillna(series)
    return (series + previous) / 2


COLUMN_ALIASES = {
    "current_assets": ["Total Current Assets", "Current Assets"],
    "current_liabilities": ["Total Current Liabilities", "Current Liabilities"],
    "total_assets": ["Total Assets"],
    "total_liabilities": ["Total Liabilities"],
    "accounts_receivable": ["Accounts Receivable", "Notes and Accounts Receivable"],
    "inventories": ["Inventories"],
    "equity": [
        "Total Equity Attributable to Shareholders of the Parent Company",
        "Total Owner's Equity (or Shareholders' Equity)",
    ],
    "revenue": ["Operating Revenue", "Total Operating Revenue"],
    "operating_costs": ["Operating Costs", "Total Operating Costs"],
    "net_profit": ["Net Profit", "Net Profit Attributable to Parent"],
    "income_tax": ["Income Tax Expenses"],
    "financial_expenses": ["Financial Expenses"],
    "interest_expenses": ["Interest Expenses"],
    "operating_cash_flow": ["Net Cash Flow from Operating Activities"],
    "capex": ["Cash Paid for Acquisition of Fixed Assets, Intangible Assets, and Other Long-term Assets"],
}


CATEGORY_DEFINITIONS = [
    {
        "name": "偿债能力",
        "slug": "solvency",
        "metrics": [
            {"name": "流动比率", "format": "ratio", "func": lambda df: safe_divide(df["current_assets"], df["current_liabilities"])},
            {"name": "速动比率", "format": "ratio", "func": lambda df: safe_divide(df["current_assets"] - df["inventories"], df["current_liabilities"])},
            {"name": "资产负债率", "format": "percent", "func": lambda df: safe_divide(df["total_liabilities"], df["total_assets"])},
            {"name": "利息保障倍数", "format": "ratio", "func": lambda df: safe_divide(df["EBIT"], df["interest_expenses"])},
        ],
    },
    {
        "name": "盈利能力",
        "slug": "profitability",
        "metrics": [
            {"name": "毛利率", "format": "percent", "func": lambda df: safe_divide(df["revenue"] - df["operating_costs"], df["revenue"])},
            {"name": "净利率", "format": "percent", "func": lambda df: safe_divide(df["net_profit"], df["revenue"])},
            {"name": "ROA", "format": "percent", "func": lambda df: safe_divide(df["net_profit"], df["average_total_assets"])},
            {"name": "ROE", "format": "percent", "func": lambda df: safe_divide(df["net_profit"], df["average_equity"])},
        ],
    },
    {
        "name": "运营效率",
        "slug": "efficiency",
        "metrics": [
            {"name": "应收账款周转率", "format": "ratio", "func": lambda df: safe_divide(df["revenue"], df["average_accounts_receivable"])},
            {"name": "存货周转率", "format": "ratio", "func": lambda df: safe_divide(df["operating_costs"], df["average_inventory"])},
            {"name": "总资产周转率", "format": "ratio", "func": lambda df: safe_divide(df["revenue"], df["average_total_assets"])},
        ],
    },
    {
        "name": "成长能力",
        "slug": "growth",
        "metrics": [
            {"name": "营收同比", "format": "percent", "func": lambda df: df["revenue"].pct_change()},
            {"name": "净利润同比", "format": "percent", "func": lambda df: df["net_profit"].pct_change()},
            {"name": "资产增长率", "format": "percent", "func": lambda df: df["total_assets"].pct_change()},
        ],
    },
    {
        "name": "现金流质量",
        "slug": "cash_flow",
        "metrics": [
            {"name": "经营现金流/净利润比", "format": "ratio", "func": lambda df: safe_divide(df["operating_cash_flow"], df["net_profit"])},
            {"name": "自由现金流", "format": "number", "func": lambda df: df["operating_cash_flow"] - df["capex"]},
        ],
    },
]


def prepare_dataset(symbol: str, number: int) -> pd.DataFrame:
    balance_df, profit_df, cash_flow_df = report_data_reader(symbol, number)

    balance_df = normalize_frame(balance_df)
    profit_df = normalize_frame(profit_df)
    cash_flow_df = normalize_frame(cash_flow_df)

    needed_cols = ["Report Date"]
    for col_list in COLUMN_ALIASES.values():
        needed_cols.extend(col_list)
    needed_cols = list(dict.fromkeys(needed_cols))

    merged = trim_columns(balance_df, needed_cols)
    merged = merged.merge(trim_columns(profit_df, needed_cols), on="Report Date", how="left")
    merged = merged.merge(trim_columns(cash_flow_df, needed_cols), on="Report Date", how="left")
    merged = merged.sort_values("Report Date").reset_index(drop=True)

    for key, aliases in COLUMN_ALIASES.items():
        merged[key] = pick_series(merged, aliases)

    merged["average_total_assets"] = rolling_average(merged["total_assets"])
    merged["average_equity"] = rolling_average(merged["equity"])
    merged["average_accounts_receivable"] = rolling_average(merged["accounts_receivable"])
    merged["average_inventory"] = rolling_average(merged["inventories"])

    merged["EBIT"] = merged["net_profit"].fillna(0) + merged["income_tax"].fillna(0) + merged["financial_expenses"].fillna(0)

    return merged


def calculate_category_results(prepared_df: pd.DataFrame) -> dict[str, pd.DataFrame]:
    results: dict[str, pd.DataFrame] = {}
    for category in CATEGORY_DEFINITIONS:
        df = pd.DataFrame({"Report Date": prepared_df["Report Date"]})
        for metric in category["metrics"]:
            df[metric["name"]] = metric["func"](prepared_df)
        results[category["name"]] = df
    return results


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


def format_value(value: float, fmt: str) -> str:
    if pd.isna(value) or np.isinf(value):
        return ""
    if fmt == "percent":
        return f"{value * 100:.2f}%"
    if fmt == "number":
        return f"{value:,.2f}"
    return f"{value:.2f}"


def build_ratio_table(prepared_df: pd.DataFrame, category_results: dict[str, pd.DataFrame]) -> str:
    headers = ["Report Date"]
    for category in CATEGORY_DEFINITIONS:
        for metric in category["metrics"]:
            headers.append(f"{category['name']}-{metric['name']}")

    lines = ["| " + " | ".join(headers) + " |", "|" + "|".join(["---"] * len(headers)) + "|"]

    for idx in prepared_df.index:
        row = [prepared_df.loc[idx, "Report Date"].strftime("%Y-%m-%d")]
        for category in CATEGORY_DEFINITIONS:
            metrics_df = category_results[category["name"]]
            for metric in category["metrics"]:
                value = metrics_df.loc[idx, metric["name"]]
                row.append(format_value(value, metric["format"]))
        lines.append("| " + " | ".join(row) + " |")

    return "\n".join(lines)


def plot_category_trends(symbol: str, output_dir: Path, category_results: dict[str, pd.DataFrame]) -> list[str]:
    image_files: list[str] = []
    for category in CATEGORY_DEFINITIONS:
        df = category_results[category["name"]]
        fig, ax = plt.subplots(figsize=(10, 6))

        for metric in category["metrics"]:
            series = df[metric["name"]]
            values_for_plot = series * 100 if metric["format"] == "percent" else series
            ax.plot(df["Report Date"], values_for_plot, marker="o", linewidth=2, label=metric["name"])

        ax.set_title(f"{category['name']}趋势", fontsize=14, fontweight="bold")
        ax.set_xlabel("报告期")
        ylabel = "数值（%指将值转换为百分比）" if any(m["format"] == "percent" for m in category["metrics"]) else "数值"
        ax.set_ylabel(ylabel)
        ax.grid(alpha=0.3)
        ax.legend()
        plt.xticks(rotation=45)
        plt.tight_layout()

        filename = f"{symbol}_{category['slug']}_trend.png"
        plt.savefig(output_dir / filename, dpi=300, bbox_inches="tight")
        plt.close()
        image_files.append(filename)

    return image_files


def generate_markdown_report(
    symbol: str,
    prepared_df: pd.DataFrame,
    category_results: dict[str, pd.DataFrame],
    image_files: list[str],
    output_dir: Path,
    freq_note: str | None = None,
) -> Path:
    report_lines: list[str] = []

    report_lines.append("prompt：请在适当的位置插入图片，严格遵守markdown图片的插入规范，图片内容如下：")
    for idx, img in enumerate(image_files, 1):
        report_lines.append(f"图片{idx}：{img}")
    report_lines.append("")

    report_lines.append(f"# {symbol} 比率分析报告")
    report_lines.append("")
    if freq_note:
        report_lines.append(f"> {freq_note}")
        report_lines.append("")

    report_lines.append("## 比率指标计算")
    report_lines.append(build_ratio_table(prepared_df, category_results))
    report_lines.append("")

    # for category, img in zip(CATEGORY_DEFINITIONS, image_files):
    #     report_lines.append(f"## {category['name']}趋势")
    #     report_lines.append(f"![{category['name']}]({img})")
    #     report_lines.append("")

    output_dir.mkdir(parents=True, exist_ok=True)
    report_path = output_dir / f"{symbol}_ratio_analysis.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(report_lines))

    return report_path


def report_data_ratio_analysis(symbol: str, number: int = 4) -> str:
    """生成财务比率分析报告。"""
    prepared_df = prepare_dataset(symbol, number)
    category_results = calculate_category_results(prepared_df)
    freq_note = detect_frequency_note(prepared_df["Report Date"])

    output_dir = Path(f"stock_report_data/report_data/{symbol}/ratio_analysis")
    output_dir.mkdir(parents=True, exist_ok=True)

    image_files = plot_category_trends(symbol, output_dir, category_results)
    report_path = generate_markdown_report(symbol, prepared_df, category_results, image_files, output_dir, freq_note)

    print(f"比率分析报告已生成: {report_path}")
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

    report_data_ratio_analysis(stock_code, periods)
