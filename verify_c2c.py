from hls_script import hls_evaluation, print_result
import os
import re
import argparse  # 添加argparse模块
import time

def verify_hls_code(code_str: str, top_function: str = "top", target_device: str = "xczu7ev-ffvc1156-2-e", 
                  clock_period: float = 5.0, vivado_hls_path: str = None, header_files: dict = None) -> dict:
    """
    验证HLS代码
    
    :param code_str: HLS C/C++代码字符串
    :param top_function: 顶层函数名
    :param target_device: 目标设备
    :param clock_period: 时钟周期（ns）
    :param vivado_hls_path: Vivado HLS路径
    :param header_files: 头文件字典，格式为 {"文件名": "文件内容"}
    :return: HLS评估结果
    """
    # 创建build目录
    build_dir = os.path.join(os.getcwd(), "build")
    os.makedirs(build_dir, exist_ok=True)
    
    # 如果提供了头文件，先写入头文件
    if header_files:
        for filename, content in header_files.items():
            header_path = os.path.join(build_dir, filename)
            with open(header_path, "w") as f:
                f.write(content)
    
    # 调用hls_evaluation函数进行评估
    return hls_evaluation(code_str, top_function, target_device, clock_period, vivado_hls_path)

def parse_c2c_md(file_path):
    """
    解析c2c.md文件，提取示例信息
    
    :param file_path: c2c.md文件路径
    :return: 示例列表，每个示例包含序号、Top Function、源代码和转写后代码
    """
    examples = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 使用正则表达式分割示例
        example_pattern = r'# (\d+)\s+.*?## Top Function\s+(.*?)\s+## 源代码\s+(.*?)\s+## 转写后代码\s+(.*?)(?=# \d+|\Z)'
        matches = re.findall(example_pattern, content, re.DOTALL)
        
        for match in matches:
            example_num = match[0].strip()
            top_function = match[1].strip()
            source_code = match[2].strip()
            rewritten_code = match[3].strip()
            
            examples.append({
                'number': example_num,
                'top_function': top_function,
                'source_code': source_code,
                'rewritten_code': rewritten_code
            })
        
        return examples
    
    except Exception as e:
        print(f"解析c2c.md文件时出错: {e}")
        return []

def verify_example(example, vivado_hls_path=None):
    """
    验证单个示例
    
    :param example: 示例信息字典
    :param vivado_hls_path: Vivado HLS路径
    :return: 验证结果
    """
    print(f"\n\n========== 验证示例 #{example['number']} ==========")
    print(f"Top Function: {example['top_function']}")
    
    # 准备头文件
    header_files = None
    
    # 验证源代码（期望不可综合）
    print("\n--- 验证源代码（期望不可综合）---")
    source_result = verify_hls_code(
        example['source_code'], 
        example['top_function'], 
        vivado_hls_path=vivado_hls_path,
        header_files=header_files
    )
    # 检查源代码是否不可综合
    source_synthesizable = True if "timing" in source_result and source_result["timing"] else False
    
    if not source_synthesizable:
        print("源代码验证结果: Pass (不可综合，符合预期)")
    else:
        print("源代码验证结果: Fail (可综合，不符合预期)")
    
    # 验证转写后代码（期望可综合）
    print("\n--- 验证转写后代码（期望可综合）---")
    rewritten_result = verify_hls_code(
        example['rewritten_code'], 
        example['top_function'], 
        vivado_hls_path=vivado_hls_path,
        header_files=header_files
    )
    print_result(rewritten_result)
    # 检查转写后代码是否可综合
    rewritten_synthesizable = True if "timing" in rewritten_result and rewritten_result["timing"] else False
    
    if rewritten_synthesizable:
        print("转写后代码验证结果: Pass (可综合，符合预期)")
    else:
        print("转写后代码验证结果: Fail (不可综合，不符合预期)")
    
    # 返回总体验证结果
    return {
        'number': example['number'],
        'top_function': example['top_function'],
        'source_pass': not source_synthesizable,
        'rewritten_pass': rewritten_synthesizable,
        'overall_pass': not source_synthesizable and rewritten_synthesizable
    }

def verify_all_examples(c2c_md_path, vivado_hls_path=None, start_index=1, end_index=-1):
    """
    验证c2c.md中的所有示例
    
    :param c2c_md_path: c2c.md文件路径
    :param vivado_hls_path: Vivado HLS路径
    :param start_index: 开始验证的示例索引（从1开始）
    :param end_index: 结束验证的示例索引（包含），默认为-1表示验证到最后
    :return: 验证结果列表
    """
    examples = parse_c2c_md(c2c_md_path)
    
    if not examples:
        print("未找到示例或解析失败")
        return []
    
    # 过滤示例，只保留索引在指定范围内的示例
    filtered_examples = []
    for ex in examples:
        ex_num = int(ex['number'])
        if ex_num >= start_index and (end_index == -1 or ex_num <= end_index):
            filtered_examples.append(ex)
    
    if not filtered_examples:
        print(f"没有找到索引在范围 [{start_index}, {end_index if end_index != -1 else '最后'}] 内的示例")
        return []
    
    if end_index == -1:
        print(f"找到 {len(examples)} 个示例，将验证从索引 {start_index} 开始的 {len(filtered_examples)} 个示例")
    else:
        print(f"找到 {len(examples)} 个示例，将验证索引范围在 [{start_index}, {end_index}] 内的 {len(filtered_examples)} 个示例")
    
    results = []
    for example in filtered_examples:
        result = verify_example(example, vivado_hls_path)
        results.append(result)
    
    # 打印总结
    print("\n\n========== 验证结果总结 ==========")
    all_pass = True
    for result in results:
        overall_status = "Pass" if result['overall_pass'] else "Fail"
        print(f"示例 #{result['number']} ({result['top_function']}): {overall_status}")
        if not result['overall_pass']:
            all_pass = False
    
    print(f"\n总体结果: {'Pass' if all_pass else 'Fail'}")
    
    return results

if __name__ == "__main__":
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='验证c2c.md中的HLS代码示例')
    parser.add_argument('-i', '--index', type=int, default=1, help='开始验证的示例索引（从1开始）')
    parser.add_argument('-e', '--end', type=int, default=-1, help='结束验证的示例索引（包含），默认为-1表示验证到最后')
    parser.add_argument('-p', '--path', type=str, help='Vivado HLS路径')
    parser.add_argument('-f', '--file', type=str, default="../HLS-data/c2c/c2c.md", help='c2c.md文件路径')
    args = parser.parse_args()
    
    # c2c.md文件路径
    c2c_md_path = args.file
    
    # 检查文件是否存在
    if not os.path.exists(c2c_md_path):
        print(f"错误: 找不到文件 {c2c_md_path}")
        # 尝试查找文件
        for root, dirs, files in os.walk(".."):
            for file in files:
                if file == "c2c.md":
                    c2c_md_path = os.path.join(root, file)
                    print(f"找到文件: {c2c_md_path}")
                    break
    start_time = time.time()
    # 验证指定范围内的示例
    verify_all_examples(c2c_md_path, vivado_hls_path=args.path, start_index=args.index, end_index=args.end)
    end_time = time.time()
    print(f"验证完成，用时 {round(end_time - start_time, 2)} 秒")