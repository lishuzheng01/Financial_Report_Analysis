"""
Test script for simplified article generation system.
"""

import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from src.doc_maker_get_all_information_prompt import get_all_information_prompt
from src.doc_maker_write_article import doc_maker_write_article


def test_article_generation():
    """Test basic article generation."""
    print("=" * 60)
    print("测试文章生成系统")
    print("=" * 60)

    # Test stock code
    code = "600519"
    print(f"\n正在测试股票代码: {code}")

    try:
        # Step 1: Get all information
        print("\n步骤 1: 获取股票信息...")
        prompt = get_all_information_prompt(code)
        print(f"✓ 成功获取信息，数据长度: {len(prompt)} 字符")

        # Step 2: Generate article
        print("\n步骤 2: 生成分析报告...")
        article = doc_maker_write_article(prompt, code=code, save_to_file=True)
        print(f"✓ 成功生成报告，文章长度: {len(article)} 字符")

        # Display preview
        print("\n" + "=" * 60)
        print("文章预览（前500字符）:")
        print("=" * 60)
        print(article[:500])
        print("...")

        print("\n" + "=" * 60)
        print("✓ 测试成功完成！")
        print("=" * 60)

    except Exception as e:
        print(f"\n✗ 测试失败: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_article_generation()
