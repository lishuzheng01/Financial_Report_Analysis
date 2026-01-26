"""
现金流质量分析测试脚本
"""
from src.report_data_cashflow_quality import cashflow_quality_analysis

# 测试股票代码
symbol = "600001"

print(f"正在生成 {symbol} 的现金流质量分析报告...")
print("=" * 60)

try:
    output_dir = cashflow_quality_analysis(symbol, number=3)
    print("\n[成功] 报告生成成功。")
    print(f"输出目录: {output_dir}")
except Exception as e:
    print(f"\n[失败] 报告生成失败: {str(e)}")
    import traceback
    traceback.print_exc()
