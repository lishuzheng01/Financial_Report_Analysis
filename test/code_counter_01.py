import os

EXCLUDE_DIRS = {
    ".git", "__pycache__", ".venv", "venv",
    "node_modules", "dist", "build"
}

def count_code_stats(root_dir="."):
    total_lines = 0
    total_chars = 0
    file_count = 0

    for root, dirs, files in os.walk(root_dir):
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]

        for file in files:
            if file.endswith(".py"):
                path = os.path.join(root, file)
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        text = f.read()
                        total_lines += text.count("\n") + 1 if text else 0
                        total_chars += len(text)
                        file_count += 1
                except Exception as e:
                    print(f"⚠️ 跳过 {path}: {e}")

    print("=" * 40)
    print("📊 项目 Python 代码统计")
    print(f"📁 文件数: {file_count}")
    print(f"📏 行数: {total_lines}")
    print(f"🔢 字符数: {total_chars}")
    print("=" * 40)

if __name__ == "__main__":
    count_code_stats()
