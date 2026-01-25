import akshare as ak
import pandas as pd
import os
import json


def get_stock_financial_data(Symbol, language="en"):
    """获取股票财务报表数据（使用新浪接口替代东方财富）

    Args:
        Symbol: 股票代码，如 '600519'
        language: 语言选项，'en' 为英文（默认），'zh' 为中文不翻译
    """
    
    StockCode = f"sh{Symbol}"
    OutputFolder = f"stock_report_data/report_data/{Symbol}"
    TranslationFolder = "stock_report_data/translater_information"
    
    if not os.path.exists(OutputFolder):
        os.makedirs(OutputFolder)
        print(f"创建文件夹: {OutputFolder}")
    
    translation_maps = {}
    if language == "en":
        translation_maps = _load_translation_maps(TranslationFolder)
    
    # 资产负债表
    print("\n正在获取资产负债表...")
    try:
        balance_sheet_df = ak.stock_financial_report_sina(stock=StockCode, symbol='资产负债表')
        if language == "en" and translation_maps:
            balance_sheet_df = _translate_dataframe(balance_sheet_df, translation_maps.get('balance', {}))
        balance_sheet_df.to_csv(f"{OutputFolder}/{Symbol}_balance_sheet.csv", index=False, encoding='utf-8-sig')
        print(f"✓ 资产负债表获取成功，形状: {balance_sheet_df.shape}")
    except Exception as e:
        print(f"✗ 资产负债表获取失败: {e}")
    
    # 利润表
    print("\n正在获取利润表...")
    try:
        income_df = ak.stock_financial_report_sina(stock=StockCode, symbol='利润表')
        if language == "en" and translation_maps:
            income_df = _translate_dataframe(income_df, translation_maps.get('profit', {}))
        income_df.to_csv(f"{OutputFolder}/{Symbol}_profit_sheet.csv", index=False, encoding='utf-8-sig')
        print(f"✓ 利润表获取成功，形状: {income_df.shape}")
    except Exception as e:
        print(f"✗ 利润表获取失败: {e}")
    
    # 现金流量表
    print("\n正在获取现金流量表...")
    try:
        cash_flow_df = ak.stock_financial_report_sina(stock=StockCode, symbol='现金流量表')
        if language == "en" and translation_maps:
            cash_flow_df = _translate_dataframe(cash_flow_df, translation_maps.get('cash_flow', {}))
        cash_flow_df.to_csv(f"{OutputFolder}/{Symbol}_cash_flow_sheet.csv", index=False, encoding='utf-8-sig')
        print(f"✓ 现金流量表获取成功，形状: {cash_flow_df.shape}")
    except Exception as e:
        print(f"✗ 现金流量表获取失败: {e}")


def _load_translation_maps(folder_path):
    """加载翻译映射文件

    Args:
        folder_path: 翻译文件所在文件夹路径

    Returns:
        dict: 包含各类报表翻译映射的字典
    """
    translation_maps = {}
    
    if not os.path.exists(folder_path):
        print(f"警告: 翻译文件夹不存在: {folder_path}")
        return translation_maps
    
    file_mapping = {
        'balance': 'translation_map_n=balance.json',
        'profit': 'translation_map_profit.json',
        'cash_flow': 'translation_map_cash_flow.json'
    }
    
    for key, filename in file_mapping.items():
        filepath = os.path.join(folder_path, filename)
        if os.path.exists(filepath):
            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    translation_maps[key] = json.load(f)
                print(f"已加载翻译文件: {filename}")
            except Exception as e:
                print(f"加载翻译文件失败 {filename}: {e}")
        else:
            print(f"翻译文件不存在: {filename}")
    
    return translation_maps


def _translate_dataframe(df, translation_map):
    """翻译 DataFrame 的列名

    Args:
        df: 要翻译的 DataFrame
        translation_map: 列名翻译映射字典

    Returns:
        DataFrame: 翻译后的 DataFrame
    """
    if not translation_map:
        return df
    
    translated_columns = {}
    for col in df.columns:
        if col in translation_map:
            translated_columns[col] = translation_map[col]
    
    if translated_columns:
        df = df.rename(columns=translated_columns)
    
    return df


if __name__ == "__main__":
    # 示例调用
    # 英文模式（默认，会翻译表头）
    get_stock_financial_data("600519", language="en")

    # 中文模式（不翻译）
    # get_stock_financial_data("600519", language="zh")
    pass
