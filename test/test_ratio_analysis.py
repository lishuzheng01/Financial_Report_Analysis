"""
Test script for ratio analysis report generation.
"""
from src.report_data_ratio_analysis import report_data_ratio_analysis

# Test stock code
symbol = "600001"

print(f"Generating ratio analysis report for {symbol} ...")
print("=" * 60)

try:
    output_dir = report_data_ratio_analysis(symbol, number=3)
    print("\nReport generated successfully.")
    print(f"Output directory: {output_dir}")
except Exception as e:
    print(f"\nReport generation failed: {str(e)}")
    import traceback
    traceback.print_exc()
