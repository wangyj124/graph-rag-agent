"""
KKS 图谱构建与社区摘要提示模板集合 (KKS 版)。

这些模板专用于 KKS 编码体系的层级提取、实体对齐与摘要。
"""

# ==============================================================================
# 1. 图谱构建提示词 (Build Graph) 
# ==============================================================================

system_template_build_graph = """
-目标-
你是一位电力行业 KKS (电厂标识系统) 编码专家。
给定相关的 KKS 定义文本和实体类型列表，你需要提取出所有实体，并严格按照 KKS 的层级逻辑（从主组到子类再到代码）将代码拆解为多个实体，并识别它们之间的关系。

-严格的命名空间与ID构建规则-
为了构建清晰的图谱，你必须在提取步骤中对 entity_name 使用【前缀_代码】格式：
1. **系统代码 (System Level)**:
   - 遇到 3位代码 (如 "MBP")，必须拆分为三个实体：
     a. 主组: Name="SysGrp_{{第1位}}", Type="系统主组"
     b. 子类: Name="SysTyp_{{前2位}}", Type="系统子类"
     c. 代码: Name="Sys_{{3位}}", Type="系统代码"
   - 遇到 2位代码 (如 "MB")，拆分为主组和子类。
2. **设备代码 (Equipment Level)**:
   - 遇到 2位代码 (如 "AA")，必须拆分为两个实体：
     a. 主组: Name="EqGrp_{{第1位}}", Type="设备主组"
     b. 代码: Name="EquipClass_{{2位}}", Type="设备代码"
3. **部件代码 (Component Level)**:
   - 遇到 2位代码 (如 "XQ")，拆分为部件主组(CpGrp_)和部件代码(CompClass_)。
   - 遇到 1位代码 (如 "S")，直接提取为部件代码(CompClass_)。
4. **机组代码**: Name="Plant_{{数字}}", Type="机组代码"。

-步骤-
1. 识别所有实体。对于每个已识别的实体，提取以下信息：
   - entity_name：使用上述规则构建的唯一ID (如 "Sys_MBP")。
   - entity_type：必须属于列表 [{entity_types}] 之一。
   - entity_description：包含 "Label: [原始代码]" 以及文本中对该代码含义的定义。如果是由子代码推导出的父节点，描述需注明"父级分类"。
   将每个实体格式化为 ("entity"{tuple_delimiter}<entity_name>{tuple_delimiter}<entity_type>{tuple_delimiter}<entity_description>)

2. 建立层级关系与定义关系。识别实体配对 (source_entity, target_entity)：
   - **层级关系**: 必须建立父子连接。
     - SysGrp_M -> 包含子类 -> SysTyp_MB -> 包含子类 -> Sys_MBP
     - EqGrp_A -> 包含子类 -> EquipClass_AA
   - **包含关系**: 如果文本提到某系统包含某设备。
     - Sys_MBP -> 包含设备 -> EquipClass_AA
   提取信息：
   - source_entity：源实体名称
   - target_entity：目标实体名称
   - relationship_type：使用中文，如 "包含子类", "包含设备", "包含部件", "属于机组"。
   - relationship_description：解释关系 (如 "M 是 MB 的父级主组")。
   - relationship_strength：对于 KKS 定义类关系，固定评分 **10**。
   将每个关系格式化为 ("relationship"{tuple_delimiter}<source_entity>{tuple_delimiter}<target_entity>{tuple_delimiter}<relationship_type>{tuple_delimiter}<relationship_description>{tuple_delimiter}<relationship_strength>)

3. 实体和关系的所有属性用中文输出。使用 **{record_delimiter}** 作为列表分隔符。
4. 完成后，输出 {completion_delimiter}

######################
-示例-
######################
Example 1:
Entity_types: [机组代码, 系统主组, 系统子类, 系统代码, 设备主组, 设备代码]
Text:
代码 10 定义为 1号机组。
代码 M 代表主机组。代码 MB 代表燃机。代码 MBA 代表燃机主轴系统。
代码 A 代表机械设备。代码 AA 代表阀门。

Output:
("entity"{tuple_delimiter}"Plant_10"{tuple_delimiter}"机组代码"{tuple_delimiter}"Label: 10; 含义: 1号机组"){record_delimiter}
("entity"{tuple_delimiter}"SysGrp_M"{tuple_delimiter}"系统主组"{tuple_delimiter}"Label: M; 含义: 主机组"){record_delimiter}
("entity"{tuple_delimiter}"SysTyp_MB"{tuple_delimiter}"系统子类"{tuple_delimiter}"Label: MB; 含义: 燃机"){record_delimiter}
("entity"{tuple_delimiter}"Sys_MBA"{tuple_delimiter}"系统代码"{tuple_delimiter}"Label: MBA; 含义: 燃机主轴系统"){record_delimiter}
("entity"{tuple_delimiter}"EqGrp_A"{tuple_delimiter}"设备主组"{tuple_delimiter}"Label: A; 含义: 机械设备"){record_delimiter}
("entity"{tuple_delimiter}"EquipClass_AA"{tuple_delimiter}"设备代码"{tuple_delimiter}"Label: AA; 含义: 阀门"){record_delimiter}
("relationship"{tuple_delimiter}"SysGrp_M"{tuple_delimiter}"SysTyp_MB"{tuple_delimiter}"包含子类"{tuple_delimiter}"M 是 MB 的父级主组"{tuple_delimiter}10){record_delimiter}
("relationship"{tuple_delimiter}"SysTyp_MB"{tuple_delimiter}"Sys_MBA"{tuple_delimiter}"包含子类"{tuple_delimiter}"MB 是 MBA 的父级子类"{tuple_delimiter}10){record_delimiter}
("relationship"{tuple_delimiter}"EqGrp_A"{tuple_delimiter}"EquipClass_AA"{tuple_delimiter}"包含子类"{tuple_delimiter}"A 是 AA 的父级设备组"{tuple_delimiter}10){completion_delimiter}
#############################
"""

human_template_build_graph = """
-真实数据-
######################
实体类型：{entity_types}
关系类型：{relationship_types}
文本：{input_text}
######################
输出：
"""

# ==============================================================================
# 2. 实体对齐与索引提示词 (Entity Resolution)
# ==============================================================================

system_template_build_index = """
你是一名 KKS 数据处理助理。你的任务是识别列表中的重复实体并合并它们。
由于 KKS 编码非常严格，请遵循以下原则：

1. **严格的 ID 区分**: "Sys_MBA" 和 "Sys_MBB" 是完全不同的实体，绝对**不能**合并。
2. **同名合并**: 只有当 Entity Name (ID) 完全一致，或者仅仅是大小写/空格差异时才合并。
3. **描述合并**: 如果两个实体 ID 相同（例如都是 "SysGrp_M"），但描述略有不同（一个写"主机组"，一个写"Main Machine Set"），应该合并它们。

输出格式：
1. 将要合并的实体输出为 Python 列表格式。
2. 如果有多组可以合并，每组占一行。
3. 如果没有要合并的实体，输出空列表 []。
4. 只输出列表，不要包含其他文字。

######################
-示例-
######################
Example 1:
['SysGrp_M', 'SysGrp_M', 'Sys_MBA']
#############
Output:
['SysGrp_M', 'SysGrp_M']
#############################
Example 2:
['Plant_10', 'Plant_11', 'Plant_10']
#############
Output:
['Plant_10', 'Plant_10']
#############################
"""

user_template_build_index = """
以下是要处理的实体列表：
{entities}
请识别重复的实体，提供可以合并的实体列表。
输出：
"""

# ==============================================================================
# 3. 社区摘要提示词 (Community Summary)
# ==============================================================================

community_template = """
基于所提供的属于同一 KKS 图社区的节点和关系，
生成该社区所代表的工业系统功能的自然语言摘要。

请重点关注：
1. 该社区涵盖了哪些主要的系统主组（如 M类主机组，P类辅机等）。
2. 该社区包含哪些关键的设备类型（如 泵、阀门、变压器）。
3. 描述这些系统和设备之间的层级或包含关系。

社区信息：
{community_info}

摘要：
"""

COMMUNITY_SUMMARY_PROMPT = """
给定一组 KKS 实体和关系三元组，生成对该系统功能区域的摘要。不要废话。
"""

entity_alignment_prompt = """
Given these KKS entities that should refer to the same code/concept:
{entity_desc}

Which entity ID best represents the canonical form (e.g., Sys_MBP)? Reply with only the entity ID."""

__all__ = [
    "system_template_build_graph",
    "human_template_build_graph",
    "system_template_build_index",
    "user_template_build_index",
    "community_template",
    "COMMUNITY_SUMMARY_PROMPT",
    "entity_alignment_prompt",
]