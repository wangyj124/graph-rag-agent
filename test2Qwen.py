import os
import sys
from openai import OpenAI
from graphrag_agent.config.settings import OPENAI_LLM_CONFIG

# 确保项目根目录在 sys.path 中，以便正确导入模块
# (假设当前脚本位于项目根目录)

def run_test():
    # 1. 获取项目配置 (参考项目方式)
    print("正在加载项目配置...")
    api_key = OPENAI_LLM_CONFIG.get("api_key")
    base_url = OPENAI_LLM_CONFIG.get("base_url")
    model = OPENAI_LLM_CONFIG.get("model")

    if not api_key or not base_url or not model:
        print("错误: 请检查 .env 文件或 settings.py，确保 OPENAI_API_KEY, OPENAI_BASE_URL, OPENAI_LLM_MODEL 已正确配置")
        return

    print(f"Base URL: {base_url}")
    print(f"Model: {model}")

    # 兼容性处理: 某些 OpenAI 兼容接口可能需要 /v1 后缀
    if base_url and not base_url.rstrip("/").endswith("/v1"):
         base_url = base_url.rstrip("/") + "/v1"

    # 2. 初始化客户端 (参考项目依赖的底层库，但这里直接用 OpenAI 官方库以配合 Thinking 示例)
    client = OpenAI(
        api_key=api_key,
        base_url=base_url,
    )

    def test_scenario(name, messages, extra_body=None):
        print(f"\n\n{'#'*20} 测试场景: {name} {'#'*20}")
        print(f"Messages: {messages}")
        if extra_body:
            print(f"Extra Body: {extra_body}")
        
        try:
            # 参考用户提供的 Qwen 思考示例代码
            completion = client.chat.completions.create(
                model=model,
                messages=messages,
                extra_body=extra_body,
                stream=True,
                stream_options={"include_usage": True} # 获取 Token 使用统计
            )

            reasoning_content = ""
            answer_content = ""
            is_answering = False
            has_printed_reasoning_header = False

            print("\n" + "=" * 20 + " 响应开始 " + "=" * 20 + "\n")

            for chunk in completion:
                # 处理 usage 信息 (通常在最后)
                if not chunk.choices:
                    if hasattr(chunk, 'usage') and chunk.usage:
                         print(f"\n[Usage Info]: {chunk.usage}")
                    continue

                delta = chunk.choices[0].delta

                # --- 核心: 收集思考内容 (参考示例) ---
                # 注意: 不同模型/框架返回的字段可能不同，这里优先检查 reasoning_content
                r_content = getattr(delta, "reasoning_content", None)
                
                if r_content:
                    if not has_printed_reasoning_header:
                        print("【思考过程】:")
                        has_printed_reasoning_header = True
                    
                    print(r_content, end="", flush=True)
                    reasoning_content += r_content

                # --- 核心: 收集正式回复 ---
                if hasattr(delta, "content") and delta.content:
                    if not is_answering:
                        if reasoning_content:
                             print("\n\n") # 与思考过程分隔
                        print("【完整回复】:")
                        is_answering = True
                    print(delta.content, end="", flush=True)
                    answer_content += delta.content

            if not reasoning_content and not has_printed_reasoning_header:
                print("(未检测到思考过程输出)")

        except Exception as e:
            print(f"\n请求出错: {e}")

    # 场景 1: 开启思考 (基准测试)
    # Qwen-DeepThink 默认可能开启，或者需要 enable_thinking=True
    test_scenario(
        "1. 开启思考 (Enable Thinking)", 
        [{"role": "user", "content": "你好，请解释一下什么是量子纠缠？"}],
        extra_body={"enable_thinking": True}
    )

    # 场景 2: 尝试通过 Prompt 关闭思考 (方案A)
    test_scenario(
        "2. 关闭思考 - 方案A (/no_think Prompt)", 
        [{"role": "user", "content": "/no_think 你好，请解释一下什么是量子纠缠？"}],
        extra_body={"enable_thinking": True} # 保持参数开启，测试 Prompt 优先级
    )

    # 场景 3: 尝试通过参数关闭思考 (方案B)
    test_scenario(
        "3. 关闭思考 - 方案B (enable_thinking=False)", 
        [{"role": "user", "content": "你好，请解释一下什么是量子纠缠？"}],
        extra_body={"enable_thinking": False}
    )

if __name__ == "__main__":
    run_test()