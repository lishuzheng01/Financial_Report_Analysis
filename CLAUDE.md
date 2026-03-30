# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

A Python-based automated financial report analysis system using AkShare to download financial data from Sina Finance, generate descriptive statistics, visualizations, and optionally use LLM to write analysis articles.

## Common Commands

```bash
# Install dependencies
pip install -r requirements.txt

# Download financial data for a stock
python -c "from src.report_data_downloader import get_stock_financial_data; get_stock_financial_data('600519', language='en')"

# Run tests
python test/test_balance_analysis.py
python test/test_profit_analysis.py
python test/test_cashflow_quality.py
python test/test_cash_flow_analysis.py
python test/test_dupont_analysis.py
python test/test_ratio_analysis.py
python test/test_struct_anomaly.py
python test/test_macroeconomic_data_get_all.py
python test/test_article_generation.py
```

## Architecture

- **src/report_data_downloader.py**: Downloads balance sheet, income statement, and cash flow from Sina Finance via AkShare
- **src/report_data_reader.py**: Unified CSV reader with consistent field naming and date sorting
- **src/report_data_descriptive_statistics_for_*.py**: Three modules for balance sheet, profit, and cash flow analysis with visualizations
- **src/report_data_ratio_analysis.py**: Financial ratio calculations (profitability, liquidity, leverage)
- **src/report_data_dupont_analysis.py**: DuPont analysis decomposition
- **src/report_data_cashflow_quality.py**: Cash flow quality assessment
- **src/report_data_struct_anomaly.py**: Structural anomaly detection
- **src/doc_maker_*.py**: LLM prompt generation and article writing
- **config/llm_config.yaml**: LLM configuration (API key, model, etc.)

## Key Conventions

- Stock code is passed as string (e.g., "600519")
- Language parameter: "en" or "zh" for bilingual support
- Output directory: `stock_report_data/report_data/{code}/`
- LLM articles saved to: `finall_stock_report/`
- Financial metrics use specific formulas documented in readme.md