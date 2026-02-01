import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, List, Optional

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from src.report_data_reader import report_data_reader

warnings.filterwarnings("ignore")

# Fonts for CJK display in charts
plt.rcParams["font.sans-serif"] = ["SimHei", "Microsoft YaHei", "Arial Unicode MS"]
plt.rcParams["axes.unicode_minus"] = False


def safe_divide(numerator: pd.Series, denominator: pd.Series) -> pd.Series:
    """Divide with zero/NaN protection."""
    num = pd.to_numeric(numerator, errors="coerce")
    den = pd.to_numeric(denominator, errors="coerce")
    result = num / den
    return result.where((den != 0) & (~den.isna()))


def normalize_frame(df: pd.DataFrame) -> pd.DataFrame:
    """Ensure datetime and numeric columns, sorted by report date."""
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


def detect_frequency_note(dates: pd.Series) -> Optional[str]:
    if len(dates) < 2:
        return None
    diffs = dates.sort_values().diff().dropna()
    if diffs.empty:
        return None
    month_gaps = diffs.dt.days.apply(lambda d: round(d / 30))
    if month_gaps.nunique() > 1:
        return "注意：报告期频率不一致（可能混合年报/季报），请谨慎比较。"
    return None


def rolling_average(series: pd.Series) -> pd.Series:
    """Average of current and previous period, fallback to current when lacking history."""
    previous = series.shift(1).fillna(series)
    return (series + previous) / 2


COLUMN_ALIASES = {
    # 利润表
    "revenue": ["Operating Revenue", "Total Operating Revenue"],
    "operating_costs": ["Operating Costs", "Total Operating Costs"],
    "net_profit": ["Net Profit", "Net Profit Attributable to Parent"],
    "selling_expenses": ["Selling Expenses"],
    "admin_expenses": ["Administrative Expenses"],
    "financial_expenses": ["Financial Expenses"],
    "rnd_expenses": ["R&D Expenses"],
    # 资产负债表
    "cash": ["Cash and Cash Equivalents"],
    "trading_fin": ["Trading Financial Assets"],
    "accounts_receivable": ["Notes and Accounts Receivable", "Accounts Receivable"],
    "inventories": ["Inventories"],
    "total_assets": ["Total Assets"],
    "fixed_assets": ["Fixed Assets"],
    "construction_in_progress": ["Construction in Progress"],
    "investment_property": ["Investment Property"],
    "current_assets": ["Total Current Assets", "Current Assets"],
    "current_liabilities": ["Total Current Liabilities", "Current Liabilities"],
    "short_term_borrowings": ["Short-term Borrowings"],
    "ncl_due_1y": ["Non-current Liabilities Due within One Year"],
    "total_liabilities": ["Total Liabilities"],
    # 现金流量表
    "ocf": ["Net Cash Flow from Operating Activities"],
    "capex_cash": ["Cash Paid for Acquisition of Fixed Assets, Intangible Assets, and Other Long-term Assets"],
}


@dataclass
class Anomaly:
    rule: str
    date: pd.Timestamp
    metric: str
    detail: str
    severity: int  # 1-3


def prepare_dataset(symbol: str, number: int) -> pd.DataFrame:
    balance_df, profit_df, cash_flow_df = report_data_reader(symbol, number)

    balance_df = normalize_frame(balance_df)
    profit_df = normalize_frame(profit_df)
    cash_flow_df = normalize_frame(cash_flow_df)

    needed_cols = ["Report Date"]
    for cols in COLUMN_ALIASES.values():
        needed_cols.extend(cols)
    needed_cols = list(dict.fromkeys(needed_cols))

    merged = trim_columns(balance_df, needed_cols)
    merged = merged.merge(trim_columns(profit_df, needed_cols), on="Report Date", how="left")
    merged = merged.merge(trim_columns(cash_flow_df, needed_cols), on="Report Date", how="left")
    merged = merged.sort_values("Report Date").reset_index(drop=True)

    for key, aliases in COLUMN_ALIASES.items():
        merged[key] = pick_series(merged, aliases, default=0.0 if key in {"capex_cash"} else np.nan)

    merged["gross_margin"] = safe_divide(merged["revenue"] - merged["operating_costs"], merged["revenue"])
    merged["cost_rate"] = safe_divide(merged["operating_costs"], merged["revenue"])
    merged["expense_rate"] = safe_divide(
        merged["selling_expenses"].fillna(0)
        + merged["admin_expenses"].fillna(0)
        + merged["financial_expenses"].fillna(0),
        merged["revenue"],
    )
    merged["rnd_rate"] = safe_divide(merged["rnd_expenses"], merged["revenue"])
    merged["ocf_profit_ratio"] = safe_divide(merged["ocf"], merged["net_profit"])

    merged["avg_ar"] = rolling_average(merged["accounts_receivable"])
    merged["avg_inventory"] = rolling_average(merged["inventories"])
    merged["ar_turnover"] = safe_divide(merged["revenue"], merged["avg_ar"])
    merged["inventory_turnover"] = safe_divide(merged["operating_costs"], merged["avg_inventory"])
    merged["ar_days"] = safe_divide(365, merged["ar_turnover"])
    merged["inventory_days"] = safe_divide(365, merged["inventory_turnover"])

    merged["long_term_assets"] = (
        merged["fixed_assets"].fillna(0)
        + merged["construction_in_progress"].fillna(0)
        + merged["investment_property"].fillna(0)
    )
    merged["short_term_debt"] = merged["short_term_borrowings"].fillna(0) + merged["ncl_due_1y"].fillna(0)
    merged["flow_gap"] = merged["cash"].fillna(0) + merged["trading_fin"].fillna(0) - merged["short_term_debt"]
    merged["current_ratio"] = safe_divide(merged["current_assets"], merged["current_liabilities"])
    merged["short_debt_ratio"] = safe_divide(merged["short_term_debt"], merged["total_liabilities"])
    merged["long_asset_ratio"] = safe_divide(merged["long_term_assets"], merged["total_assets"])

    merged["capex_cash_pos"] = merged["capex_cash"].clip(lower=0)
    merged["long_asset_delta"] = merged["long_term_assets"].diff().clip(lower=0)
    merged["capex_rate"] = safe_divide(
        merged["long_asset_delta"].fillna(0) + merged["capex_cash_pos"], merged["revenue"]
    )

    return merged


def rule_continuous_volatility(df: pd.DataFrame) -> List[Anomaly]:
    anomalies: List[Anomaly] = []
    metrics = {
        "营业收入": ("revenue", 0.30),
        "净利润": ("net_profit", 0.30),
        "经营现金流": ("ocf", 0.30),
    }
    for name, (field, threshold) in metrics.items():
        growth = df[field].pct_change()
        for idx in range(2, len(df)):
            prev_g = growth.iloc[idx - 1]
            curr_g = growth.iloc[idx]
            if pd.isna(prev_g) or pd.isna(curr_g):
                continue
            # 同向高速
            if abs(curr_g) > threshold and abs(prev_g) > threshold and np.sign(curr_g) == np.sign(prev_g):
                detail = f"{name}连续两期高增速：上一期{prev_g:.1%}，本期{curr_g:.1%}"
                anomalies.append(Anomaly("连续波动异常-同向高速", df["Report Date"].iloc[idx], name, detail, 2))
            # 反转剧震
            amplitude = abs(curr_g - prev_g)
            if curr_g < -0.20 and prev_g > 0.20 and amplitude > 0.40:
                detail = f"{name}增速剧烈反转：上一期{prev_g:.1%}，本期{curr_g:.1%}，幅度{amplitude:.1%}"
                anomalies.append(Anomaly("连续波动异常-反转", df["Report Date"].iloc[idx], name, detail, 3))
    return anomalies


def rule_cost_expense(df: pd.DataFrame, window: int = 4) -> List[Anomaly]:
    anomalies: List[Anomaly] = []
    ratios = {
        "成本率": df["cost_rate"],
        "三费率": df["expense_rate"],
        "研发费用率": df["rnd_rate"],
    }
    for name, series in ratios.items():
        recent = series.dropna().tail(window)
        if recent.empty:
            continue
        current = recent.iloc[-1]
        median = recent.median()
        iqr = recent.quantile(0.75) - recent.quantile(0.25)
        deviation = current - median
        if abs(deviation) > 0.15 or (iqr > 0 and (current < median - 1.5 * iqr or current > median + 1.5 * iqr)):
            severity = 2 if abs(deviation) < 0.25 else 3
            detail = f"{name}现值{current:.2%}，中位数{median:.2%}，偏离{deviation:.2%}"
            anomalies.append(Anomaly("成本/费用率反常", df["Report Date"].iloc[-1], name, detail, severity))
    return anomalies


def rule_asset_liability_mismatch(df: pd.DataFrame) -> List[Anomaly]:
    anomalies: List[Anomaly] = []
    latest = df.iloc[-1]
    cond1 = (latest["current_ratio"] < 1) and (latest["flow_gap"] < 0)
    if cond1:
        detail = f"流动比率{latest['current_ratio']:.2f}且流动缺口{latest['flow_gap']:.0f}<0"
        anomalies.append(Anomaly("资产负债错配-流动缺口", latest["Report Date"], "流动性", detail, 3))
    cond2 = (latest["short_debt_ratio"] > 0.7) and (latest["long_asset_ratio"] > 0.5)
    if cond2:
        detail = f"短债占比{latest['short_debt_ratio']:.1%}，长期资产占比{latest['long_asset_ratio']:.1%}，存在短贷长投风险"
        anomalies.append(Anomaly("资产负债错配-短贷长投", latest["Report Date"], "期限错配", detail, 3))
    return anomalies


def rule_cash_profit_gap(df: pd.DataFrame) -> List[Anomaly]:
    anomalies: List[Anomaly] = []
    ratio = df["ocf_profit_ratio"]
    ocf = df["ocf"]
    net = df["net_profit"]
    if len(df) >= 2:
        last_two_ratio = ratio.tail(2)
        if (last_two_ratio < 0.8).all():
            detail = f"近两期经营现金流/净利润均低于0.8：{last_two_ratio.iloc[-2]:.2f}, {last_two_ratio.iloc[-1]:.2f}"
            anomalies.append(Anomaly("现金流与利润背离", df["Report Date"].iloc[-1], "现金流/净利润", detail, 2))
        last_two_sign = (ocf.tail(2) < 0) & (net.tail(2) > 0)
        if last_two_sign.all():
            detail = "近两期净利润为正但经营现金流为负，可能存在利润质量问题"
            anomalies.append(Anomaly("现金流与利润背离", df["Report Date"].iloc[-1], "利润质量", detail, 3))
    return anomalies


def rule_ar_inventory(df: pd.DataFrame, window: int = 4) -> List[Anomaly]:
    anomalies: List[Anomaly] = []
    if len(df) < 2:
        return anomalies
    # 周转天数变化
    ar_days_diff = df["ar_days"].iloc[-1] - df["ar_days"].iloc[-2]
    inv_days_diff = df["inventory_days"].iloc[-1] - df["inventory_days"].iloc[-2]
    revenue_growth = df["revenue"].pct_change().iloc[-1]
    if pd.notna(ar_days_diff) and ar_days_diff > 30 and (pd.isna(revenue_growth) or revenue_growth < 0.10):
        rev_text = f"{revenue_growth:.1%}" if pd.notna(revenue_growth) else "NA"
        detail = f"应收周转天数较上期增加{ar_days_diff:.1f}天，营收增速{rev_text}"
        anomalies.append(Anomaly("应收/存货异常", df["Report Date"].iloc[-1], "应收周转", detail, 2))
    if pd.notna(inv_days_diff) and inv_days_diff > 30 and (pd.isna(revenue_growth) or revenue_growth < 0.10):
        rev_text = f"{revenue_growth:.1%}" if pd.notna(revenue_growth) else "NA"
        detail = f"存货周转天数较上期增加{inv_days_diff:.1f}天，营收增速{rev_text}"
        anomalies.append(Anomaly("应收/存货异常", df["Report Date"].iloc[-1], "存货周转", detail, 2))

    # 占用率偏离
    def check_ratio(series: pd.Series, name: str):
        recent = series.dropna().tail(window)
        if recent.empty:
            return
        current = recent.iloc[-1]
        mean = recent.mean()
        deviation = current - mean
        if abs(deviation) > 0.15:
            sev = 2 if abs(deviation) < 0.25 else 3
            detail = f"{name}占用率{current:.2%}，较均值偏离{deviation:.2%}"
            anomalies.append(Anomaly("应收/存货异常", df["Report Date"].iloc[-1], name, detail, sev))

    check_ratio(safe_divide(df["accounts_receivable"], df["revenue"]), "应收/营收")
    check_ratio(safe_divide(df["inventories"], df["revenue"]), "存货/营收")
    return anomalies


def rule_capex_capitalization(df: pd.DataFrame, window: int = 4) -> List[Anomaly]:
    anomalies: List[Anomaly] = []
    if len(df) < 2:
        return anomalies
    capex_rate = df["capex_rate"]
    rnd_rate = df["rnd_rate"]
    recent = capex_rate.dropna().tail(window)
    if recent.empty:
        return anomalies
    current = recent.iloc[-1]
    baseline = recent.iloc[:-1].mean() if len(recent) > 1 else np.nan
    uplift = current - baseline if pd.notna(baseline) else np.nan
    if (current > 0.30) and (pd.notna(uplift) and uplift > 0.15):
        detail = f"资本开支率{current:.2%}，较近{len(recent)-1}期均值抬升{uplift:.2%}"
        anomalies.append(Anomaly("资本开支/费用资本化异常", df["Report Date"].iloc[-1], "资本开支率", detail, 3))

    # 资本开支上升 + 研发下降
    capex_rise = capex_rate.iloc[-1] - capex_rate.iloc[-2]
    rnd_drop = rnd_rate.iloc[-2] - rnd_rate.iloc[-1]
    if pd.notna(capex_rise) and pd.notna(rnd_drop) and capex_rise > 0.10 and rnd_drop > 0.10:
        detail = f"资本开支率单期上升{capex_rise:.2%}且研发费用率下降{rnd_drop:.2%}，可能存在费用资本化"
        anomalies.append(Anomaly("资本开支/费用资本化异常", df["Report Date"].iloc[-1], "资本化倾向", detail, 2))
    return anomalies


def evaluate_anomalies(df: pd.DataFrame, window: int = 4) -> List[Anomaly]:
    results: List[Anomaly] = []
    results.extend(rule_continuous_volatility(df))
    results.extend(rule_cost_expense(df, window))
    results.extend(rule_asset_liability_mismatch(df))
    results.extend(rule_cash_profit_gap(df))
    results.extend(rule_ar_inventory(df, window))
    results.extend(rule_capex_capitalization(df, window))
    return results


def build_anomaly_table(anomalies: List[Anomaly]) -> str:
    headers = ["规则", "触发日期", "指标/维度", "细节说明", "严重度(1-3)"]
    lines = ["| " + " | ".join(headers) + " |", "|" + "|".join(["---"] * len(headers)) + "|"]
    if not anomalies:
        lines.append("| 未触发 | - | - | - | - |")
        return "\n".join(lines)
    for a in anomalies:
        lines.append(
            "| "
            + " | ".join(
                [
                    a.rule,
                    a.date.strftime("%Y-%m-%d"),
                    a.metric,
                    a.detail.replace("|", "/"),
                    str(a.severity),
                ]
            )
            + " |"
        )
    return "\n".join(lines)


def build_snapshot_table(df: pd.DataFrame) -> str:
    latest = df.iloc[-1]
    def ratio_value(num, den):
        if pd.isna(num) or pd.isna(den) or den == 0:
            return ""
        return f"{num / den:.2%}"
    items = [
        ("报告期", latest["Report Date"].strftime("%Y-%m-%d")),
        ("营收", f"{latest['revenue']:,.0f}"),
        ("净利润", f"{latest['net_profit']:,.0f}"),
        ("经营现金流", f"{latest['ocf']:,.0f}"),
        ("毛利率", f"{latest['gross_margin']:.2%}" if pd.notna(latest["gross_margin"]) else ""),
        ("成本率", f"{latest['cost_rate']:.2%}" if pd.notna(latest["cost_rate"]) else ""),
        ("三费率", f"{latest['expense_rate']:.2%}" if pd.notna(latest["expense_rate"]) else ""),
        ("研发费用率", f"{latest['rnd_rate']:.2%}" if pd.notna(latest["rnd_rate"]) else ""),
        ("应收/营收", ratio_value(latest["accounts_receivable"], latest["revenue"])),
        ("存货/营收", ratio_value(latest["inventories"], latest["revenue"])),
        ("流动比率", f"{latest['current_ratio']:.2f}" if pd.notna(latest["current_ratio"]) else ""),
        ("短债占比", f"{latest['short_debt_ratio']:.2%}" if pd.notna(latest["short_debt_ratio"]) else ""),
        ("资本开支率", f"{latest['capex_rate']:.2%}" if pd.notna(latest["capex_rate"]) else ""),
    ]
    lines = ["| 指标 | 值 |", "| --- | --- |"]
    for k, v in items:
        lines.append(f"| {k} | {v} |")
    return "\n".join(lines)


def plot_trends(symbol: str, df: pd.DataFrame, output_dir: Path) -> list[str]:
    output_dir.mkdir(parents=True, exist_ok=True)
    image_files: list[str] = []

    # 图1：营收/净利/OCF增速
    fig, ax = plt.subplots(figsize=(10, 6))
    for name, series in {
        "营收增速": df["revenue"].pct_change(),
        "净利增速": df["net_profit"].pct_change(),
        "经营现金流增速": df["ocf"].pct_change(),
    }.items():
        ax.plot(df["Report Date"], series * 100, marker="o", label=name)
    ax.axhline(0, color="#888", linewidth=1)
    ax.set_ylabel("增速（%）")
    ax.set_xlabel("报告期")
    ax.set_title(f"{symbol} 关键增速", fontsize=14, fontweight="bold")
    ax.grid(alpha=0.3)
    plt.xticks(rotation=45)
    ax.legend()
    plt.tight_layout()
    fname1 = f"{symbol}_growth_trend.png"
    plt.savefig(output_dir / fname1, dpi=300, bbox_inches="tight")
    plt.close()
    image_files.append(fname1)

    # 图2：费用率&毛利率
    fig, ax = plt.subplots(figsize=(10, 6))
    for name, series in {
        "毛利率": df["gross_margin"],
        "成本率": df["cost_rate"],
        "三费率": df["expense_rate"],
        "研发费用率": df["rnd_rate"],
    }.items():
        ax.plot(df["Report Date"], series * 100, marker="o", label=name)
    ax.set_ylabel("比例（%）")
    ax.set_xlabel("报告期")
    ax.set_title(f"{symbol} 费用率/毛利率", fontsize=14, fontweight="bold")
    ax.grid(alpha=0.3)
    plt.xticks(rotation=45)
    ax.legend()
    plt.tight_layout()
    fname2 = f"{symbol}_expense_ratio.png"
    plt.savefig(output_dir / fname2, dpi=300, bbox_inches="tight")
    plt.close()
    image_files.append(fname2)

    # 图3：资产负债错配指标
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.bar(df["Report Date"], df["current_ratio"], label="流动比率", alpha=0.7)
    ax.plot(df["Report Date"], df["short_debt_ratio"] * 1.0, color="#D1495B", marker="s", label="短债占比")
    ax.plot(df["Report Date"], df["long_asset_ratio"] * 1.0, color="#00798C", marker="^", label="长期资产占比")
    ax.set_ylabel("比例")
    ax.set_xlabel("报告期")
    ax.set_title(f"{symbol} 期限结构指标", fontsize=14, fontweight="bold")
    ax.grid(alpha=0.3)
    plt.xticks(rotation=45)
    ax.legend()
    plt.tight_layout()
    fname3 = f"{symbol}_mismatch.png"
    plt.savefig(output_dir / fname3, dpi=300, bbox_inches="tight")
    plt.close()
    image_files.append(fname3)

    return image_files


def generate_markdown_report(
    symbol: str,
    df: pd.DataFrame,
    anomalies: List[Anomaly],
    image_files: list[str],
    output_dir: Path,
    freq_note: Optional[str] = None,
) -> Path:
    lines: list[str] = []
    lines.append("prompt：请在适当的位置插入图片，严格遵守markdown图片的插入规范，图片内容如下：图片1...")
    for idx, img in enumerate(image_files, 1):
        lines.append(f"图片{idx}：{img}")
    lines.append("")

    lines.append(f"# {symbol} 结构化异常检测报告")
    lines.append("")
    if freq_note:
        lines.append(f"> {freq_note}")
        lines.append("")

    lines.append("## 异常汇总")
    lines.append(build_anomaly_table(anomalies))
    lines.append("")

    lines.append("## 关键指标快照（最新一期）")
    lines.append(build_snapshot_table(df))
    lines.append("")

    output_dir.mkdir(parents=True, exist_ok=True)
    report_path = output_dir / f"{symbol}_struct_anomaly.md"
    with open(report_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return report_path


def struct_anomaly_analysis(symbol: str, number: int = 4) -> str:
    """结构化异常检测主入口。"""
    df = prepare_dataset(symbol, number)
    freq_note = detect_frequency_note(df["Report Date"])
    anomalies = evaluate_anomalies(df, window=min(number, 8))

    output_dir = Path(f"stock_report_data/report_data/{symbol}/struct_anomaly")
    image_files = plot_trends(symbol, df, output_dir)
    report_path = generate_markdown_report(symbol, df, anomalies, image_files, output_dir, freq_note)

    print(f"结构化异常检测报告已生成: {report_path}")
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
        periods_input = input("请输入分析期数(默认4): ").strip()
        periods = int(periods_input) if periods_input else 4

    struct_anomaly_analysis(stock_code, periods)
