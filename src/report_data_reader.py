import pandas as pd

def report_data_reader(Symbol, number=None):
    '''
    读取股票财务报表数据
    
    Args:
        Symbol: 股票代码，如 '600519'
        number: 要读取的期数，从最新一期开始往后数，默认为1（只取最新一期）
                例如：number=3 表示读取最新一期、第二期、第三期，共3期数据
        
    Returns:
        tuple: balance_report、profit_report、cash_flow_report的DataFrame
    '''
    if number is None:
        number = 1
    # 配置文件路径
    balance_report_file_path = f"stock_report_data/report_data/{Symbol}/{Symbol}_balance_sheet.csv"
    profit_report_file_path = f"stock_report_data/report_data/{Symbol}/{Symbol}_profit_sheet.csv"
    cash_flow_report_file_path = f"stock_report_data/report_data/{Symbol}/{Symbol}_cash_flow_sheet.csv"
    
    # 读取指定期数的财报，第一行为最新一期
    balance_report_df = pd.read_csv(balance_report_file_path, nrows=number)
    profit_report_df = pd.read_csv(profit_report_file_path, nrows=number)
    cash_flow_report_df = pd.read_csv(cash_flow_report_file_path, nrows=number)
    
    return balance_report_df, profit_report_df, cash_flow_report_df
