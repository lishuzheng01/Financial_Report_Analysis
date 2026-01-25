"""
Simple Article Generation System.

This module implements a basic article generation system that transforms
financial report data into comprehensive markdown articles.
"""

import os
import logging
from datetime import datetime
from typing import Optional

from openai import OpenAI

# Import config loader
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config.llm_config import load_config

# Setup logging
logger = logging.getLogger(__name__)


def doc_maker_write_article(
    prompt: str,
    code: Optional[str] = None,
    save_to_file: bool = True
) -> str:
    """
    Generate financial analysis article.

    Args:
        prompt: Full data string from get_all_information_prompt(code)
        code: Stock code for file naming (e.g., "600519")
        save_to_file: Whether to save output to file

    Returns:
        Generated article as markdown string

    Example:
        >>> from src.doc_maker_get_all_information_prompt import get_all_information_prompt
        >>> prompt = get_all_information_prompt("600519")
        >>> article = doc_maker_write_article(prompt, code="600519")
    """
    if not prompt or len(prompt) < 100:
        raise ValueError("prompt不能为空且长度应大于100字符")

    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

    logger.info("开始生成文章...")

    try:
        config = load_config()
        client = OpenAI(
            api_key=config.writer_api_key if config.writer_api_key else "dummy",
            base_url=config.writer_api_base
        )

        system_prompt = "你是一个专业的财务分析师和技术写作专家。"
        user_prompt = f"""请根据以下财务数据撰写一份综合分析报告。

数据：
{prompt}

要求：
1. 使用Markdown格式
2. 包含数据表格
3. 引用具体数字支撑分析
4. 结构清晰，逻辑连贯
5. 字数3000-5000字

请撰写完整的分析报告。"""

        response = client.chat.completions.create(
            model=config.writer_model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=config.writer_temperature,
            max_tokens=config.writer_max_tokens
        )

        article = response.choices[0].message.content
        logger.info(f"文章生成成功：{len(article)}字")

        if save_to_file and code:
            filepath = save_article_to_file(article, code)
            logger.info(f"文章已保存至: {filepath}")

        return article

    except Exception as e:
        logger.error(f"文章生成失败: {e}")
        raise RuntimeError(f"文章生成失败: {e}")


def save_article_to_file(article: str, code: str, output_dir: str = "finall_stock_report") -> str:
    """
    Save article to finall_stock_report/{code}/.

    Args:
        article: Generated markdown content
        code: Stock code
        output_dir: Base output directory

    Returns:
        Full path to saved file
    """
    target_dir = os.path.join(output_dir, code)
    os.makedirs(target_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{code}_AI生成综合分析报告_{timestamp}.md"
    filepath = os.path.join(target_dir, filename)

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(article)

    return filepath


if __name__ == "__main__":
    print("Simple Article Generation System")
    print("使用示例：")
    print("from src.doc_maker_get_all_information_prompt import get_all_information_prompt")
    print("from src.doc_maker_write_article import doc_maker_write_article")
    print("")
    print("code = '600519'")
    print("prompt = get_all_information_prompt(code)")
    print("article = doc_maker_write_article(prompt, code=code)")
