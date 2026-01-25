import os
import json

def get_markdown_report_information(code):
    # 配置文件路径
    target_folder = f"finall_stock_report/{code}"
    # 初始化存储结果的字典
    md_file_contents = {}
    
    # 检查文件夹是否存在
    if not os.path.exists(target_folder):
        print(f"错误：文件夹 '{target_folder}' 不存在，请检查路径！")
        return md_file_contents
    
    # 遍历文件夹下的所有文件（仅一层）
    for filename in os.listdir(target_folder):
        # 拼接文件完整相对路径
        file_path = os.path.join(target_folder, filename)
        
        # 筛选：只处理文件 + 后缀是 .md 的文件（兼容大小写）
        if os.path.isfile(file_path) and filename.lower().endswith(".md"):
            # 读取文件内容（处理异常，避免单个文件失败影响整体）
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                md_file_contents[filename] = content
                print(f"✅ 成功读取：{filename}")
            except Exception as e:
                print(f"❌ 读取 {filename} 失败：{str(e)}")
    
    return md_file_contents

def get_report_data_information(code):

    target_folder = f"finall_stock_report/{code}"
    # 初始化存储结果的字典
    cvs_data_contents = {}
    
    # 检查文件夹是否存在
    if not os.path.exists(target_folder):
        print(f"错误：文件夹 '{target_folder}' 不存在，请检查路径！")
        return cvs_data_contents
    
    # 遍历文件夹下的所有文件（仅一层）
    for filename in os.listdir(target_folder):
        # 拼接文件完整相对路径
        file_path = os.path.join(target_folder, filename)
        
        # 筛选：只处理文件 + 后缀是 .csv 的文件（兼容大小写）
        if os.path.isfile(file_path) and filename.lower().endswith(".csv"):
            # 读取文件内容（处理异常，避免单个文件失败影响整体）
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
                cvs_data_contents[filename] = content
                print(f"✅ 成功读取：{filename}")
            except Exception as e:
                print(f"❌ 读取 {filename} 失败：{str(e)}")
    
    return cvs_data_contents
    
def get_all_information_prompt(code):
    # 获取内容（假设返回的是字典）
    md_file_contents = get_markdown_report_information(code)
    csv_data_contents = get_report_data_information(code)

    # 定义标题
    report_md_header = "以下是具体的计算数据\n"
    report_data_header = "\n以下全部是具体的财报数据（三大报表）\n"

    # 处理 md_file_contents：如果是字典则转换，如果是字符串则保留
    if isinstance(md_file_contents, dict):
        # 方式 A: 转换为美化的 JSON 字符串
        md_text = json.dumps(md_file_contents, indent=4, ensure_ascii=False)
    else:
        md_text = str(md_file_contents)

    # 处理 csv_data_contents
    if isinstance(csv_data_contents, dict):
        # 方式 B: 或者手动拼接内容（适合 Prompt 展示）
        csv_text = ""
        for file_name, content in csv_data_contents.items():
            csv_text += f"\n--- 文件: {file_name} ---\n{content}\n"
    else:
        csv_text = str(csv_data_contents)

    # 最终拼接
    all_prompt = report_md_header + md_text
    # all_prompt = report_md_header + md_text + report_data_header + csv_text 如果返回全部财报内容的话，会超出模型的上下文范围，严重影响模型的性能和准确度。
    return all_prompt
