import re
import random
import os
import argparse
from typing import List, Dict, Tuple, Optional

# 污染策略类型
POLLUTION_TYPES = ["system_call", "dynamic_memory", "stl", "exception"]

def parse_src_md(file_path: str) -> List[Dict]:
    """
    解析src.md文件，提取可综合代码
    
    :param file_path: src.md文件路径
    :return: 代码示例列表，每个示例包含索引、顶层函数和源代码
    """
    examples = []
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # 使用正则表达式分割示例
        example_pattern = r'# (\d+)\s+# ([^\n]+)\s+(.*?)(?=# \d+|\Z)'
        matches = re.findall(example_pattern, content, re.DOTALL)
        
        for match in matches:
            example_num = match[0].strip()
            top_function = match[1].strip()
            source_code = match[2].strip()
            
            examples.append({
                'number': example_num,
                'top_function': top_function,
                'source_code': source_code
            })
        
        return examples
    
    except Exception as e:
        print(f"解析src.md文件时出错: {e}")
        return []

def apply_system_call_pollution(code: str) -> Tuple[str, Dict]:
    """
    应用系统调用污染
    
    :param code: 原始代码
    :return: 污染后的代码和污染信息
    """
    # 查找主函数或顶层函数的开始位置
    function_pattern = r'void\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\([^)]*\)\s*{'
    match = re.search(function_pattern, code)
    
    if not match:
        return code, {"success": False, "message": "找不到合适的函数进行污染"}
    
    function_start = match.start()
    function_name = match.group(1)
    
    # 在函数开始处插入系统调用
    system_call = """
    // 添加系统调用（不可综合）
    FILE *log_file = fopen("log.txt", "w");
    fprintf(log_file, "Function %s called\\n", __func__);
    fclose(log_file);
    """
    
    # 找到函数体的开始位置（第一个{之后）
    body_start = code.find('{', function_start) + 1
    
    # 插入系统调用
    polluted_code = code[:body_start] + system_call + code[body_start:]
    
    return polluted_code, {
        "success": True, 
        "pollution_type": "system_call",
        "function_name": function_name,
        "position": body_start
    }

def apply_dynamic_memory_pollution(code: str) -> Tuple[str, Dict]:
    """
    应用动态内存污染
    
    :param code: 原始代码
    :return: 污染后的代码和污染信息
    """
    # 查找主函数或顶层函数的开始位置
    function_pattern = r'void\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\([^)]*\)\s*{'
    match = re.search(function_pattern, code)
    
    if not match:
        return code, {"success": False, "message": "找不到合适的函数进行污染"}
    
    function_start = match.start()
    function_name = match.group(1)
    
    # 在函数开始处插入动态内存分配
    dynamic_memory = """
    // 添加动态内存分配（不可综合）
    int dynamic_size = 100;
    float* dynamic_array = (float*)malloc(dynamic_size * sizeof(float));
    
    // 初始化动态数组
    for(int i = 0; i < dynamic_size; i++) {
        dynamic_array[i] = (float)i;
    }
    
    // 使用动态数组
    float dynamic_sum = 0;
    for(int i = 0; i < dynamic_size; i++) {
        dynamic_sum += dynamic_array[i];
    }
    
    // 释放内存
    free(dynamic_array);
    """
    
    # 找到函数体的开始位置（第一个{之后）
    body_start = code.find('{', function_start) + 1
    
    # 插入动态内存分配
    polluted_code = code[:body_start] + dynamic_memory + code[body_start:]
    
    # 添加头文件
    if "#include <stdlib.h>" not in code:
        polluted_code = "#include <stdlib.h>\n" + polluted_code
    
    return polluted_code, {
        "success": True, 
        "pollution_type": "dynamic_memory",
        "function_name": function_name,
        "position": body_start
    }

def apply_stl_pollution(code: str) -> Tuple[str, Dict]:
    """
    应用STL污染
    
    :param code: 原始代码
    :return: 污染后的代码和污染信息
    """
    # 查找主函数或顶层函数的开始位置
    function_pattern = r'void\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\([^)]*\)\s*{'
    match = re.search(function_pattern, code)
    
    if not match:
        return code, {"success": False, "message": "找不到合适的函数进行污染"}
    
    function_start = match.start()
    function_name = match.group(1)
    
    # 在函数开始处插入STL使用
    stl_code = """
    // 添加STL使用（不可综合）
    std::vector<float> vec;
    for(int i = 0; i < 100; i++) {
        vec.push_back((float)i);
    }
    
    // 使用STL算法
    std::sort(vec.begin(), vec.end());
    
    // 计算总和
    float sum = 0;
    for(auto val : vec) {
        sum += val;
    }
    """
    
    # 找到函数体的开始位置（第一个{之后）
    body_start = code.find('{', function_start) + 1
    
    # 插入STL使用
    polluted_code = code[:body_start] + stl_code + code[body_start:]
    
    # 添加头文件
    if "#include <vector>" not in code:
        polluted_code = "#include <vector>\n" + polluted_code
    if "#include <algorithm>" not in code:
        polluted_code = "#include <algorithm>\n" + polluted_code
    
    return polluted_code, {
        "success": True, 
        "pollution_type": "stl",
        "function_name": function_name,
        "position": body_start
    }

def apply_exception_pollution(code: str) -> Tuple[str, Dict]:
    """
    应用异常处理污染
    
    :param code: 原始代码
    :return: 污染后的代码和污染信息
    """
    # 查找主函数或顶层函数的开始位置
    function_pattern = r'void\s+([a-zA-Z_][a-zA-Z0-9_]*)\s*\([^)]*\)\s*{'
    match = re.search(function_pattern, code)
    
    if not match:
        return code, {"success": False, "message": "找不到合适的函数进行污染"}
    
    function_start = match.start()
    function_name = match.group(1)
    
    # 在函数开始处插入异常处理
    exception_code = """
    // 添加异常处理（不可综合）
    try {
        float a = 10.0f;
        float b = 0.0f;
        
        if(b == 0.0f) {
            throw std::runtime_error("Division by zero");
        }
        
        float result = a / b;
    } catch(const std::exception& e) {
        // 处理异常
    }
    """
    
    # 找到函数体的开始位置（第一个{之后）
    body_start = code.find('{', function_start) + 1
    
    # 插入异常处理
    polluted_code = code[:body_start] + exception_code + code[body_start:]
    
    # 添加头文件
    if "#include <stdexcept>" not in code:
        polluted_code = "#include <stdexcept>\n" + polluted_code
    
    return polluted_code, {
        "success": True, 
        "pollution_type": "exception",
        "function_name": function_name,
        "position": body_start
    }

def generate_fix(polluted_code: str, pollution_info: Dict) -> str:
    """
    根据污染信息生成修复代码
    
    :param polluted_code: 污染后的代码
    :param pollution_info: 污染信息
    :return: 修复后的代码
    """
    if not pollution_info["success"]:
        return polluted_code
    
    pollution_type = pollution_info["pollution_type"]
    
    if pollution_type == "system_call":
        # 使用__SYNTHESIS__宏排除系统调用
        fixed_code = polluted_code.replace(
            "// 添加系统调用（不可综合）",
            "#ifndef __SYNTHESIS__\n    // 添加系统调用（不可综合）"
        )
        fixed_code = fixed_code.replace(
            "fclose(log_file);",
            "fclose(log_file);\n#endif"
        )
        
    elif pollution_type == "dynamic_memory":
        # 使用固定大小的资源替代动态内存
        fixed_code = polluted_code.replace(
            "// 添加动态内存分配（不可综合）\n    int dynamic_size = 100;\n    float* dynamic_array = (float*)malloc(dynamic_size * sizeof(float));",
            """// 使用固定大小的资源替代动态内存
#ifdef NO_SYNTH
    int dynamic_size = 100;
    float* dynamic_array = (float*)malloc(dynamic_size * sizeof(float));
#else
    int dynamic_size = 100;
    float _dynamic_array[100];
    float* dynamic_array = _dynamic_array;
#endif"""
        )
        
        fixed_code = fixed_code.replace(
            "// 释放内存\n    free(dynamic_array);",
            """// 释放内存
#ifdef NO_SYNTH
    free(dynamic_array);
#endif"""
        )
        
    elif pollution_type == "stl":
        # 使用固定大小的数组替代STL
        fixed_code = polluted_code.replace(
            """// 添加STL使用（不可综合）
    std::vector<float> vec;
    for(int i = 0; i < 100; i++) {
        vec.push_back((float)i);
    }
    
    // 使用STL算法
    std::sort(vec.begin(), vec.end());
    
    // 计算总和
    float sum = 0;
    for(auto val : vec) {
        sum += val;
    }""",
            """// 使用固定大小的数组替代STL
    float vec[100];
    int vec_size = 0;
    
    // 填充数组
    for(int i = 0; i < 100; i++) {
        vec[vec_size++] = (float)i;
    }
    
    // 使用冒泡排序替代std::sort
    for(int i = 0; i < vec_size - 1; i++) {
        for(int j = 0; j < vec_size - i - 1; j++) {
            if(vec[j] > vec[j+1]) {
                float temp = vec[j];
                vec[j] = vec[j+1];
                vec[j+1] = temp;
            }
        }
    }
    
    // 计算总和
    float sum = 0;
    for(int i = 0; i < vec_size; i++) {
        sum += vec[i];
    }"""
        )
        
    elif pollution_type == "exception":
        # 使用条件检查替代异常处理
        fixed_code = polluted_code.replace(
            """// 添加异常处理（不可综合）
    try {
        float a = 10.0f;
        float b = 0.0f;
        
        if(b == 0.0f) {
            throw std::runtime_error("Division by zero");
        }
        
        float result = a / b;
    } catch(const std::exception& e) {
        // 处理异常
    }""",
            """// 使用条件检查替代异常处理
    float a = 10.0f;
    float b = 0.0f;
    
    if(b == 0.0f) {
        // 处理错误情况
    } else {
        float result = a / b;
    }"""
        )
    
    else:
        fixed_code = polluted_code
    
    return fixed_code

def apply_pollution(code: str, pollution_type: str) -> Tuple[str, Dict]:
    """
    应用指定类型的污染
    
    :param code: 原始代码
    :param pollution_type: 污染类型
    :return: 污染后的代码和污染信息
    """
    if pollution_type == "system_call":
        return apply_system_call_pollution(code)
    elif pollution_type == "dynamic_memory":
        return apply_dynamic_memory_pollution(code)
    elif pollution_type == "stl":
        return apply_stl_pollution(code)
    elif pollution_type == "exception":
        return apply_exception_pollution(code)
    else:
        return code, {"success": False, "message": f"未知的污染类型: {pollution_type}"}

def generate_c2c_md_entry(number: int, top_function: str, source_code: str, fixed_code: str, pollution_type: str) -> str:
    """
    生成c2c.md格式的条目
    
    :param number: 示例编号
    :param top_function: 顶层函数名
    :param source_code: 源代码（污染后的代码）
    :param fixed_code: 修复后的代码
    :param pollution_type: 污染类型
    :return: c2c.md格式的条目
    """
    # 根据污染类型确定大类和子类
    category = "不受支持的C/C++构造"
    
    if pollution_type == "system_call":
        subcategory = "系统调用"
        transform_rule = "使用 `__SYNTHESIS__`宏，从设计中排除不可综合的代码。"
    elif pollution_type == "dynamic_memory":
        subcategory = "动态存储器使用"
        transform_rule = "创建固定大小的资源，并将现有指针直接设置为指向此固定大小的资源。"
    elif pollution_type == "stl":
        subcategory = "标准模板库"
        transform_rule = "创建局部函数，该函数具有相同功能但不呈现递归、动态存储器分配或动态创建和解构对象特征。"
    elif pollution_type == "exception":
        subcategory = "异常处理"
        transform_rule = "用返回值或状态寄存器替代 `try/catch`，避免硬件无法实现的异常机制。"
    else:
        subcategory = "未知"
        transform_rule = "未知"
    
    # 生成c2c.md格式的条目
    entry = f"""# {number}

## 大类

{category}

## 子类

{subcategory}

## 转写规则

{transform_rule}

## Top Function

{top_function}

## 源代码

{source_code}

## 转写后代码

{fixed_code}
"""
    
    return entry

def augment_dataset(src_md_path: str, output_path: str, num_samples: int = 10):
    """
    扩充数据集
    
    :param src_md_path: 源文件路径
    :param output_path: 输出文件路径
    :param num_samples: 要生成的样本数量
    """
    # 解析源文件
    examples = parse_src_md(src_md_path)
    
    if not examples:
        print("未找到示例或解析失败")
        return
    
    print(f"找到 {len(examples)} 个示例")
    
    # 读取现有的c2c.md文件，确定起始编号
    try:
        with open(output_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # 查找最后一个示例的编号
        last_example_pattern = r'# (\d+)\s+'
        matches = re.findall(last_example_pattern, content)
        
        if matches:
            start_number = int(matches[-1]) + 1
        else:
            start_number = 1
            
    except FileNotFoundError:
        # 文件不存在，从1开始
        start_number = 1
        content = ""
    
    # 生成新样本
    new_entries = []
    
    for i in range(num_samples):
        # 随机选择一个示例
        example = random.choice(examples)
        
        # 随机选择一种污染类型
        pollution_type = random.choice(POLLUTION_TYPES)
        
        # 应用污染
        polluted_code, pollution_info = apply_pollution(example['source_code'], pollution_type)
        
        if not pollution_info["success"]:
            print(f"示例 {example['number']} 污染失败: {pollution_info['message']}")
            continue
        
        # 生成修复代码
        fixed_code = generate_fix(polluted_code, pollution_info)
        
        # 生成c2c.md条目
        entry = generate_c2c_md_entry(
            start_number + i,
            example['top_function'],
            polluted_code,
            fixed_code,
            pollution_type
        )
        
        new_entries.append(entry)
        print(f"生成示例 #{start_number + i} ({pollution_type})")
    
    # 写入文件
    with open(output_path, 'a', encoding='utf-8') as f:
        for entry in new_entries:
            f.write(entry + "\n")
    
    print(f"成功生成 {len(new_entries)} 个新示例，写入 {output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='HLS代码数据集逆向增强工具')
    parser.add_argument('-s', '--src', type=str, default="../HLS-data/c2c/src.md", help='源文件路径')
    parser.add_argument('-o', '--output', type=str, default="../HLS-data/c2c/c2c.md", help='输出文件路径')
    parser.add_argument('-n', '--num', type=int, default=50, help='要生成的样本数量')
    args = parser.parse_args()
    
    augment_dataset(args.src, args.output, args.num)
