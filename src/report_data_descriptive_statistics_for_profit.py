import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
from pathlib import Path
import warnings
from src.report_data_reader import report_data_reader
warnings.filterwarnings('ignore')

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
plt.rcParams['axes.unicode_minus'] = False

def load_profit_data(code, number=1):
    """加载利润表数据

    Args:
        code: 股票代码
        number: 要读取的期数，从最新一期开始往后数，默认为1
    """
    try:
        _, profit_report, _ = report_data_reader(code, number)
        profit_report['Report Date'] = pd.to_datetime(profit_report['Report Date'])
        profit_report = profit_report.sort_values('Report Date')
        return profit_report
    except Exception as e:
        print(f"Error loading data: {e}")
        return None

def calculate_profitability_ratios(df):
    """计算盈利能力指标"""
    ratios = pd.DataFrame()
    ratios['Report Date'] = df['Report Date']

    # 毛利率 = (营业收入 - 营业成本) / 营业收入
    ratios['毛利率'] = ((df['Operating Revenue'] - df['Operating Costs']) /
                       df['Operating Revenue'] * 100).round(2)

    # 净利率 = 净利润 / 营业收入
    ratios['净利率'] = (df['Net Profit Attributable to Parent'] /
                       df['Total Operating Revenue'] * 100).round(2)

    # 营业利润率 = 营业利润 / 营业收入
    ratios['营业利润率'] = (df['Operating Profit'] /
                          df['Total Operating Revenue'] * 100).round(2)

    # EBITDA利润率 (简化计算)
    ebitda = df['Operating Profit'] + df['Administrative Expenses'] * 0.1  # 简化折旧摊销估算
    ratios['EBITDA利润率'] = (ebitda / df['Total Operating Revenue'] * 100).round(2)

    return ratios

def calculate_expense_ratios(df):
    """计算成本费用构成指标"""
    ratios = pd.DataFrame()
    ratios['Report Date'] = df['Report Date']

    # 销售费用率
    ratios['销售费用率'] = (df['Selling Expenses'] /
                          df['Total Operating Revenue'] * 100).round(2)

    # 管理费用率
    ratios['管理费用率'] = (df['Administrative Expenses'] /
                          df['Total Operating Revenue'] * 100).round(2)

    # 研发费用率
    ratios['研发费用率'] = (df['R&D Expenses'] /
                          df['Total Operating Revenue'] * 100).round(2)

    # 财务费用率
    ratios['财务费用率'] = (df['Financial Expenses'] /
                          df['Total Operating Revenue'] * 100).round(2)

    # 期间费用率
    period_expenses = (df['Selling Expenses'] + df['Administrative Expenses'] +
                      df['R&D Expenses'] + df['Financial Expenses'])
    ratios['期间费用率'] = (period_expenses /
                          df['Total Operating Revenue'] * 100).round(2)

    return ratios

def calculate_revenue_quality(df):
    """计算收入质量指标"""
    ratios = pd.DataFrame()
    ratios['Report Date'] = df['Report Date']

    # 主营业务收入占比
    ratios['主营业务收入占比'] = (df['Operating Revenue'] /
                              df['Total Operating Revenue'] * 100).round(2)

    # 其他业务收入占比
    ratios['其他业务收入占比'] = (df['Other Business Revenue'] /
                              df['Total Operating Revenue'] * 100).round(2)

    # 投资收益占比
    ratios['投资收益占营业利润比'] = (df['Investment Income'] /
                                  df['Operating Profit'] * 100).round(2)

    return ratios

def calculate_growth_rates(df):
    """计算增长表现指标"""
    ratios = pd.DataFrame()
    ratios['Report Date'] = df['Report Date']

    # 营业收入增长率
    ratios['营业收入增长率'] = (df['Total Operating Revenue'].pct_change() * 100).round(2)

    # 净利润增长率
    ratios['净利润增长率'] = (df['Net Profit Attributable to Parent'].pct_change() * 100).round(2)

    # 营业利润增长率
    ratios['营业利润增长率'] = (df['Operating Profit'].pct_change() * 100).round(2)

    # 毛利变动幅度
    gross_profit = df['Operating Revenue'] - df['Operating Costs']
    ratios['毛利变动幅度'] = (gross_profit.pct_change() * 100).round(2)

    return ratios

def plot_profitability_trends(ratios, code, output_dir):
    """绘制盈利能力趋势图"""
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    fig.suptitle('盈利能力指标趋势', fontsize=16, fontweight='bold')

    metrics = ['毛利率', '净利率', '营业利润率', 'EBITDA利润率']
    colors = ['#2E86AB', '#A23B72', '#F18F01', '#06A77D']

    for idx, (ax, metric, color) in enumerate(zip(axes.flat, metrics, colors)):
        ax.plot(ratios['Report Date'], ratios[metric], marker='o',
                linewidth=2, markersize=6, color=color, label=metric)
        ax.set_title(metric, fontsize=12, fontweight='bold')
        ax.set_xlabel('报告日期', fontsize=10)
        ax.set_ylabel('比率 (%)', fontsize=10)
        ax.grid(True, alpha=0.3)
        ax.legend()
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)

    plt.tight_layout()
    filename = f"{code}_盈利能力趋势.png"
    plt.savefig(os.path.join(output_dir, filename), dpi=300, bbox_inches='tight')
    plt.close()
    return filename

def plot_expense_structure(ratios, code, output_dir):
    """绘制成本费用构成图"""
    fig, axes = plt.subplots(1, 2, figsize=(15, 6))
    fig.suptitle('成本费用构成分析', fontsize=16, fontweight='bold')

    # 期间费用率趋势
    ax1 = axes[0]
    expense_metrics = ['销售费用率', '管理费用率', '研发费用率', '财务费用率']
    colors = ['#E63946', '#F77F00', '#06A77D', '#457B9D']

    for metric, color in zip(expense_metrics, colors):
        ax1.plot(ratios['Report Date'], ratios[metric], marker='o',
                linewidth=2, markersize=5, color=color, label=metric)

    ax1.set_title('期间费用率趋势', fontsize=12, fontweight='bold')
    ax1.set_xlabel('报告日期', fontsize=10)
    ax1.set_ylabel('费用率 (%)', fontsize=10)
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45)

    # 最新期间费用构成饼图
    ax2 = axes[1]
    latest_data = ratios.iloc[-1]
    expense_values = [latest_data[metric] for metric in expense_metrics]

    # 处理负值：取绝对值用于饼图显示
    expense_values_abs = [abs(val) if pd.notna(val) else 0 for val in expense_values]

    # 只有当有正值时才绘制饼图
    if sum(expense_values_abs) > 0:
        ax2.pie(expense_values_abs, labels=expense_metrics, autopct='%1.1f%%',
                colors=colors, startangle=90)
        ax2.set_title(f'最新期间费用构成 ({latest_data["Report Date"].strftime("%Y-%m-%d")})',
                      fontsize=12, fontweight='bold')
    else:
        ax2.text(0.5, 0.5, '数据不足', ha='center', va='center', fontsize=14)
        ax2.set_title(f'最新期间费用构成 ({latest_data["Report Date"].strftime("%Y-%m-%d")})',
                      fontsize=12, fontweight='bold')

    plt.tight_layout()
    filename = f"{code}_成本费用构成.png"
    plt.savefig(os.path.join(output_dir, filename), dpi=300, bbox_inches='tight')
    plt.close()
    return filename

def plot_revenue_quality(ratios, code, output_dir):
    """绘制收入质量分析图"""
    fig, axes = plt.subplots(1, 2, figsize=(15, 6))
    fig.suptitle('收入质量分析', fontsize=16, fontweight='bold')

    # 主营业务收入占比趋势
    ax1 = axes[0]
    ax1.plot(ratios['Report Date'], ratios['主营业务收入占比'],
            marker='o', linewidth=2, markersize=6, color='#2E86AB', label='主营业务收入占比')
    ax1.plot(ratios['Report Date'], ratios['其他业务收入占比'],
            marker='s', linewidth=2, markersize=6, color='#F18F01', label='其他业务收入占比')
    ax1.set_title('收入构成趋势', fontsize=12, fontweight='bold')
    ax1.set_xlabel('报告日期', fontsize=10)
    ax1.set_ylabel('占比 (%)', fontsize=10)
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45)

    # 投资收益占营业利润比
    ax2 = axes[1]
    ax2.bar(ratios['Report Date'], ratios['投资收益占营业利润比'],
           color='#06A77D', alpha=0.7)
    ax2.set_title('投资收益占营业利润比', fontsize=12, fontweight='bold')
    ax2.set_xlabel('报告日期', fontsize=10)
    ax2.set_ylabel('占比 (%)', fontsize=10)
    ax2.grid(True, alpha=0.3, axis='y')
    plt.setp(ax2.xaxis.get_majorticklabels(), rotation=45)

    plt.tight_layout()
    filename = f"{code}_收入质量分析.png"
    plt.savefig(os.path.join(output_dir, filename), dpi=300, bbox_inches='tight')
    plt.close()
    return filename

def plot_growth_trends(ratios, code, output_dir):
    """绘制增长表现趋势图"""
    fig, axes = plt.subplots(2, 2, figsize=(15, 10))
    fig.suptitle('增长表现分析', fontsize=16, fontweight='bold')

    metrics = ['营业收入增长率', '净利润增长率', '营业利润增长率', '毛利变动幅度']
    colors = ['#2E86AB', '#E63946', '#F18F01', '#06A77D']

    for idx, (ax, metric, color) in enumerate(zip(axes.flat, metrics, colors)):
        data = ratios[metric].dropna()
        dates = ratios['Report Date'][ratios[metric].notna()]
        ax.bar(dates, data, color=color, alpha=0.7, label=metric)
        ax.axhline(y=0, color='black', linestyle='--', linewidth=1)
        ax.set_title(metric, fontsize=12, fontweight='bold')
        ax.set_xlabel('报告日期', fontsize=10)
        ax.set_ylabel('增长率 (%)', fontsize=10)
        ax.grid(True, alpha=0.3, axis='y')
        ax.legend()
        plt.setp(ax.xaxis.get_majorticklabels(), rotation=45)

    plt.tight_layout()
    filename = f"{code}_增长表现分析.png"
    plt.savefig(os.path.join(output_dir, filename), dpi=300, bbox_inches='tight')
    plt.close()
    return filename

def generate_statistics_summary(profitability, expense, revenue_quality, growth):
    """生成统计摘要"""
    summary = {}

    # 盈利能力统计
    summary['盈利能力'] = {
        '毛利率': {
            '均值': profitability['毛利率'].mean(),
            '最新': profitability['毛利率'].iloc[-1],
            '最大': profitability['毛利率'].max(),
            '最小': profitability['毛利率'].min()
        },
        '净利率': {
            '均值': profitability['净利率'].mean(),
            '最新': profitability['净利率'].iloc[-1],
            '最大': profitability['净利率'].max(),
            '最小': profitability['净利率'].min()
        },
        '营业利润率': {
            '均值': profitability['营业利润率'].mean(),
            '最新': profitability['营业利润率'].iloc[-1],
            '最大': profitability['营业利润率'].max(),
            '最小': profitability['营业利润率'].min()
        }
    }

    # 成本费用统计
    summary['成本费用'] = {
        '期间费用率': {
            '均值': expense['期间费用率'].mean(),
            '最新': expense['期间费用率'].iloc[-1]
        },
        '销售费用率': {
            '均值': expense['销售费用率'].mean(),
            '最新': expense['销售费用率'].iloc[-1]
        },
        '研发费用率': {
            '均值': expense['研发费用率'].mean(),
            '最新': expense['研发费用率'].iloc[-1]
        }
    }

    # 收入质量统计
    summary['收入质量'] = {
        '主营业务收入占比': {
            '均值': revenue_quality['主营业务收入占比'].mean(),
            '最新': revenue_quality['主营业务收入占比'].iloc[-1]
        }
    }

    # 增长表现统计
    summary['增长表现'] = {
        '营业收入增长率': {
            '均值': growth['营业收入增长率'].mean(),
            '最新': growth['营业收入增长率'].iloc[-1]
        },
        '净利润增长率': {
            '均值': growth['净利润增长率'].mean(),
            '最新': growth['净利润增长率'].iloc[-1]
        }
    }

    return summary

def generate_markdown_report(code, summary, image_files, output_dir):
    """生成Markdown报告"""
    report_lines = []

    # 添加图片文件名提示
    report_lines.append("**prompt：可用的图片文件名称如下，按照markdown文件的图片插入规范在文档的对应位置插入图片**\n")
    for img in image_files:
        report_lines.append(f"- {img}")
    report_lines.append("\n---\n")

    # 报告标题
    report_lines.append(f"# {code} 利润表描述性统计分析报告\n")
    report_lines.append(f"**生成日期**: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")

    # 1. 盈利能力分析
    report_lines.append("## 1. 盈利能力分析\n")
    report_lines.append("盈利能力是衡量企业每一块钱收入带来产出的核心指标。\n\n")

    prof = summary['盈利能力']
    report_lines.append("### 1.1 关键指标统计\n\n")
    report_lines.append("| 指标 | 均值 | 最新值 | 最大值 | 最小值 |\n")
    report_lines.append("|------|------|--------|--------|--------|\n")
    report_lines.append(f"| 毛利率 | {prof['毛利率']['均值']:.2f}% | {prof['毛利率']['最新']:.2f}% | {prof['毛利率']['最大']:.2f}% | {prof['毛利率']['最小']:.2f}% |\n")
    report_lines.append(f"| 净利率 | {prof['净利率']['均值']:.2f}% | {prof['净利率']['最新']:.2f}% | {prof['净利率']['最大']:.2f}% | {prof['净利率']['最小']:.2f}% |\n")
    report_lines.append(f"| 营业利润率 | {prof['营业利润率']['均值']:.2f}% | {prof['营业利润率']['最新']:.2f}% | {prof['营业利润率']['最大']:.2f}% | {prof['营业利润率']['最小']:.2f}% |\n\n")

    report_lines.append("### 1.2 分析要点\n\n")
    report_lines.append(f"- **毛利率**：最新值为 {prof['毛利率']['最新']:.2f}%，反映了企业产品或服务的定价能力和成本控制水平。\n")
    report_lines.append(f"- **净利率**：最新值为 {prof['净利率']['最新']:.2f}%，体现了企业最终的盈利效率。\n")
    report_lines.append(f"- **营业利润率**：最新值为 {prof['营业利润率']['最新']:.2f}%，显示了核心业务的盈利能力。\n\n")

    # 2. 成本费用构成分析
    report_lines.append("## 2. 成本费用构成分析\n")
    report_lines.append("成本费用构成反映了企业的开支偏好与管控能力。\n\n")

    exp = summary['成本费用']
    report_lines.append("### 2.1 期间费用统计\n\n")
    report_lines.append("| 指标 | 均值 | 最新值 |\n")
    report_lines.append("|------|------|--------|\n")
    report_lines.append(f"| 期间费用率 | {exp['期间费用率']['均值']:.2f}% | {exp['期间费用率']['最新']:.2f}% |\n")
    report_lines.append(f"| 销售费用率 | {exp['销售费用率']['均值']:.2f}% | {exp['销售费用率']['最新']:.2f}% |\n")
    report_lines.append(f"| 研发费用率 | {exp['研发费用率']['均值']:.2f}% | {exp['研发费用率']['最新']:.2f}% |\n\n")

    report_lines.append("### 2.2 分析要点\n\n")
    report_lines.append(f"- **期间费用率**：最新值为 {exp['期间费用率']['最新']:.2f}%，反映了企业整体费用管控水平。\n")
    report_lines.append(f"- **销售费用率**：最新值为 {exp['销售费用率']['最新']:.2f}%，体现了市场拓展投入力度。\n")
    report_lines.append(f"- **研发费用率**：最新值为 {exp['研发费用率']['最新']:.2f}%，显示了企业创新投入强度。\n\n")

    # 3. 收入质量分析
    report_lines.append("## 3. 收入质量分析\n")
    report_lines.append("收入质量分析关注核心业务的贡献度。\n\n")

    rev = summary['收入质量']
    report_lines.append("### 3.1 收入构成\n\n")
    report_lines.append("| 指标 | 均值 | 最新值 |\n")
    report_lines.append("|------|------|--------|\n")
    report_lines.append(f"| 主营业务收入占比 | {rev['主营业务收入占比']['均值']:.2f}% | {rev['主营业务收入占比']['最新']:.2f}% |\n\n")

    report_lines.append("### 3.2 分析要点\n\n")
    report_lines.append(f"- **主营业务收入占比**：最新值为 {rev['主营业务收入占比']['最新']:.2f}%，占比越高说明核心业务越稳固。\n\n")

    # 4. 增长表现分析
    report_lines.append("## 4. 增长表现分析\n")
    report_lines.append("增长表现反映了企业业务扩张的速度和质量。\n\n")

    growth = summary['增长表现']
    report_lines.append("### 4.1 增长率统计\n\n")
    report_lines.append("| 指标 | 均值 | 最新值 |\n")
    report_lines.append("|------|------|--------|\n")
    report_lines.append(f"| 营业收入增长率 | {growth['营业收入增长率']['均值']:.2f}% | {growth['营业收入增长率']['最新']:.2f}% |\n")
    report_lines.append(f"| 净利润增长率 | {growth['净利润增长率']['均值']:.2f}% | {growth['净利润增长率']['最新']:.2f}% |\n\n")

    report_lines.append("### 4.2 分析要点\n\n")
    report_lines.append(f"- **营业收入增长率**：最新值为 {growth['营业收入增长率']['最新']:.2f}%，反映了业务规模扩张速度。\n")
    report_lines.append(f"- **净利润增长率**：最新值为 {growth['净利润增长率']['最新']:.2f}%，体现了盈利增长质量。\n\n")

    # 5. 综合评价
    report_lines.append("## 5. 综合评价\n\n")
    report_lines.append("### 5.1 优势分析\n\n")
    report_lines.append("- 根据盈利能力指标，可以评估企业的盈利质量和成本控制能力。\n")
    report_lines.append("- 成本费用构成显示了企业在销售、研发等方面的投入策略。\n")
    report_lines.append("- 收入质量指标反映了核心业务的稳定性。\n\n")

    report_lines.append("### 5.2 关注点\n\n")
    report_lines.append("- 关注盈利能力指标的波动趋势，判断企业盈利稳定性。\n")
    report_lines.append("- 分析期间费用率变化，评估费用管控效果。\n")
    report_lines.append("- 观察增长率指标，判断企业发展动力是否充足。\n\n")

    report_lines.append("---\n")
    report_lines.append("*本报告由自动化程序生成，数据来源于公司财务报表。*\n")

    return report_lines

def main(code, number=1):
    """主函数

    Args:
        code: 股票代码
        number: 要分析的期数，从最新一期开始往后数，默认为1
    """
    print(f"开始生成 {code} 的利润表描述性统计分析（最近{number}期）...")

    # 创建输出目录
    output_dir = f"stock_report_data/report_data/{code}/descriptive statistics for Profit"
    os.makedirs(output_dir, exist_ok=True)

    # 加载数据
    df = load_profit_data(code, number)
    if df is None:
        print("数据加载失败！")
        return

    # 计算各类指标
    print("计算盈利能力指标...")
    profitability = calculate_profitability_ratios(df)

    print("计算成本费用指标...")
    expense = calculate_expense_ratios(df)

    print("计算收入质量指标...")
    revenue_quality = calculate_revenue_quality(df)

    print("计算增长表现指标...")
    growth = calculate_growth_rates(df)

    # 生成可视化图表
    print("生成可视化图表...")
    image_files = []

    img1 = plot_profitability_trends(profitability, code, output_dir)
    image_files.append(img1)
    print(f"  - {img1}")

    img2 = plot_expense_structure(expense, code, output_dir)
    image_files.append(img2)
    print(f"  - {img2}")

    img3 = plot_revenue_quality(revenue_quality, code, output_dir)
    image_files.append(img3)
    print(f"  - {img3}")

    img4 = plot_growth_trends(growth, code, output_dir)
    image_files.append(img4)
    print(f"  - {img4}")

    # 生成统计摘要
    print("生成统计摘要...")
    summary = generate_statistics_summary(profitability, expense, revenue_quality, growth)

    # 生成Markdown报告
    print("生成Markdown报告...")
    report_content = generate_markdown_report(code, summary, image_files, output_dir)

    # 保存报告
    report_filename = f"{code}_descriptive_statistics_for_profit.md"
    report_path = os.path.join(output_dir, report_filename)
    with open(report_path, 'w', encoding='utf-8') as f:
        f.writelines(report_content)

    print(f"\n报告生成完成！")
    print(f"报告路径: {report_path}")
    print(f"图表数量: {len(image_files)}")
    print(f"分析期数: {number}")

    return output_dir

def report_data_descriptive_statistics_for_profit(Symbol, number=1):
    """
    利润表描述性统计分析

    Args:
        Symbol: 股票代码，如 '600519'
        number: 要读取的期数，从最新一期开始往后数，默认为1（只取最新一期）
                例如：number=3 表示读取最新一期、第二期、第三期，共3期数据

    Returns:
        str: 输出目录路径
    """
    return main(Symbol, number)

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 2:
        code = sys.argv[1]
        number = int(sys.argv[2])
    elif len(sys.argv) > 1:
        code = sys.argv[1]
        number = 1
    else:
        code = input("请输入股票代码: ")
        number = int(input("请输入分析期数（默认1）: ") or "1")
    main(code, number)










