#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
代码统计工具
统计指定目录下的文件总行数、总字符数，并可选择性区分代码行、空行和注释行。
"""

import os
import sys

# --- 配置区 ---
# 要统计的文件扩展名（可根据需要增删）
CODE_EXTENSIONS = {
    '.py', '.js', '.java', '.c', '.cpp', '.h', '.hpp',
    '.cs', '.php', '.html', '.css', '.sql', '.go', '.rs','.json','csv'
}
# 是否详细模式：打印每个文件的信息
VERBOSE = False
# 是否排除常见的忽略目录（如venv, .git等）
EXCLUDE_DIRS = {'.git', '__pycache__', 'venv', 'env', '.idea', 'node_modules', 'build', 'dist'}


def count_lines_and_chars(file_path):
    """
    统计单个文件的行数和字符数
    """
    encodings_to_try = ('utf-8', 'gbk')
    f = None
    for enc in encodings_to_try:
        try:
            f = open(file_path, 'r', encoding=enc, errors='ignore')
            break
        except Exception:
            f = None
            continue
    if f is None:
        print(f"警告：无法读取文件 {file_path}")
        return 0, 0, 0, 0, 0

    total_lines = 0
    total_chars = 0
    code_lines = 0
    blank_lines = 0
    comment_lines = 0

    # 简单的启发式规则判断注释 (可以根据需要扩展)
    # 注意：这只是非常基础的判断，复杂的注释（如多行字符串当注释）可能无法准确识别
    single_line_comment_prefixes = ['#', '//', '--', '/*']  # 可以根据语言添加

    try:
        for line in f:
            total_lines += 1
            total_chars += len(line)

            stripped_line = line.strip()
            if not stripped_line:
                blank_lines += 1
                continue

            if any(stripped_line.startswith(prefix) for prefix in single_line_comment_prefixes):
                comment_lines += 1
            else:
                code_lines += 1
    finally:
        f.close()

    return total_lines, total_chars, code_lines, blank_lines, comment_lines


def main():
    """
    主函数
    """
    # 如果没有传入路径，则使用当前目录
    target_dir = sys.argv[1] if len(sys.argv) > 1 else '.'

    if not os.path.isdir(target_dir):
        print(f"错误：指定的路径 '{target_dir}' 不是一个有效的目录。")
        sys.exit(1)

    print(f"正在统计目录: {os.path.abspath(target_dir)}")
    print("-" * 50)

    grand_total_files = 0
    grand_total_lines = 0
    grand_total_chars = 0
    grand_code_lines = 0
    grand_blank_lines = 0
    grand_comment_lines = 0

    # 先收集目标文件列表，便于展示进度与总数
    target_files = []
    for root, dirs, files in os.walk(target_dir):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        for file in files:
            file_ext = os.path.splitext(file)[1].lower()
            if file_ext in CODE_EXTENSIONS:
                target_files.append(os.path.join(root, file))

    total_files = len(target_files)

    # 遍历并统计，同时展示进度
    for idx, file_path in enumerate(target_files, start=1):
        lines, chars, code_l, blank_l, comment_l = count_lines_and_chars(file_path)

        grand_total_files += 1
        grand_total_lines += lines
        grand_total_chars += chars
        grand_code_lines += code_l
        grand_blank_lines += blank_l
        grand_comment_lines += comment_l

        rel_path = os.path.relpath(file_path, target_dir)
        if VERBOSE:
            print(f"第{idx}/{total_files}个 {rel_path} | 行: {lines:>6} | 字符: {chars:>8} | 代码: {code_l:>5} | 空行: {blank_l:>4} | 注释: {comment_l:>4}")
        else:
            print(f"第{idx}/{total_files}个 {rel_path}")

    # 打印总计
    print("-" * 50)
    print("汇总统计:")
    print(f"扫描到的代码文件总数: {grand_total_files}")
    print(f"所有文件总行数: {grand_total_lines}")
    print(f"所有文件总字符数: {grand_total_chars}")
    print(f"其中 - 代码行数: {grand_code_lines}")
    print(f"      - 空行数: {grand_blank_lines}")
    print(f"      - 注释行数: {grand_comment_lines}")


if __name__ == "__main__":
    main()
