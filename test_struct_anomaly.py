"""
Simple smoke test for structured anomaly detection report.
"""
from src.report_data_struct_anomaly import struct_anomaly_analysis


symbol = "600519"  # sample stock code; adjust as needed

print(f"Generating structured anomaly report for {symbol} ...")
print("=" * 60)

try:
    output_dir = struct_anomaly_analysis(symbol, number=4)
    print("\n✓ Report generated successfully.")
    print(f"Output directory: {output_dir}")
except Exception as e:
    print("\n✗ Report generation failed:")
    print(str(e))
    import traceback

    traceback.print_exc()
