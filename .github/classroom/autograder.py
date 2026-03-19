import os
import glob
import re

def find_result_file():
    files = glob.glob("output/lab1_report_*.md")
    return files[0] if files else None

def extract_id_name_from_filename(filename):
    match = re.match(r"output/lab1_report_(\d+)_([^.]+)\.md", filename)
    if match:
        return match.group(1), match.group(2)
    return None, None

def check_sanity_pass(md_path):
    with open(md_path, encoding="utf-8") as f:
        content = f.read()
    return ("Sanity checks" in content and "PASS" in content)

def check_custom_block(md_path, task_title):
    with open(md_path, encoding="utf-8") as f:
        content = f.read()
    # 精确定位到 ### 任务标题
    pattern = rf"### {re.escape(task_title)}\s*\n([\s\S]*?)(?=\n### |\Z)"
    match = re.search(pattern, content)
    if not match:
        return False
    block = match.group(1).strip()
    # 检查是否有非默认内容
    for line in block.splitlines():
        l = line.strip()
        if l and not l.startswith("（请在此处补充") and not l.startswith("(请在此处补充"):
            return True
    return False

def extract_N_from_md(md_path):
    import re
    with open(md_path, encoding="utf-8") as f:
        content = f.read()
    match = re.search(r"循环次数：N\s*=\s*(\d+)", content)
    if match:
        return int(match.group(1))
    return None

def main():
    result_file = find_result_file()
    if not result_file:
        print("Autograding: ❌ 未生成结果文件")
        exit(1)
    student_id, student_name = extract_id_name_from_filename(result_file)
    print(f"检测到学号: {student_id}, 姓名: {student_name}")
    N = extract_N_from_md(result_file)
    print(f"检测到循环次数 N = {N}")
    if not check_sanity_pass(result_file):
        print("Autograding: ❌ Sanity check 未通过")
        exit(1)
    if not check_custom_block(result_file, "任务1：建模与公式"):
        print("Autograding: ❌ 任务1（建模与公式）未填写")
        exit(1)
    if not check_custom_block(result_file, "任务3：工程解释与改进建议"):
        print("Autograding: ❌ 任务3（工程解释与改进建议）未填写")
        exit(1)
    print("Autograding: ✅ 所有检查通过")
    exit(0)

if __name__ == "__main__":
    main()