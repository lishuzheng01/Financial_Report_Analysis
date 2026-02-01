# 财务报告分析系统
一套基于 Python 与 AkShare 的自动化财报下载、可视化与分析工具，支持生成中英文 Markdown/Word 报告，并可调用 LLM 自动撰写分析文字。

## 项目概览
- 一键抓取：使用 AkShare 从新浪财经接口下载资产负债表、利润表、现金流量表（支持多期）。  
- 描述性分析：资产结构、负债结构、资本结构、利润率、费用率、收入质量、增长趋势、现金流结构等可视化。  
- LLM 报告：根据财务与宏观数据拼装提示词，调用 OpenAI API 生成完整分析文章。  
- 多语言：报告与图片标签可切换中/英文。  
- 输出统一：Markdown 报告、图片和原始 CSV 统一存放到 `stock_report_data/` 目录。  

## 目录结构
```
Financial_Report_Analysis/
├─ src/
│  ├─ report_data_downloader.py              # 财务报表下载
│  ├─ report_data_reader.py                  # CSV 读取与预处理
│  ├─ report_data_descriptive_statistics_for_balance.py
│  ├─ report_data_descriptive_statistics_for_profit.py
│  ├─ report_data_descriptive_statistics_for_cash_flow.py
│  ├─ doc_maker_get_all_information_prompt.py # 生成 LLM 提示词
│  ├─ doc_maker_write_article.py             # 调用 LLM 写报告
│  └─ report_envirment_maker.py              # 环境与路径初始化
├─ stock_report_data/                        # 下载与分析生成物
├─ finall_stock_report/                      # LLM 文章输出
├─ config/llm_config.json                    # LLM 配置（需自建）
├─ test_*.py                                 # 单元/功能测试
└─ requirements.txt
```

## 环境要求
- Python 3.8+
- pip 可用
- OpenAI API Key（仅在生成 LLM 报告时需要）

## 安装步骤
1. 克隆或下载仓库。  
2. 安装依赖：  
   ```bash
   pip install -r requirements.txt
   ```
3. 配置 LLM（可选，用于自动写报告）：在 `config/llm_config.json` 中填入
   ```json
   {
     "api_key": "your-api-key",
     "base_url": "https://api.openai.com/v1",
     "model": "gpt-4",
     "temperature": 0.7,
     "max_tokens": 4000
   }
   ```

## 快速上手
### 1) 下载财务数据
```python
from src.report_data_downloader import get_stock_financial_data
get_stock_financial_data("600519", language="en")  # language 可选 "en" 或 "zh"
```
下载后会在 `stock_report_data/report_data/600519/` 生成三张报表的 CSV。

### 2) 生成描述性分析报告与图片
- 资产负债表：`python test_balance_analysis.py`
- 利润表：`python test_profit_analysis.py`
- 现金流量表：`python test_cashflow_quality.py`（质量）或 `python test_cash_flow_analysis.py`（描述性趋势）

生成结果（Markdown + PNG）位于 `stock_report_data/report_data/{code}/...` 子目录。

### 3) 自动写完整文章
```python
from src.doc_maker_get_all_information_prompt import get_all_information_prompt
from src.doc_maker_write_article import doc_maker_write_article

code = "600519"
prompt = get_all_information_prompt(code)
article = doc_maker_write_article(prompt, code=code, save_to_file=True)
```
文章会保存到 `finall_stock_report/`。

## 核心模块
- `report_data_downloader.py`：调用 AkShare `stock_financial_report_sina`，按代码下载三张表，支持字段翻译。  
- `report_data_reader.py`：统一读取 CSV，保证字段命名一致、日期排序。  
- `report_data_descriptive_statistics_for_balance.py`：资产/负债/资本结构及趋势图。  
- `report_data_descriptive_statistics_for_profit.py`：盈利能力、费用结构、收入质量、增长趋势。  
- `report_data_descriptive_statistics_for_cash_flow.py`：经营/投资/融资现金流对比与趋势。  
- `doc_maker_*`：组装提示词并调用 LLM 输出文章。  

## 计算说明（关键指标与公式）
> 约定：若分母为 0 则该指标记为 NA；百分比保留 2 位小数；平均值按 `(期初+期末)/2`（若需要）。金额默认单位：元。

### 1. 资产负债表分析
- 流动资产率 = `Total Current Assets / Total Assets`  
- 非流动资产率 = `Total Non-current Assets / Total Assets`  
- 应收账款占比 = `Accounts Receivable / Total Assets`  
- 存货占比 = `Inventories / Total Assets`  
- 资产负债率 = `Total Liabilities / Total Assets`  
- 债务权益比 = `Total Liabilities / Shareholders' Equity`  
- 权益乘数 = `Total Assets / Shareholders' Equity`  
- 同比变动率 = `(本期数 - 上期数) / 上期数`（用于总资产等核心科目趋势图）。  

### 2. 利润表分析
**盈利能力**
- 毛利率 = `(Operating Revenue - Operating Costs) / Operating Revenue`  
- 净利率 = `Net Profit Attributable to Parent / Total Operating Revenue`  
- 营业利润率 = `Operating Profit / Total Operating Revenue`  
- EBITDA 利润率 ≈ `(Operating Profit + 0.1 × Administrative Expenses) / Total Operating Revenue`  
  - 说明：代码中以 10% 管理费用近似折旧摊销，用于快速估算 EBITDA。  

**费用结构**
- 销售费用率 = `Selling Expenses / Total Operating Revenue`  
- 管理费用率 = `Administrative Expenses / Total Operating Revenue`  
- 研发费用率 = `R&D Expenses / Total Operating Revenue`  
- 财务费用率 = `Financial Expenses / Total Operating Revenue`  
- 期间费用率 = `(销售+管理+研发+财务费用) / Total Operating Revenue`  

**收入质量**
- 主营业务收入占比 = `Operating Revenue / Total Operating Revenue`  
- 其他业务收入占比 = `Other Business Revenue / Total Operating Revenue`  
- 投资收益占营业利润比 = `Investment Income / Operating Profit`  

**增长表现**（按报告期排序后 `pct_change()`）
- 营业收入增长率 = `Total Operating Revenue` 环比增长率  
- 净利润增长率 = `Net Profit Attributable to Parent` 环比增长率  
- 营业利润增长率 = `Operating Profit` 环比增长率  
- 毛利变动幅度 = `(Operating Revenue - Operating Costs)` 环比增长率  

### 3. 现金流量分析
- 三大活动净额：`Net Cash Flow from Operating / Investing / Financing Activities`，用于柱状对比；正负色彩区分流入流出。  
- 现金流趋势：以上三项按时间绘制折线。  
- 与资产负债表联动：结合总资产、负债、权益趋势做对比说明。  
（若需现金流质量指标，可在 `现金流质量分析方法.md` 中扩展 OCF/净利润比、自由现金流等。）  

### 4. 呈现与输出规则
- 图片统一保存在 `stock_report_data/report_data/{code}/.../*.png`，Markdown 报告在同级目录。  
- 报告头部包含一段提示：列出可用图片文件名，方便手动在 Markdown 中插入。  
- LLM 文章默认保存为 `finall_stock_report/{code}_analysis_{timestamp}.md`。  

## 常见问题
- **API Key 失效/未配置**：仅影响 LLM 写作，下载与描述性分析可正常运行。  
- **下载失败**：检查网络与股票代码；新浪接口可能存在频率限制，稍后重试。  
- **图表中文乱码**：代码已设置字体 `SimHei/Microsoft YaHei`，若仍乱码，请在本机安装相应字体。  

## 免责声明
本工具仅用于学习与研究，不构成任何投资建议。请结合实际业务与数据来源自行判断与复核。  

## 贡献
欢迎提交 Issue/PR。建议附上复现步骤和相关测试结果。  
