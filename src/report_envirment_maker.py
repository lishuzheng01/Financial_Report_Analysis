import shutil
import os
import pandas as pd

def get_all_files_recursive(code):
    """
    递归获取指定文件夹下的所有文件（包含子目录）
    :param code: 股票代码，用于构建文件夹路径
    :return: (股票代码, 包含所有文件路径的列表)
    """
    folder_path = f"stock_report_data/report_data/{code}"
    file_paths = []
    
    if not os.path.isdir(folder_path):
        print(f"错误：文件夹 {folder_path} 不存在！")
        return code, file_paths
    
    # os.walk() 会遍历所有子目录，返回 (当前目录, 子目录列表, 文件列表)
    for root, dirs, files in os.walk(folder_path):
        for file in files:
            # 拼接完整路径
            full_path = os.path.join(root, file)
            file_paths.append(os.path.abspath(full_path))
    
    return code, file_paths

def report_envirment_maker(code, source_file):
    target_dir = f"finall_stock_report/{code}"
    
    # 先确保目标目录存在，不存在则创建
    os.makedirs(target_dir, exist_ok=True)
    
    # 复制文件到目标目录（保留原文件名）
    shutil.copy2(source_file, target_dir)

def report_data_maker(code,number):

    balance_file_sheet_path = f"finall_stock_report/{code}/{code}_balance_sheet.csv"
    cash_flow_sheet_path = f"finall_stock_report/{code}/{code}_cash_flow_sheet.csv"
    prpfit_sheet_path = f"finall_stock_report/{code}/{code}_profit_sheet.csv"

    balance_file_sheet = pd.read_csv(balance_file_sheet_path, nrows=number)
    cash_flow_sheet = pd.read_csv(cash_flow_sheet_path, nrows=number)
    prpfit_sheet = pd.read_csv(prpfit_sheet_path, nrows=number)

    balance_file_sheet.to_csv(balance_file_sheet_path, index=False)
    cash_flow_sheet.to_csv(cash_flow_sheet_path, index=False)
    prpfit_sheet.to_csv(prpfit_sheet_path, index=False)

def finall_report_envirment_maker(code,number):
    code, file_paths = get_all_files_recursive(code)
    for source_file in file_paths:
        report_envirment_maker(code, source_file)
        report_data_maker(code,number)

