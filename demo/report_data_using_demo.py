import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.report_data_reader import report_data_reader
import pandas as pd

Symbol = "600519"

balance_report,profit_report,cash_flow_report = report_data_reader(Symbol)
print("资产负债表最新数据:")
print(balance_report)
print("\n利润表最新数据:")
print(profit_report)
print("\n现金流量表最新数据:")
print(cash_flow_report)




