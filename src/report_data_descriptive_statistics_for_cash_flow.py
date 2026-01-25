import pandas as pd
import matplotlib.pyplot as plt
import os
from pathlib import Path
from src.report_data_reader import report_data_reader

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei']
plt.rcParams['axes.unicode_minus'] = False

def report_data_descriptive_statistics_for_cash_flow(Symbol, number=1):
    '''
    现金流量表描述性统计分析

    Args:
        Symbol: 股票代码，如 '600519'
        number: 要读取的期数，从最新一期开始往后数，默认为1（只取最新一期）
                例如：number=3 表示读取最新一期、第二期、第三期，共3期数据
    '''
    # 读取财务报表数据
    balance_report, profit_report, cash_flow_report = report_data_reader(Symbol, number)

    # 创建输出目录
    output_dir = Path(f"stock_report_data/report_data/{Symbol}/descriptive statistics for cash flow")
    output_dir.mkdir(parents=True, exist_ok=True)

    # 存储图片文件名
    image_files = []

    # 1. 现金流量结构分析
    image_files.extend(analyze_cash_flow_structure(cash_flow_report, Symbol, output_dir))

    # 2. 现金流量趋势分析
    if number > 1:
        image_files.extend(analyze_cash_flow_trends(cash_flow_report, Symbol, output_dir))

    # 3. 资产负债结构分析
    image_files.extend(analyze_balance_structure(balance_report, Symbol, output_dir))

    # 4. 资本结构分析
    image_files.extend(analyze_capital_structure(balance_report, Symbol, output_dir))

    # 5. 变动趋势分析
    if number > 1:
        image_files.extend(analyze_change_trends(balance_report, Symbol, output_dir))

    # 生成Markdown报告
    generate_markdown_report(Symbol, balance_report, profit_report, cash_flow_report,
                           image_files, output_dir, number)

    print(f"报告生成完成！输出目录: {output_dir}")
    return output_dir


def analyze_cash_flow_structure(cash_flow_report, symbol, output_dir):
    """分析现金流量结构"""
    image_files = []
    latest_data = cash_flow_report.iloc[0]

    # 三大活动现金流量净额对比
    activities = {
        '经营活动': latest_data.get('Net Cash Flow from Operating Activities', 0),
        '投资活动': latest_data.get('Net Cash Flow from Investing Activities', 0),
        '融资活动': latest_data.get('Net Cash Flow from Financing Activities', 0)
    }

    fig, ax = plt.subplots(figsize=(10, 6))
    colors = ['#2ecc71' if v >= 0 else '#e74c3c' for v in activities.values()]
    bars = ax.bar(activities.keys(), activities.values(), color=colors, alpha=0.7)
    ax.axhline(y=0, color='black', linestyle='-', linewidth=0.5)
    ax.set_title(f'{symbol} 三大活动现金流量净额对比', fontsize=14, fontweight='bold')
    ax.set_ylabel('金额（元）', fontsize=12)
    ax.grid(axis='y', alpha=0.3)

    for bar in bars:
        height = bar.get_height()
        ax.text(bar.get_x() + bar.get_width()/2., height,
                f'{height/100000000:.2f}亿',
                ha='center', va='bottom' if height >= 0 else 'top', fontsize=10)

    plt.tight_layout()
    filename = f"{symbol}_三大活动现金流量净额对比.png"
    plt.savefig(output_dir / filename, dpi=300, bbox_inches='tight')
    plt.close()
    image_files.append(filename)

    return image_files


def analyze_cash_flow_trends(cash_flow_report, symbol, output_dir):
    """分析现金流量趋势"""
    image_files = []

    # 现金流量趋势图
    fig, ax = plt.subplots(figsize=(12, 6))
    dates = cash_flow_report['Report Date'].tolist()

    operating = cash_flow_report['Net Cash Flow from Operating Activities'].tolist()
    investing = cash_flow_report['Net Cash Flow from Investing Activities'].tolist()
    financing = cash_flow_report['Net Cash Flow from Financing Activities'].tolist()

    ax.plot(dates, operating, marker='o', label='经营活动现金流', linewidth=2)
    ax.plot(dates, investing, marker='s', label='投资活动现金流', linewidth=2)
    ax.plot(dates, financing, marker='^', label='融资活动现金流', linewidth=2)

    ax.axhline(y=0, color='black', linestyle='--', linewidth=0.5)
    ax.set_title(f'{symbol} 现金流量趋势分析', fontsize=14, fontweight='bold')
    ax.set_xlabel('报告期', fontsize=12)
    ax.set_ylabel('金额（元）', fontsize=12)
    ax.legend(loc='best')
    ax.grid(True, alpha=0.3)
    plt.xticks(rotation=45)
    plt.tight_layout()

    filename = f"{symbol}_现金流量趋势分析.png"
    plt.savefig(output_dir / filename, dpi=300, bbox_inches='tight')
    plt.close()
    image_files.append(filename)

    return image_files


def analyze_balance_structure(balance_report, symbol, output_dir):
    """分析资产负债结构"""
    image_files = []
    latest_data = balance_report.iloc[0]

    # 1. 资产结构分析
    current_assets = latest_data.get('Total Current Assets', 0)
    non_current_assets = latest_data.get('Total Non-current Assets', 0)
    total_assets = latest_data.get('Total Assets', 1)

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    # 流动资产vs非流动资产
    asset_data = [current_assets, non_current_assets]
    asset_labels = ['流动资产', '非流动资产']
    colors1 = ['#3498db', '#9b59b6']
    ax1.pie(asset_data, labels=asset_labels, autopct='%1.1f%%',
            colors=colors1, startangle=90)
    ax1.set_title(f'{symbol} 资产结构分析', fontsize=12, fontweight='bold')

    # 流动资产细分
    cash = latest_data.get('Cash and Cash Equivalents', 0)
    receivables = latest_data.get('Accounts Receivable', 0)
    inventory = latest_data.get('Inventories', 0)
    other_current = current_assets - cash - receivables - inventory

    asset_detail = [cash, receivables, inventory, other_current]
    asset_detail_labels = ['货币资金', '应收账款', '存货', '其他流动资产']
    colors2 = ['#2ecc71', '#f39c12', '#e74c3c', '#95a5a6']
    ax2.pie(asset_detail, labels=asset_detail_labels, autopct='%1.1f%%',
            colors=colors2, startangle=90)
    ax2.set_title(f'{symbol} 流动资产细分', fontsize=12, fontweight='bold')

    plt.tight_layout()
    filename = f"{symbol}_资产结构分析.png"
    plt.savefig(output_dir / filename, dpi=300, bbox_inches='tight')
    plt.close()
    image_files.append(filename)

    return image_files

def analyze_capital_structure(balance_report, symbol, output_dir):
    """分析资本结构"""
    image_files = []
    latest_data = balance_report.iloc[0]

    # 负债结构分析
    current_liabilities = latest_data.get('Total Current Liabilities', 0)
    non_current_liabilities = latest_data.get('Total Non-current Liabilities', 0)
    total_equity = latest_data.get('Total Owner\'s Equity (or Shareholders\' Equity)', 0)
    total_assets = latest_data.get('Total Assets', 1)

    # 资产负债率、产权比率等指标
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

    # 负债结构饼图
    liability_data = [current_liabilities, non_current_liabilities, total_equity]
    liability_labels = ['流动负债', '非流动负债', '所有者权益']
    colors = ['#e74c3c', '#f39c12', '#2ecc71']
    ax1.pie(liability_data, labels=liability_labels, autopct='%1.1f%%',
            colors=colors, startangle=90)
    ax1.set_title(f'{symbol} 资本结构分析', fontsize=12, fontweight='bold')

    # 关键财务指标
    asset_liability_ratio = (current_liabilities + non_current_liabilities) / total_assets * 100
    equity_ratio = total_equity / total_assets * 100
    debt_to_equity = (current_liabilities + non_current_liabilities) / total_equity if total_equity > 0 else 0

    indicators = ['资产负债率(%)', '权益比率(%)', '产权比率']
    values = [asset_liability_ratio, equity_ratio, debt_to_equity]

    bars = ax2.barh(indicators, values, color=['#e74c3c', '#2ecc71', '#3498db'])
    ax2.set_title(f'{symbol} 关键财务指标', fontsize=12, fontweight='bold')
    ax2.set_xlabel('数值', fontsize=10)

    for i, (bar, val) in enumerate(zip(bars, values)):
        if i < 2:
            ax2.text(val, bar.get_y() + bar.get_height()/2, f'{val:.2f}%',
                    ha='left', va='center', fontsize=10)
        else:
            ax2.text(val, bar.get_y() + bar.get_height()/2, f'{val:.2f}',
                    ha='left', va='center', fontsize=10)

    plt.tight_layout()
    filename = f"{symbol}_资本结构分析.png"
    plt.savefig(output_dir / filename, dpi=300, bbox_inches='tight')
    plt.close()
    image_files.append(filename)

    return image_files


def analyze_change_trends(balance_report, symbol, output_dir):
    """分析变动趋势"""
    image_files = []

    # 总资产增长趋势
    fig, ax = plt.subplots(figsize=(12, 6))
    dates = balance_report['Report Date'].tolist()
    total_assets = balance_report['Total Assets'].tolist()

    ax.plot(dates, total_assets, marker='o', linewidth=2, color='#3498db')
    ax.set_title(f'{symbol} 总资产变动趋势', fontsize=14, fontweight='bold')
    ax.set_xlabel('报告期', fontsize=12)
    ax.set_ylabel('总资产（元）', fontsize=12)
    ax.grid(True, alpha=0.3)
    plt.xticks(rotation=45)
    plt.tight_layout()

    filename = f"{symbol}_总资产变动趋势.png"
    plt.savefig(output_dir / filename, dpi=300, bbox_inches='tight')
    plt.close()
    image_files.append(filename)

    # 主要科目同比变化
    if len(balance_report) >= 2:
        latest = balance_report.iloc[0]
        previous = balance_report.iloc[1]

        items = {
            '总资产': ('Total Assets', latest.get('Total Assets', 0), previous.get('Total Assets', 1)),
            '流动资产': ('Total Current Assets', latest.get('Total Current Assets', 0), previous.get('Total Current Assets', 1)),
            '非流动资产': ('Total Non-current Assets', latest.get('Total Non-current Assets', 0), previous.get('Total Non-current Assets', 1)),
            '总负债': ('Total Liabilities', latest.get('Total Liabilities', 0), previous.get('Total Liabilities', 1)),
            '所有者权益': ('Total Owner\'s Equity (or Shareholders\' Equity)', 
                       latest.get('Total Owner\'s Equity (or Shareholders\' Equity)', 0),
                       previous.get('Total Owner\'s Equity (or Shareholders\' Equity)', 1))
        }

        labels = []
        changes = []
        for name, (key, curr, prev) in items.items():
            if prev != 0:
                change_pct = ((curr - prev) / prev) * 100
                labels.append(name)
                changes.append(change_pct)

        fig, ax = plt.subplots(figsize=(10, 6))
        colors = ['#2ecc71' if c >= 0 else '#e74c3c' for c in changes]
        bars = ax.barh(labels, changes, color=colors, alpha=0.7)
        ax.axvline(x=0, color='black', linestyle='-', linewidth=0.5)
        ax.set_title(f'{symbol} 主要科目同比变化率', fontsize=14, fontweight='bold')
        ax.set_xlabel('变化率 (%)', fontsize=12)
        ax.grid(axis='x', alpha=0.3)

        for bar, val in zip(bars, changes):
            ax.text(val, bar.get_y() + bar.get_height()/2, f'{val:.2f}%',
                   ha='left' if val >= 0 else 'right', va='center', fontsize=10)

        plt.tight_layout()
        filename = f"{symbol}_主要科目同比变化.png"
        plt.savefig(output_dir / filename, dpi=300, bbox_inches='tight')
        plt.close()
        image_files.append(filename)

    return image_files


def generate_markdown_report(symbol, balance_report, profit_report, cash_flow_report,
                            image_files, output_dir, number):
    """生成Markdown报告"""
    latest_balance = balance_report.iloc[0]
    latest_cash_flow = cash_flow_report.iloc[0]
    report_date = latest_balance.get('Report Date', 'N/A')

    # 计算关键指标
    total_assets = latest_balance.get('Total Assets', 0)
    current_assets = latest_balance.get('Total Current Assets', 0)
    non_current_assets = latest_balance.get('Total Non-current Assets', 0)
    current_liabilities = latest_balance.get('Total Current Liabilities', 0)
    non_current_liabilities = latest_balance.get('Total Non-current Liabilities', 0)
    total_equity = latest_balance.get('Total Owner\'s Equity (or Shareholders\' Equity)', 0)
    
    cash = latest_balance.get('Cash and Cash Equivalents', 0)
    receivables = latest_balance.get('Accounts Receivable', 0)
    inventory = latest_balance.get('Inventories', 0)

    operating_cf = latest_cash_flow.get('Net Cash Flow from Operating Activities', 0)
    investing_cf = latest_cash_flow.get('Net Cash Flow from Investing Activities', 0)
    financing_cf = latest_cash_flow.get('Net Cash Flow from Financing Activities', 0)

    # 计算比率
    current_asset_ratio = (current_assets / total_assets * 100) if total_assets > 0 else 0
    non_current_asset_ratio = (non_current_assets / total_assets * 100) if total_assets > 0 else 0
    inventory_ratio = (inventory / total_assets * 100) if total_assets > 0 else 0
    receivables_ratio = (receivables / total_assets * 100) if total_assets > 0 else 0
    
    total_liabilities = current_liabilities + non_current_liabilities
    asset_liability_ratio = (total_liabilities / total_assets * 100) if total_assets > 0 else 0
    debt_to_equity = (total_liabilities / total_equity) if total_equity > 0 else 0
    equity_multiplier = (total_assets / total_equity) if total_equity > 0 else 0

    report_content = f"""# {symbol} 财务报表描述性统计分析报告

**报告日期**: {report_date}  
**分析期数**: {number}期

---

## Prompt
可用的图片文件名称如下，按照markdown文件的图片插入规范在文档的对应位置插入图片：

"""

    # 添加图片列表
    for img in image_files:
        report_content += f"- {img}\n"

    report_content += f"""

---

## 一、现金流量分析

### 1.1 三大活动现金流量概况

| 活动类型 | 现金流量净额（元） | 现金流量净额（亿元） |
|---------|------------------|-------------------|
| 经营活动 | {operating_cf:,.2f} | {operating_cf/100000000:.2f} |
| 投资活动 | {investing_cf:,.2f} | {investing_cf/100000000:.2f} |
| 融资活动 | {financing_cf:,.2f} | {financing_cf/100000000:.2f} |

"""

    report_content += """
### 1.2 现金流量结构分析

"""

    # 保存报告
    report_path = output_dir / f"{symbol}_descriptive_statistics_for_cash_flow.md"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report_content)
    
    # 现金流量分析
    if operating_cf > 0:
        report_content += "- **经营活动现金流为正**，表明公司主营业务能够产生正向现金流，经营状况良好。\n"
    else:
        report_content += "- **经营活动现金流为负**，需要关注公司经营状况和资金周转情况。\n"

    if investing_cf < 0:
        report_content += "- **投资活动现金流为负**，表明公司正在进行资本支出或投资扩张。\n"
    else:
        report_content += "- **投资活动现金流为正**，可能来自资产处置或投资回收。\n"

    if financing_cf > 0:
        report_content += "- **融资活动现金流为正**，公司通过融资渠道获得资金。\n"
    else:
        report_content += "- **融资活动现金流为负**，公司可能在偿还债务或分配股利。\n"

    report_content += f"""

---

## 二、资产结构分析

### 2.1 资产流动性分析

| 指标 | 金额（元） | 占总资产比例 |
|-----|-----------|------------|
| 流动资产 | {current_assets:,.2f} | {current_asset_ratio:.2f}% |
| 非流动资产 | {non_current_assets:,.2f} | {non_current_asset_ratio:.2f}% |
| 总资产 | {total_assets:,.2f} | 100.00% |

### 2.2 流动资产细分

| 项目 | 金额（元） | 占总资产比例 |
|-----|-----------|------------|
| 货币资金 | {cash:,.2f} | {(cash/total_assets*100) if total_assets > 0 else 0:.2f}% |
| 应收账款 | {receivables:,.2f} | {receivables_ratio:.2f}% |
| 存货 | {inventory:,.2f} | {inventory_ratio:.2f}% |

### 2.3 资产结构评价

"""

    if current_asset_ratio > 50:
        report_content += "- 流动资产占比较高，资产流动性较好，短期偿债能力较强。\n"
    else:
        report_content += "- 非流动资产占比较高，可能属于重资产行业，需关注资产使用效率。\n"

    if inventory_ratio > 20:
        report_content += f"- 存货占比{inventory_ratio:.2f}%，需关注存货周转效率和减值风险。\n"

    if receivables_ratio > 15:
        report_content += f"- 应收账款占比{receivables_ratio:.2f}%，需关注应收账款回收情况。\n"

    report_content += f"""

---

## 三、负债结构分析

### 3.1 负债构成

| 项目 | 金额（元） | 占总资产比例 |
|-----|-----------|------------|
| 流动负债 | {current_liabilities:,.2f} | {(current_liabilities/total_assets*100) if total_assets > 0 else 0:.2f}% |
| 非流动负债 | {non_current_liabilities:,.2f} | {(non_current_liabilities/total_assets*100) if total_assets > 0 else 0:.2f}% |
| 总负债 | {total_liabilities:,.2f} | {asset_liability_ratio:.2f}% |

### 3.2 财务杠杆评估

| 指标 | 数值 |
|-----|------|
| 资产负债率 | {asset_liability_ratio:.2f}% |
| 产权比率 | {debt_to_equity:.2f} |
| 权益乘数 | {equity_multiplier:.2f} |

"""
    with open(report_path, 'a', encoding='utf-8') as f:
        f.write(report_content)

    report_content = """
### 3.3 负债结构评价

"""

    if asset_liability_ratio < 40:
        report_content += "- 资产负债率较低，财务风险较小，但可能未充分利用财务杠杆。\n"
    elif asset_liability_ratio < 60:
        report_content += "- 资产负债率适中，财务结构较为合理。\n"
    else:
        report_content += "- 资产负债率较高，需关注偿债压力和财务风险。\n"

    if current_liabilities > non_current_liabilities:
        report_content += "- 短期债务占比较高，需关注短期偿债能力和流动性风险。\n"
    else:
        report_content += "- 长期债务占比较高，债务结构相对稳定。\n"

    report_content += f"""

---

## 四、资本结构分析

### 4.1 股东权益构成

| 项目 | 金额（元） |
|-----|-----------|
| 所有者权益总额 | {total_equity:,.2f} |
| 实收资本 | {latest_balance.get('Paid-in Capital (or Share Capital)', 0):,.2f} |
| 资本公积 | {latest_balance.get('Capital Reserve', 0):,.2f} |
| 盈余公积 | {latest_balance.get('Surplus Reserve', 0):,.2f} |
| 未分配利润 | {latest_balance.get('Retained Earnings', 0):,.2f} |

### 4.2 资本结构评价

- **产权比率**: {debt_to_equity:.2f}，反映债权人权益与股东权益的比例关系。
- **权益乘数**: {equity_multiplier:.2f}，反映总资产是股东权益的倍数。
- **净资产规模**: {total_equity/100000000:.2f}亿元。

"""

    if number > 1:
        report_content += """
---

## 五、变动趋势分析

### 5.1 总资产增长情况

"""
        if len(balance_report) >= 2:
            latest_assets = balance_report.iloc[0]['Total Assets']
            previous_assets = balance_report.iloc[1]['Total Assets']
            growth_rate = ((latest_assets - previous_assets) / previous_assets * 100) if previous_assets > 0 else 0
            
            report_content += f"- 总资产增长率: {growth_rate:.2f}%\n"
            if growth_rate > 10:
                report_content += "- 资产规模快速扩张，需关注扩张质量和效益。\n"
            elif growth_rate > 0:
                report_content += "- 资产规模稳步增长。\n"
            else:
                report_content += "- 资产规模出现收缩，需关注经营状况。\n"

    report_content += """

---

## 六、综合评价

"""
    with open(report_path, 'a', encoding='utf-8') as f:
        f.write(report_content)

    # 综合评价
    report_content = ""
    
    # 现金流健康度
    if operating_cf > 0 and operating_cf > abs(investing_cf):
        report_content += "### 6.1 现金流健康度：良好\n\n"
        report_content += "- 经营活动产生正向现金流，且能够覆盖投资支出，现金流状况健康。\n\n"
    elif operating_cf > 0:
        report_content += "### 6.1 现金流健康度：一般\n\n"
        report_content += "- 经营活动产生正向现金流，但可能需要外部融资支持投资活动。\n\n"
    else:
        report_content += "### 6.1 现金流健康度：需关注\n\n"
        report_content += "- 经营活动现金流为负，需要关注经营状况和资金链安全。\n\n"

    # 资产质量
    if current_asset_ratio > 40 and receivables_ratio < 20 and inventory_ratio < 25:
        report_content += "### 6.2 资产质量：优秀\n\n"
        report_content += "- 资产流动性好，应收账款和存货占比合理，资产质量较高。\n\n"
    else:
        report_content += "### 6.2 资产质量：一般\n\n"
        report_content += "- 需关注资产流动性和应收账款、存货的管理效率。\n\n"

    # 财务风险
    if asset_liability_ratio < 50 and current_liabilities < total_equity:
        report_content += "### 6.3 财务风险：低\n\n"
        report_content += "- 资产负债率适中，债务结构合理，财务风险较低。\n\n"
    elif asset_liability_ratio < 70:
        report_content += "### 6.3 财务风险：中等\n\n"
        report_content += "- 资产负债率处于合理区间，需持续关注偿债能力。\n\n"
    else:
        report_content += "### 6.3 财务风险：较高\n\n"
        report_content += "- 资产负债率较高，需重点关注偿债压力和财务风险。\n\n"

    report_content += """
---

**报告生成时间**: """ + pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S') + """

**数据来源**: 公司财务报表

**免责声明**: 本报告仅供参考，不构成投资建议。投资者应根据自身情况做出独立判断。
"""

    with open(report_path, 'a', encoding='utf-8') as f:
        f.write(report_content)

    print(f"Markdown报告已生成: {report_path}")
