
# 财务报告分析系统

一个基于 Python 的自动化财务报告分析与中文股票研究文章生成系统。

## 项目概述

本项目提供以下功能：

* 使用 AkShare 从中国股票市场下载财务数据
* 分析资产负债表、利润表和现金流量表
* 使用 AI 自动生成全面的财务分析报告
* 支持将报告导出为 Markdown 和文档格式

## 功能特性

* **数据采集**：从新浪财经自动下载上市公司财务报表
* **多语言支持**：支持中英文
* **统计分析**：对关键财务指标进行描述性统计分析
* **AI 智能报告**：通过 OpenAI API 生成详细的财务分析文章
* **灵活输出**：支持将报告保存为 Markdown 或 Word 文档

## 项目结构

```
Financial_Report_Analysis/
├── src/                                    # 源代码
│   ├── report_data_downloader.py          # 财务数据下载
│   ├── report_data_reader.py              # 数据读取与处理
│   ├── report_data_descriptive_statistics_for_balance.py
│   ├── report_data_descriptive_statistics_for_profit.py
│   ├── report_data_descriptive_statistics_for_cash_flow.py
│   ├── doc_maker_get_all_information_prompt.py
│   ├── doc_maker_write_article.py         # 生成分析文章
│   └── report_envirment_maker.py          # 环境配置
├── config/                                 # 配置文件
├── stock_report_data/                      # 下载的数据存储目录
├── finall_stock_report/                    # 生成的分析报告
├── test_*.py                               # 测试脚本
├── requirements.txt                        # Python 依赖
└── readme.md                               # 本说明文件
```

## 安装说明

### 前置条件

* Python 3.8 或更高版本
* pip 包管理工具
* OpenAI API Key（用于文章生成）

### 安装步骤

1. 克隆或下载本项目仓库

2. 安装依赖：

```bash
pip install -r requirements.txt
```

3. 配置 API：

   * 在 `config/` 目录下创建 `llm_config.json`
   * 示例配置如下：

```json
{
    "api_key": "your-api-key-here",
    "base_url": "https://api.openai.com/v1",
    "model": "gpt-4"
}
```

## 使用方法

### 1. 下载财务数据

```python
from src.report_data_downloader import get_stock_financial_data

# 下载指定股票的财务数据（例如：贵州茅台 - 600519）
get_stock_financial_data("600519", language="en")
```

### 2. 生成分析报告

```python
from src.doc_maker_get_all_information_prompt import get_all_information_prompt
from src.doc_maker_write_article import doc_maker_write_article

# 获取股票相关信息
code = "600519"
prompt = get_all_information_prompt(code)

# 生成分析文章
article = doc_maker_write_article(prompt, code=code, save_to_file=True)
print(article)
```

### 3. 运行测试

测试各个模块功能：

```bash
# 测试文章生成
python test_article_generation.py

# 测试资产负债表分析
python test_balance_analysis.py

# 测试利润表分析
python test_profit_analysis.py

# 测试现金流量表分析
python test_cash_flow_analysis.py
```

## 核心模块说明

### 数据下载模块

* **模块名**：`src/report_data_downloader.py`
* 下载资产负债表、利润表和现金流量表
* 支持中英文翻译
* 数据来源：通过 AkShare 接入新浪财经

### 数据读取模块

* **模块名**：`src/report_data_reader.py`
* 读取 CSV 格式的财务数据
* 对数据进行清洗与格式化处理

### 描述性统计分析

* **模块**：

  * `src/report_data_descriptive_statistics_for_balance.py`
  * `src/report_data_descriptive_statistics_for_profit.py`
  * `src/report_data_descriptive_statistics_for_cash_flow.py`
* 计算关键财务指标的描述性统计
* 识别财务趋势与变化模式

### 文章生成模块

* **模块名**：`src/doc_maker_write_article.py`
* 使用 OpenAI API 自动生成财务分析文章
* 默认输出为 Markdown 格式
* 文件保存至 `finall_stock_report/` 目录

## 配置说明

### 大模型（LLM）配置

在 `config/llm_config.json` 中填写如下内容：

```json
{
    "api_key": "your-openai-api-key",
    "base_url": "https://api.openai.com/v1",
    "model": "gpt-4",
    "temperature": 0.7,
    "max_tokens": 4000
}
```

### 股票代码格式

* 上海证券交易所：6 位数字代码（如 “600519” 表示贵州茅台）
* 深圳证券交易所：6 位数字代码（如 “000001” 表示平安银行）

## 输出结果

生成的分析报告将保存至：

* **Markdown 文件**：`finall_stock_report/{stock_code}_analysis_{timestamp}.md`
* **原始数据文件**：`stock_report_data/report_data/{stock_code}/`

## 项目依赖

主要依赖库包括：

* **akshare**：中国股票市场数据接口
* **pandas**：数据处理与分析
* **openai**：AI 文章生成
* **python-docx**：文档生成
* **matplotlib**：数据可视化

完整依赖列表请参考 [requirements.txt](requirements.txt)。

## 常见问题排查

### 常见问题

1. **API Key 错误**

   * 确认 `config/llm_config.json` 文件存在且 API Key 有效
   * 检查 API Key 的权限与调用额度

2. **数据下载失败**

   * 检查网络连接
   * 确认股票代码是否正确
   * AkShare 可能存在访问频率限制

3. **模块导入错误**

   * 执行 `pip install -r requirements.txt`
   * 确认 Python 版本为 3.8 及以上

## 示例工作流程

完整示例流程如下：

```python
# 第一步：下载财务数据
from src.report_data_downloader import get_stock_financial_data
get_stock_financial_data("600519", language="en")

# 第二步：生成分析报告
from src.doc_maker_get_all_information_prompt import get_all_information_prompt
from src.doc_maker_write_article import doc_maker_write_article

prompt = get_all_information_prompt("600519")
article = doc_maker_write_article(prompt, code="600519", save_to_file=True)

print("报告生成成功！")
```

## 许可证

本项目仅用于教育与研究目的。

## 贡献指南

欢迎提交贡献，请确保代码风格统一，并包含相应测试。

## 联系方式

如有问题或建议，请在项目仓库中提交 Issue。

---

