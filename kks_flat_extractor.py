import re
import os

# ================= 1. 定义规则库 =================
# 保持不变
RULES_PIPES = [
    (1, 190, "主管道 (Main Pipes)"),
    (191, 199, "安全阀的吸入与泄压管道 (Suction and Pressure Relief on Safety Valves)"),
    (201, 299, "未使用 (Not Used)"),
    (301, 399, "测量用压力管线 (Pressure Lines for Measurement)"),
    (401, 499, "排放管 (Drain Pipes)"),
    (501, 599, "排气管 (Vent Pipes)"),
    (601, 699, "取样点与计量设备用管道 (Pipes for Extraction Points & For Metering Equipment)")
]

RULES_VALVES = [
    (1, 100, "主工艺流中的止回阀与截止阀（手动与遥控操作）(Check and Stop Valves in Main Process Stream)"),
    (101, 190, "独立控制阀与遥控调节阀门 (Self Contained Control Valves and Remote Operated Modulating Valves)"),
    (191, 200, "安全阀与泄压阀 (Safety Valves and Pressure Relief Valves)"),
    (301, 399, "测量装置隔离阀 (Isolation Valves for Measuring Devices)"),
    (401, 499, "排放阀 (Drain Valves)"),
    (501, 599, "排气阀 (Vent Valves)"),
    (601, 699, "取样点与计量设备用阀门 (Valves at Extraction Points & for Metering Equipment)")
]

RULES_INSTRUMENTS = [
    (1, 99, "二进制输出信号测量仪表 (Measuring Instruments with Binary Output Signal)"),
    (101, 199, "模拟输出信号测量仪表 (Measuring Instruments with Analog Output Signal)"),
    (201, 299, "PCC机架安装模块（不含本特利内华达振动模块）(PCC Rack Mounted Modules)"),
    (301, 399, "未分配 (Not Assigned)"),
    (401, 499, "测试接口（无仪表）(Test Connections (No Instruments))"),
    (501, 599, "本地指示器 (Local Indicators)"),
    (601, 699, "未分配 (Not Assigned)"),
    (701, 899, "预留 (Reserved)"),
    (901, 999, "未分配 (Not Assigned)")
]

# ================= 2. 核心逻辑 =================

def get_description(number, rules):
    for start, end, desc in rules:
        if start <= number <= end:
            return desc
    return "未定义范围 (Undefined Range)"

def generate_flat_line(original_str):
    """
    original_str: 正则提取到的原始字符串，例如 "001"
    """
    try:
        # 1. 转换成整数用于逻辑判断
        num_for_logic = int(original_str)
    except ValueError:
        return f"* 错误：序号 '{original_str}' 不是数字"

    # 2. 获取描述
    desc_pipe = get_description(num_for_logic, RULES_PIPES)
    desc_valve = get_description(num_for_logic, RULES_VALVES)
    desc_inst = get_description(num_for_logic, RULES_INSTRUMENTS)

    # 3. 输出时使用 original_str (保留 "001")
    return (f"* 设备序号 **{original_str}** 描述为 "
            f"管道类设备 (PIPES)：{desc_pipe}；"
            f"阀门类设备 (VALVES)：{desc_valve}；"
            f"仪表类设备 (INSTRUMENTS)：{desc_inst}。")

def process_file(input_file, output_file):
    if not os.path.exists(input_file):
        print(f"错误：找不到文件 {input_file}")
        return

    # 正则匹配
    pattern = re.compile(r'^\s*\*\s*\*\*(设备序号)\*\*:\s*(\d+)')
    
    found_count = 0
    
    with open(input_file, 'r', encoding='utf-8') as f_in, \
         open(output_file, 'w', encoding='utf-8') as f_out:
        
        for line in f_in:
            match = pattern.search(line)
            if match:
                serial_str = match.group(2) # 获取原始字符串 "001"
                
                # 传入原始字符串
                new_line = generate_flat_line(serial_str)
                
                f_out.write(new_line + "\n")
                found_count += 1

    print(f"处理完成！提取了 {found_count} 条数据，结果已保存至: {output_file}")

# ================= 3. 执行 =================

if __name__ == '__main__':
    INPUT_FILE = './total_files/KKS-KKS码.md'
    OUTPUT_FILE = './total_files/KKS-设备序号.md'
    
    # 自动生成测试文件（含 001 测试用例）
    if not os.path.exists(INPUT_FILE):
        with open(INPUT_FILE, 'w', encoding='utf-8') as f:
            f.write("""
测试数据：
    * **设备序号**: 001 
    * **设备序号**: 099
    * **设备序号**: 402
            """)
        print("已生成测试文件 input.md")

    process_file(INPUT_FILE, OUTPUT_FILE)