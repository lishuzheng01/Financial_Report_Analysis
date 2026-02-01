"""
测试利润表描述性统计分析功能
"""
from src.report_data_descriptive_statistics_for_profit import report_data_descriptive_statistics_for_profit

# 测试股票代码
symbol = "600519"  # 贵州茅台

# 测试单期数据
print(f"正在生成 {symbol} 的利润表描述性统计分析报告...")
print("=" * 60)

try:
    # 生成报告（分析最近3期数据）
    output_dir = report_data_descriptive_statistics_for_profit(symbol, number=3)
    print(f"\n[成功] 报告生成成功！")
    print(f"输出目录: {output_dir}")

except Exception as e:
    print(f"\n[失败] 报告生成失败: {str(e)}")
    import traceback
    traceback.print_exc()
