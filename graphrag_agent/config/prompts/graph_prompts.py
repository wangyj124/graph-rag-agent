"""
KKS 图谱构建与社区摘要提示模板集合。
"""

# ==============================================================================
# 1. 图谱构建提示词 (Build Graph)
# ==============================================================================

system_template_build_graph = """
-目标-
你是一位电力行业 KKS (电厂标识系统) 编码专家。
给定相关的 KKS 文本，你需要提取出所有实体，并严格按照 KKS 的逻辑将代码拆解。
你需要构建两类实体：
1. **定义类实体**（如 MBA, AA）：基于字典定义的具体含义。
2. **数值/实例类实体**（如 11, 101, Tag）：基于通用规则或具体测点。

-严格的命名空间与ID构建规则-
为了构建清晰的图谱，你必须在提取步骤中对 entity_name 使用【前缀_代码】格式：

1. **字典定义类 (Schema)**:
   - **机组**: Name="Plant_{{数字}}", Type="机组代码"
   - **系统**: 遇到 3位代码 (如 "MBP")，必须拆分为：
     a. 主组: Name="SysGrp_{{第1位}}", Type="系统主组"
     b. 子类: Name="SysTyp_{{前2位}}", Type="系统子类"
     c. 代码: Name="Sys_{{3位}}", Type="系统代码"
   - **设备**: 遇到 2位代码 (如 "AA")，必须拆分为：
     a. 主组: Name="EqGrp_{{第1位}}", Type="设备主组"
     b. 代码: Name="EquipClass_{{2位}}", Type="设备代码"
   - **部件**: 遇到 2位代码 (如 "XQ")，必须拆分为：
     a. 主组: Name="CpGrp_{{第1位}}", Type="部件主组"
     b. 代码: Name="CompClass_{{2位}}", Type="部件代码"

2. **数值/实例类 (Instances)**:
   - **系统区域序号**: Name="Area_{{数字}}", Type="系统区域序号"
   - **设备序号**: Name="EquipSeq_{{数字}}", Type="设备序号"
   - **部件序号**: Name="CompSeq_{{数字}}", Type="部件序号"
   - **冗余码**: Name="Redun_{{字母}}", Type="冗余码"

3. **测点KKS码 (Full Tag)**:
   - Name="Tag_{{完整字符串}}", Type="测点KKS码"

-描述 (Description) 填写规则-
1. **字典类、数值类中的设备序号**: 使用文本中具体的含义 (如 "Label: MBA; 含义: 燃机涡轮机")，如果文本中没有它的描述，应在描述属性上填写'暂无'。
2. **数值类**: 必须使用**通用定义**（设备序号EquipSeq除外）：
   - Area 描述: "标识组件在系统流路中的位置，通常沿介质流动方向递增。"
   - CompSeq 描述: "由两个数字构成，表示具体的部件编号。"
   - Redun 描述: "一般为单个字母，可有可无。"
3. **测点KKS码**: "Label: {{测点KKS码}}; 含义: {{KKS码描述}}"。

-步骤-
1. 识别所有实体。将每个实体格式化为 ("entity"{tuple_delimiter}<entity_name>{tuple_delimiter}<entity_type>{tuple_delimiter}<entity_description>)

2. 建立关系。识别实体配对 (source, target)：
   - **层级关系**: 对于系统、设备、部件，该类具有主子类属性的实体，建立父子连接 (如 SysGrp_M -> 包含子类 -> SysTyp_MB)。
   - **测点全关联 (核心)**: 对于每一个测点KKS码 (Tag)，必须将其拆解并与**所有**组成部分建立关系：
     - ("Tag_...", "位于机组", "Plant_...")
     - ("Tag_...", "位于系统", "Sys_...")
     - ("Tag_...", "位于区域", "Area_...")
     - ("Tag_...", "属于设备类型", "EquipClass_...")
     - ("Tag_...", "设备实例为", "EquipSeq_...")
     - (若有) ("Tag_...", "属于部件类型", "CompClass_...")
     - (若有) ("Tag_...", "部件实例为", "CompSeq_...")
     - (若有) ("Tag_...", "具有冗余", "Redun_...")
   
   将每个关系格式化为 ("relationship"{tuple_delimiter}<source>{tuple_delimiter}<target>{tuple_delimiter}<type>{tuple_delimiter}<desc>{tuple_delimiter}<strength>)
   (注意：KKS 定义关系的 strength 固定为 10)

3. 实体和关系的所有属性用中文输出。使用 **{record_delimiter}** 作为列表分隔符。
4. 完成后，输出 {completion_delimiter}

######################
-示例-
######################
Example 1:
Entity_types: [机组代码,系统主组,系统子类,系统代码,系统区域序号,设备主组,设备代码,设备序号,冗余码,部件主组,部件代码,部件序号,测点KKS码]
Text:
代码 10 定义为 1号机组。
代码 M 代表主机组。代码 MB 代表燃机。代码 MBA 代表燃机主轴系统。
代码 A 代表机械设备。代码 AA 代表阀门。
代码 101 代表管道类设备 (PIPES)：主管道 (Main Pipes)；阀门类设备 (VALVES)：独立控制阀与遥控调节阀门 (Self Contained Control Valves and Remote Operated Modulating Valves)；仪表类设备 (INSTRUMENTS)：模拟输出信号测量仪表 (Measuring Instruments with Analog Output Signal)。
代码 K 代表机械部件。代码 KC 代表换热器、冷却器。
KKS码: 10MBA11AA101KC02. 描述: 1号机组燃机阀门(含部件)。
结构拆解: 机组: 10, 系统代码: MBA, 系统区域序号: 11, 设备代码: AA, 设备序号: 101，部件代码：KC，部件序号：02
KKS码: 10MBA11AA101XKC02 描述: 1号机组燃机阀门(含冗余)。
结构拆解: 机组: 10, 系统代码: MBA, 系统区域序号: 11, 设备代码: AA, 设备序号: 101，冗余码：X，部件代码：KC，部件序号：02

Output:
("entity"{tuple_delimiter}"Plant_10"{tuple_delimiter}"机组代码"{tuple_delimiter}"Label: 10; 含义: 1号机组"){record_delimiter}
("entity"{tuple_delimiter}"SysGrp_M"{tuple_delimiter}"系统主组"{tuple_delimiter}"Label: M; 含义: 主机组"){record_delimiter}
("entity"{tuple_delimiter}"SysTyp_MB"{tuple_delimiter}"系统子类"{tuple_delimiter}"Label: MB; 含义: 燃机"){record_delimiter}
("entity"{tuple_delimiter}"Sys_MBA"{tuple_delimiter}"系统代码"{tuple_delimiter}"Label: MBA; 含义: 燃机主轴系统"){record_delimiter}
("entity"{tuple_delimiter}"EqGrp_A"{tuple_delimiter}"设备主组"{tuple_delimiter}"Label: A; 含义: 机械设备"){record_delimiter}
("entity"{tuple_delimiter}"EquipClass_AA"{tuple_delimiter}"设备代码"{tuple_delimiter}"Label: AA; 含义: 阀门"){record_delimiter}
("entity"{tuple_delimiter}"CpGrp_K"{tuple_delimiter}"部件主组"{tuple_delimiter}"Label: K; 含义: 机械部件"){record_delimiter}
("entity"{tuple_delimiter}"CompClass_KC"{tuple_delimiter}"部件代码"{tuple_delimiter}"Label: KC; 含义: 换热器，冷却器"){record_delimiter}
("relationship"{tuple_delimiter}"SysGrp_M"{tuple_delimiter}"SysTyp_MB"{tuple_delimiter}"包含子类"{tuple_delimiter}"M 是 MB 的父级主组"{tuple_delimiter}10){record_delimiter}
("relationship"{tuple_delimiter}"SysTyp_MB"{tuple_delimiter}"Sys_MBA"{tuple_delimiter}"包含子类"{tuple_delimiter}"MB 是 MBA 的父级子类"{tuple_delimiter}10){record_delimiter}
("relationship"{tuple_delimiter}"EqGrp_A"{tuple_delimiter}"EquipClass_AA"{tuple_delimiter}"包含子类"{tuple_delimiter}"A 是 AA 的父级设备组"{tuple_delimiter}10){record_delimiter}
("relationship"{tuple_delimiter}"CpGrp_K"{tuple_delimiter}"CompClass_KC"{tuple_delimiter}"包含子类"{tuple_delimiter}"K 是 KC 的父级部件组"{tuple_delimiter}10){record_delimiter}

("entity"{tuple_delimiter}"Area_11"{tuple_delimiter}"系统区域序号"{tuple_delimiter}"Label: 11; 含义: 标识组件在系统流路中的位置"){record_delimiter}
("entity"{tuple_delimiter}"EquipSeq_101"{tuple_delimiter}"设备序号"{tuple_delimiter}"Label: 101; 含义: 管道类设备 (PIPES)：主管道 (Main Pipes)；阀门类设备 (VALVES)：独立控制阀与遥控调节阀门 (Self Contained Control Valves and Remote Operated Modulating Valves)；仪表类设备 (INSTRUMENTS)：模拟输出信号测量仪表 (Measuring Instruments with Analog Output Signal)"){record_delimiter}
("entity"{tuple_delimiter}"Tag_10MBA11AA101KC02"{tuple_delimiter}"测点KKS码"{tuple_delimiter}"Label: 10MBA11AA101KC02; 含义: 1号机组燃机阀门(含部件)"){record_delimiter}
("relationship"{tuple_delimiter}"Tag_10MBA11AA101KC02"{tuple_delimiter}"Plant_10"{tuple_delimiter}"位于机组"{tuple_delimiter}"测点位于1号机组"{tuple_delimiter}10){record_delimiter}
("relationship"{tuple_delimiter}"Tag_10MBA11AA101KC02"{tuple_delimiter}"Sys_MBA"{tuple_delimiter}"位于系统"{tuple_delimiter}"测点位于燃机主轴系统"{tuple_delimiter}10){record_delimiter}
("relationship"{tuple_delimiter}"Tag_10MBA11AA101KC02"{tuple_delimiter}"Area_11"{tuple_delimiter}"位于区域"{tuple_delimiter}"测点位于区域11"{tuple_delimiter}10){record_delimiter}
("relationship"{tuple_delimiter}"Tag_10MBA11AA101KC02"{tuple_delimiter}"EquipClass_AA"{tuple_delimiter}"属于设备类型"{tuple_delimiter}"测点设备类型为阀门"{tuple_delimiter}10){record_delimiter}
("relationship"{tuple_delimiter}"Tag_10MBA11AA101KC02"{tuple_delimiter}"EquipSeq_101"{tuple_delimiter}"设备实例为"{tuple_delimiter}"测点设备序号为101"{tuple_delimiter}10){record_delimiter}
("relationship"{tuple_delimiter}"Tag_10MBA11AA101KC02"{tuple_delimiter}"CompClass_KC"{tuple_delimiter}"属于部件类型"{tuple_delimiter}"测点部件类型为换热器，冷却器"{tuple_delimiter}10){record_delimiter}
("relationship"{tuple_delimiter}"Tag_10MBA11AA101KC02"{tuple_delimiter}"CompSeq_02"{tuple_delimiter}"设备实例为"{tuple_delimiter}"测点部件序号为02"{tuple_delimiter}10){record_delimiter}

("entity"{tuple_delimiter}"Redun_X"{tuple_delimiter}"冗余码"{tuple_delimiter}"Label: X; 含义: 标识设备的冗余或备用状态"){record_delimiter}
("entity"{tuple_delimiter}"Tag_10MBA11AA101XKC02"{tuple_delimiter}"测点KKS码"{tuple_delimiter}"Label: 10MBA11AA101XKC02; 含义: 1号机组燃机阀门(含冗余)"){record_delimiter}
("relationship"{tuple_delimiter}"Tag_10MBA11AA101XKC02"{tuple_delimiter}"Redun_X"{tuple_delimiter}"具有冗余"{tuple_delimiter}"测点具有冗余码X"{tuple_delimiter}10){completion_delimiter}
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
请严格遵循以下原则：

1. **Tag 不合并**: 测点KKS码 (Tag_...) 必须绝对唯一，除非字符串完全一致，否则**绝不合并**。
2. **ID 严格区分**: "Sys_MBA" 和 "Sys_MBB" 是不同实体；ID作为实体合并的唯一判别标准，实体ID不同，不能合并。
3. **数值实体合并**: 对于 Area_XX, EquipSeq_XXX 等数值实体，如果 ID 相同 (如都是 "Area_11")，可以合并，因为它们共享相同的通用定义。
4. **描述合并**: 如果两个实体 ID 相同，但描述略有差异 (如 "Label: FT; 含义: 温度" vs "Label: FT; 含义: Temperature Measurement")，应该合并。

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
['Tag_10MBA11FT101', 'Tag_10MBA11FT102']
#############
Output:
[]
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
1. **系统与设备范围**: 该社区涵盖了哪些主要系统 (如 MBA) 和设备类型 (如 AA, FT)。
2. **测点分布**: 该社区包含哪些具体的测点KKS码 (Tag)，它们主要测量什么参数（如温度、压力）。
3. **结构特征**: 描述这些测点如何分布在不同的区域 (Area) 或序号 (Serial) 中。

社区信息：
{community_info}

摘要：
"""

COMMUNITY_SUMMARY_PROMPT = """
给定一组 KKS 实体和关系三元组，生成对该系统功能区域及测点分布的摘要。不要废话。
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