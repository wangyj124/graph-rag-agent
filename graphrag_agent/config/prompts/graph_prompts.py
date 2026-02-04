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
1. **定义类实体**（如 ZZZ, XX）：基于字典定义的具体含义。
2. **数值/实例类实体**（如 99, 777, Tag）：基于通用规则或具体测点。

-严格的命名空间与ID构建规则-
为了构建清晰的图谱，你必须在提取步骤中对 entity_name 使用【前缀_代码】格式：

1. **字典定义类 (Schema)**:
   - **机组**: Name="Plant_{{数字}}", Type="机组代码"
   - **系统**: 遇到 3位代码 (如 "ZZZ")，必须拆分为：
     a. 主组: Name="SysGrp_{{第1位}}", Type="系统主组"
     b. 子类: Name="SysTyp_{{前2位}}", Type="系统子类"
     c. 代码: Name="Sys_{{3位}}", Type="系统代码"
   - **设备**: 遇到 2位代码 (如 "XX")，必须拆分为：
     a. 主组: Name="EqGrp_{{第1位}}", Type="设备主组"
     b. 代码: Name="EquipClass_{{2位}}", Type="设备代码"
   - **部件**: 遇到 2位代码 (如 "YY")，必须拆分为：
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
1. **所有实体描述 (All Descriptions)**: 必须严格使用文本中显式给出的定义。如果文本中没有该代码的文字描述（例如仅从KKS码中拆解出的代码），**必须**在描述属性上填写'暂无'。**严禁**使用你的外部知识进行补全。
2. **数值类**: 必须使用**通用定义**（设备序号EquipSeq除外）：
   - Area 描述: "标识组件在系统流路中的位置，通常沿介质流动方向递增。"
   - CompSeq 描述: "由两个数字构成，表示具体的部件编号。"
   - Redun 描述: "一般为单个字母，可有可无。"
3. **测点KKS码**: "Label: {{测点KKS码}}; 含义: {{KKS码描述}}"。

-步骤-
1. 识别所有实体。将每个实体格式化为 ("entity"{tuple_delimiter}<entity_name>{tuple_delimiter}<entity_type>{tuple_delimiter}<entity_description>)

2. 建立关系。识别实体配对 (source, target)：
   - **层级关系**: 对于系统、设备、部件，该类具有主子类属性的实体，建立父子连接 (如 SysGrp_Z -> 包含子类 -> SysTyp_ZZ)。
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
-以下是虚构的格式示例（严禁作为真实数据输出）-
######################
Example 1:
Entity_types: [机组代码,系统主组,系统子类,系统代码,系统区域序号,设备主组,设备代码,设备序号,冗余码,部件主组,部件代码,部件序号,测点KKS码]
Text:
代码 99 定义为 99号机组。
代码 Z 代表虚构主组。代码 ZZ 代表虚构系统子类。代码 ZZZ 代表虚构系统。
代码 X 代表虚构设备组。代码 XX 代表虚构设备类型。
代码 777 代表虚构设备序号。
代码 Y 代表虚构部件组。代码 YY 代表虚构部件类型。
KKS码: 99ZZZ88XX777YY66. 描述: 虚构KKS测点。
结构拆解: 机组: 99, 系统代码: ZZZ, 系统区域序号: 88, 设备代码: XX, 设备序号: 777，部件代码：YY，部件序号：66
KKS码: 99ZZZ88XX777QYY66 描述: 虚构KKS测点(含冗余)。
结构拆解: 机组: 99, 系统代码: ZZZ, 系统区域序号: 88, 设备代码: XX, 设备序号: 777，冗余码：Q，部件代码：YY，部件序号：66
Output:
("entity"{tuple_delimiter}"Plant_99"{tuple_delimiter}"机组代码"{tuple_delimiter}"Label: 99; 含义: 99号机组"){record_delimiter}
("entity"{tuple_delimiter}"SysGrp_Z"{tuple_delimiter}"系统主组"{tuple_delimiter}"Label: Z; 含义: 虚构主组"){record_delimiter}
("entity"{tuple_delimiter}"SysTyp_ZZ"{tuple_delimiter}"系统子类"{tuple_delimiter}"Label: ZZ; 含义: 虚构系统子类"){record_delimiter}
("entity"{tuple_delimiter}"Sys_ZZZ"{tuple_delimiter}"系统代码"{tuple_delimiter}"Label: ZZZ; 含义: 虚构系统"){record_delimiter}
("entity"{tuple_delimiter}"EqGrp_X"{tuple_delimiter}"设备主组"{tuple_delimiter}"Label: X; 含义: 虚构设备组"){record_delimiter}
("entity"{tuple_delimiter}"EquipClass_XX"{tuple_delimiter}"设备代码"{tuple_delimiter}"Label: XX; 含义: 虚构设备类型"){record_delimiter}
("entity"{tuple_delimiter}"CpGrp_Y"{tuple_delimiter}"部件主组"{tuple_delimiter}"Label: Y; 含义: 虚构部件组"){record_delimiter}
("entity"{tuple_delimiter}"CompClass_YY"{tuple_delimiter}"部件代码"{tuple_delimiter}"Label: YY; 含义: 虚构部件类型"){record_delimiter}
("relationship"{tuple_delimiter}"SysGrp_Z"{tuple_delimiter}"SysTyp_ZZ"{tuple_delimiter}"包含子类"{tuple_delimiter}"Z 是 ZZ 的父级主组"{tuple_delimiter}10){record_delimiter}
("relationship"{tuple_delimiter}"SysTyp_ZZ"{tuple_delimiter}"Sys_ZZZ"{tuple_delimiter}"包含子类"{tuple_delimiter}"ZZ 是 ZZZ 的父级子类"{tuple_delimiter}10){record_delimiter}
("relationship"{tuple_delimiter}"EqGrp_X"{tuple_delimiter}"EquipClass_XX"{tuple_delimiter}"包含子类"{tuple_delimiter}"X 是 XX 的父级设备组"{tuple_delimiter}10){record_delimiter}
("relationship"{tuple_delimiter}"CpGrp_Y"{tuple_delimiter}"CompClass_YY"{tuple_delimiter}"包含子类"{tuple_delimiter}"Y 是 YY 的父级部件组"{tuple_delimiter}10){record_delimiter}

("entity"{tuple_delimiter}"CompSeq_66"{tuple_delimiter}"部件序号"{tuple_delimiter}"Label: 66; 含义: 虚构部件序号"){record_delimiter}
("entity"{tuple_delimiter}"Area_88"{tuple_delimiter}"系统区域序号"{tuple_delimiter}"Label: 88; 含义: 虚构区域"){record_delimiter}
("entity"{tuple_delimiter}"EquipSeq_777"{tuple_delimiter}"设备序号"{tuple_delimiter}"Label: 777; 含义: 虚构设备序号"){record_delimiter}
("entity"{tuple_delimiter}"Tag_99ZZZ88XX777YY66"{tuple_delimiter}"测点KKS码"{tuple_delimiter}"Label: 99ZZZ88XX777YY66; 含义: 虚构KKS测点"){record_delimiter}
("relationship"{tuple_delimiter}"Tag_99ZZZ88XX777YY66"{tuple_delimiter}"Plant_99"{tuple_delimiter}"位于机组"{tuple_delimiter}"测点位于99号机组"{tuple_delimiter}10){record_delimiter}
("relationship"{tuple_delimiter}"Tag_99ZZZ88XX777YY66"{tuple_delimiter}"Sys_ZZZ"{tuple_delimiter}"位于系统"{tuple_delimiter}"测点位于虚构系统"{tuple_delimiter}10){record_delimiter}
("relationship"{tuple_delimiter}"Tag_99ZZZ88XX777YY66"{tuple_delimiter}"Area_88"{tuple_delimiter}"位于区域"{tuple_delimiter}"测点位于区域88"{tuple_delimiter}10){record_delimiter}
("relationship"{tuple_delimiter}"Tag_99ZZZ88XX777YY66"{tuple_delimiter}"EquipClass_XX"{tuple_delimiter}"属于设备类型"{tuple_delimiter}"测点设备类型为XX"{tuple_delimiter}10){record_delimiter}
("relationship"{tuple_delimiter}"Tag_99ZZZ88XX777YY66"{tuple_delimiter}"EquipSeq_777"{tuple_delimiter}"设备实例为"{tuple_delimiter}"测点设备序号为777"{tuple_delimiter}10){record_delimiter}
("relationship"{tuple_delimiter}"Tag_99ZZZ88XX777YY66"{tuple_delimiter}"CompClass_YY"{tuple_delimiter}"属于部件类型"{tuple_delimiter}"测点部件类型为YY"{tuple_delimiter}10){record_delimiter}
("relationship"{tuple_delimiter}"Tag_99ZZZ88XX777YY66"{tuple_delimiter}"CompSeq_66"{tuple_delimiter}"设备实例为"{tuple_delimiter}"测点部件序号为66"{tuple_delimiter}10){record_delimiter}

("entity"{tuple_delimiter}"Redun_Q"{tuple_delimiter}"冗余码"{tuple_delimiter}"Label: Q; 含义: 虚构冗余码"){record_delimiter}
("entity"{tuple_delimiter}"Tag_99ZZZ88XX777QYY66"{tuple_delimiter}"测点KKS码"{tuple_delimiter}"Label: 99ZZZ88XX777QYY66; 含义: 虚构KKS测点(含冗余)"){record_delimiter}
("relationship"{tuple_delimiter}"Tag_99ZZZ88XX777QYY66"{tuple_delimiter}"Redun_Q"{tuple_delimiter}"具有冗余"{tuple_delimiter}"测点具有冗余码Q"{tuple_delimiter}10){completion_delimiter}
#############################
"""

human_template_build_graph = """
=== 真实任务开始 (Real Task Starts) ===
######################
实体类型：{entity_types}
关系类型：{relationship_types}
文本：{input_text}
######################
重要指令：
1. 仅提取文本中明确出现的实体和关系。
2. 严禁提取或模仿上述示例中的虚构实体（如 Tag_99ZZZ..., Sys_ZZZ 等）。
3. 输出前请自检：如果结果中包含 '99ZZZ' 或 '虚构' 字样，请立刻剔除。
4. 如果文本中没有相关信息，不要编造。

输出：
"""

# ==============================================================================
# 2. 实体对齐与索引提示词 (Entity Resolution)
# ==============================================================================

system_template_build_index = """
你是一名 KKS 数据处理助理。你的任务是识别列表中的重复实体并合并它们。
请严格遵循以下原则：

1. **Tag 不合并**: 测点KKS码 (Tag_...) 必须绝对唯一，除非字符串完全一致，否则**绝不合并**。
2. **ID 严格区分**: "Sys_ZZZ" 和 "Sys_YYY" 是不同实体；ID作为实体合并的唯一判别标准，实体ID不同，不能合并。
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
['SysGrp_Z', 'SysGrp_Z', 'Sys_ZZZ']
#############
Output:
['SysGrp_Z', 'SysGrp_Z']
#############################
Example 2:
['Tag_99ZZZ88XX777', 'Tag_99ZZZ88XX778']
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
1. **系统与设备范围**: 该社区涵盖了哪些主要系统 (如 ZZZ) 和设备类型 (如 XX, YY)。
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

Which entity ID best represents the canonical form (e.g., Sys_ZZZ)? Reply with only the entity ID."""

# ==============================================================================
# 4. 描述融合提示词 (Description Fusion)
# ==============================================================================

entity_description_fusion_prompt = """
你是一位专业的知识图谱数据清洗专家。你的任务是判断两个关于同一个 KKS 编码实体的描述是否需要融合，并输出融合后的最终描述。

### 现有描述：
{old_description}

### 新提取的描述：
{new_description}

### 处理规则：
1. **判别无意义信息**：如果“新提取的描述”包含类似“暂无”、“无额外信息”、“No additional data”、“无”等表示缺失含义的内容，请忽略新描述，直接返回“现有描述”。
2. **判别语义重复**：如果“新提取的描述”表达的意思已经包含在“现有描述”中，或者两者意思高度相似，请直接返回“现有描述”。
3. **追加补充信息**：如果“新提取的描述”提供了“现有描述”中没有的新信息（例如不同的名称、功能说明、位置信息等），请将新信息追加到“现有描述”后面，使用分号“; ”分隔。
4. **简洁去重**：在追加时，确保最终结果简洁，避免词语完全重复。
5. **输出要求**：只输出融合后的描述文本，不要包含任何解释性文字或引号。

### 输出：
"""

__all__ = [
    "system_template_build_graph",
    "human_template_build_graph",
    "system_template_build_index",
    "user_template_build_index",
    "community_template",
    "COMMUNITY_SUMMARY_PROMPT",
    "entity_alignment_prompt",
    "entity_description_fusion_prompt",
]